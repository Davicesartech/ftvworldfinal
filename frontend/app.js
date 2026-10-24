/* Futvôlei SPA — app.js (JS puro). Tudo dentro de uma IIFE: sem variáveis globais. */
(() => {
'use strict';
/* Armazenamento seguro: usa o do navegador e cai para memória se estiver indisponível */
const mk=n=>{try{const s=window[n];s.setItem('_t','1');s.removeItem('_t');return s}catch(e){const m={};return{getItem:k=>k in m?m[k]:null,setItem:(k,v)=>{m[k]=String(v)},removeItem:k=>{delete m[k]}}}};
const LS=mk('localStorage'),SS=mk('sessionStorage');


/* ===== Config e utilitários ===== */
// Endereço da API Flask. Em produção troque por 'https://seu-servidor.com/api'.
const API_CONFIG = { baseUrl: 'http://127.0.0.1:5000/api' };
const NIVEIS = ['iniciante', 'intermediário', 'avançado'];
const SEXOS = [['feminino', 'Feminino'], ['masculino', 'Masculino']];
const GENEROS = [['masculino', 'Masculino'], ['feminino', 'Feminino'], ['misto', 'Misto']];   // tipo do campeonato: masculino só homens, feminino só mulheres, misto aceita os dois
const bGen = c => UI.badge((Object.fromEntries(GENEROS)[c.genero || 'misto'] || 'Misto'), 'gn ' + esc(c.genero || 'misto'));
const PLACAR_MAX = 18;   // a partida vai até 18 pontos: quem chega a 18 vence
const primeiroNome = n => String(n || '').trim().split(/\s+/)[0] || '';
const nomeDupla = (u1, u2) => u1 && u2 ? `${primeiroNome(u1.nome)} & ${primeiroNome(u2.nome)}` : '';   // nome da dupla = 1º nome do jogador 1 + 1º nome do jogador 2
const bSexo = u => u && u.sexo ? UI.badge((u.sexo === 'feminino' ? '♀ ' : '♂ ') + (u.sexo === 'feminino' ? 'Feminino' : 'Masculino'), 'sx ' + esc(u.sexo)) : '';   // selo de sexo no perfil
const $ = (s, r = document) => r.querySelector(s);
// Escapa HTML para evitar XSS ao renderizar dados do usuário
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = d => d ? new Date(d + (d.length === 10 ? 'T12:00' : '')).toLocaleDateString('pt-BR') : '—';
const hoje = () => new Date().toISOString().slice(0, 10);
const nm = (a, id) => esc(a.find(x => x.id === id)?.nome ?? '—');
const compat = (c, d, us) => c.nivel === 'livre' || [d.j1, d.j2].every(id => us.find(u => u.id === id)?.nivel === c.nivel);
// SHA-256 no navegador (só demo). Em produção o hash (bcrypt/argon2 + salt) deve ser feito no backend.
const hash = async s => { try { if (crypto.subtle) return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join(''); } catch { } return sha256(s); };
function sha256(s) {   // reserva para contextos sem crypto.subtle: mesmo resultado
  const b = new TextEncoder().encode(s), l = b.length, n = (((l + 8) >> 6) + 1) << 4, w = new Uint32Array(n), K = [], H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
  for (let i = 0; i < l; i++) w[i >> 2] |= b[i] << (24 - (i % 4) * 8);
  w[l >> 2] |= 0x80 << (24 - (l % 4) * 8); w[n - 1] = l * 8;
  for (let c = 2, k = 0; k < 64; c++) { let p = true; for (let d = 2; d * d <= c; d++) if (c % d === 0) { p = false; break; } if (p) K[k++] = (Math.cbrt(c) % 1) * 4294967296 | 0; }
  const R = (x, y) => (x >>> y) | (x << (32 - y));
  for (let o = 0; o < n; o += 16) {
    const W = Array.from(w.subarray(o, o + 16));
    for (let i = 16; i < 64; i++) W[i] = (W[i - 16] + (R(W[i - 15], 7) ^ R(W[i - 15], 18) ^ (W[i - 15] >>> 3)) + W[i - 7] + (R(W[i - 2], 17) ^ R(W[i - 2], 19) ^ (W[i - 2] >>> 10))) | 0;
    let [a, b2, c, d, e, f, g, h] = H;
    for (let i = 0; i < 64; i++) { const t1 = (h + (R(e, 6) ^ R(e, 11) ^ R(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + W[i]) | 0, t2 = ((R(a, 2) ^ R(a, 13) ^ R(a, 22)) + ((a & b2) ^ (a & c) ^ (b2 & c))) | 0; h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b2; b2 = a; a = (t1 + t2) | 0; }
    [a, b2, c, d, e, f, g, h].forEach((v, i) => H[i] = (H[i] + v) | 0);
  }
  return H.map(v => (v >>> 0).toString(16).padStart(8, '0')).join('');
}

/* ===== Camada de dados: fetch() para o backend Flask + tradução de nomes de campo ===== */
// O backend usa nomes do banco (id_usuario1, vagas_total...). O front usa nomes curtos (j1, limite...).
// MAPA liga os dois; os ids viram texto no front (os data-id do HTML são texto) e número ao voltar pro servidor.
const BASE_URL = (API_CONFIG.baseUrl || 'http://127.0.0.1:5000/api').replace(/\/$/, '');
const IDS = new Set(['id', 'dono', 'j1', 'j2', 'camp', 'dupla', 'quadra', 'a', 'b', 'venc', 'de', 'para', 'user']);
const MAPA = {
  usuarios:     { rota: '/usuarios',     campos: { nasc: 'data_nascimento', videoUrl: 'video_url', criado: 'data_criacao', aceite: 'data_aceite_termos', hab: 'habilidades' } },
  campeonatos:  { rota: '/campeonatos',  campos: { desc: 'descricao', inicio: 'data', hora: 'horario', limite: 'vagas_total', local: 'cidade', dono: 'id_dono', vd: 'vagas_disponiveis' } },
  quadras:      { rota: '/quadras',      campos: { local: 'endereco', desc: 'descricao', dono: 'id_responsavel' } },
  duplas:       { rota: '/duplas',       campos: { j1: 'id_usuario1', j2: 'id_usuario2' } },
  inscricoes:   { rota: '/inscricoes',   campos: { camp: 'id_campeonato', dupla: 'id_dupla', data: 'data_inscricao' } },
  partidas:     { rota: '/partidas',     campos: { camp: 'id_campeonato', quadra: 'id_quadra', a: 'id_dupla1', b: 'id_dupla2', sa: 'placar_dupla1', sb: 'placar_dupla2', data: 'data_hora', venc: 'id_dupla_vencedora' } },
  solicitacoes: { rota: '/solicitacoes', campos: { de: 'id_de', para: 'id_para', data: 'data_solicitacao' } },
  candidatos:   { rota: '/candidatos',   campos: { user: 'id_usuario', msg: 'mensagem', data: 'data_criacao' } },
  logs:         { rota: '/logs',         campos: { data: 'data_hora' } },
};
const inverso = t => Object.fromEntries(Object.entries(MAPA[t].campos).map(([f, b]) => [b, f]));
function doApi(t, r) {   // registro do backend -> formato do front
  if (t === 'config') return { id: r.chave, ...(r.valor && typeof r.valor === 'object' ? r.valor : { valor: r.valor }) };
  const inv = inverso(t), o = {};
  for (const [k, v] of Object.entries(r)) { const f = inv[k] || k; o[f] = IDS.has(f) && v != null ? String(v) : v; }
  if (t === 'usuarios') o.hab = Array.isArray(r.habilidades) ? r.habilidades.join(',') : (r.habilidades || '');
  if (t === 'inscricoes') o.ativa = r.status === 'ativa';
  if (t === 'campeonatos' && o.hora) o.hora = String(o.hora).slice(0, 5);
  if (t === 'campeonatos' && o.vd != null) o.vd = +o.vd;
  if (t === 'partidas' && o.data) o.data = String(o.data).slice(0, 10);
  return o;
}
function paraApi(t, o) {   // objeto do front -> corpo para o backend
  const m = MAPA[t].campos, r = {};
  for (const [f, v] of Object.entries(o)) {
    if (v === undefined || f === 'vd') continue;
    r[m[f] || f] = IDS.has(f) && v !== '' && v != null && !isNaN(v) ? Number(v) : v;
  }
  if (t === 'inscricoes' && 'ativa' in o) { r.status = o.ativa ? 'ativa' : 'cancelada'; delete r.ativa; }
  return r;
}
const Token = { get: () => SS.getItem('fv2_token'), set: t => SS.setItem('fv2_token', t), clear: () => SS.removeItem('fv2_token') };
async function http(metodo, rota, corpo) {
  let resp;
  try {
    resp = await fetch(BASE_URL + rota, {
      method: metodo,
      headers: { ...(corpo !== undefined && { 'Content-Type': 'application/json' }), ...(Token.get() && { Authorization: 'Bearer ' + Token.get() }) },
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined
    });
  } catch { throw Error('Não foi possível falar com o servidor. Confira se o backend está rodando em ' + BASE_URL + '.'); }
  const dados = await resp.json().catch(() => null);
  if (!resp.ok) {
    if (resp.status === 401 && Token.get() && rota !== '/login') { Token.clear(); SS.removeItem('fv2_sess'); setTimeout(() => location.reload(), 1200); }
    throw Object.assign(Error(dados?.erro || `Erro ${resp.status} no servidor.`), { status: resp.status });
  }
  return dados;
}
// cache só para as leituras síncronas que o front faz (menu, contador de solicitações...)
const Cache = {};
const Storage = { get: k => Cache[k] || [], set: () => { } };
const Api = {
  async list(t) {                                                     // GET /t
    let r;
    try { r = t === 'config' ? await http('GET', '/config') : await http('GET', MAPA[t].rota); }
    catch (e) {
      if (e.status === 401 && !Token.get()) return Cache[t] = [];   // visitante sem login: rotas protegidas voltam vazias em vez de quebrar a página
      throw e;
    }
    if (!Array.isArray(r)) r = r && typeof r === 'object' ? Object.entries(r).map(([chave, valor]) => ({ chave, valor })) : [];   // aceita também {chave: valor}
    const out = r.map(x => doApi(t, x));
    if (t === 'duplas') {   // o nome da dupla é sempre o primeiro nome de cada jogador (vale também para duplas antigas com nome personalizado)
      const us = Cache.usuarios?.length ? Cache.usuarios : await Api.list('usuarios').catch(() => []);
      out.forEach(d => { d.nome = nomeDupla(us.find(u => u.id === d.j1), us.find(u => u.id === d.j2)) || d.nome; });
    }
    return Cache[t] = out;
  },
  async get(t, id) {                                                  // GET /t/:id
    if (t === 'config') return (await Api.list('config')).find(x => x.id === id);
    try { return doApi(t, await http('GET', `${MAPA[t].rota}/${id}`)); } catch (e) { if (/não encontrad/i.test(e.message)) return undefined; throw e; }
  },
  async save(t, o) {                                                  // POST /t  ou  PUT /t/:id
    if (t === 'config') {   // config guarda um JSON por chave: mescla com o que já existe
      const { id, ...resto } = o, atual = (await Api.get('config', id)) || {}, { id: _, ...valor } = { ...atual, ...resto };
      await http('PUT', `/config/${id}`, { valor }); return { id, ...valor };
    }
    const corpo = paraApi(t, o), r = o.id ? await http('PUT', `${MAPA[t].rota}/${o.id}`, corpo) : await http('POST', MAPA[t].rota, corpo);
    return doApi(t, r);
  },
  async remove(t, id) { await http('DELETE', t === 'config' ? `/config/${id}` : `${MAPA[t].rota}/${id}`); }   // DELETE /t/:id
};

/* ===== Validações ===== */
const Validators = {
  email: e => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e),
  senha: s => (s || '').length >= 6,
  tel: t => { const d = String(t || '').replace(/\D/g, ''); return /^[1-9]{2}\d{8}$/.test(d) || /^[1-9]{2}9\d{8}$/.test(d); },   // DDD + 8 dígitos (fixo) ou 9 dígitos (celular)
  cpf: c => { const d = String(c || '').replace(/\D/g, ''); if (!/^\d{11}$/.test(d) || /^(\d)\1{10}$/.test(d)) return false; const dv = n => { let t = 0; for (let i = 0; i < n; i++) t += +d[i] * (n + 1 - i); return (t * 10 % 11) % 10; }; return dv(9) === +d[9] && dv(10) === +d[10]; },
  cep: c => /^\d{8}$/.test(String(c || '').replace(/\D/g, ''))
};

/* ===== Máscaras de campos (telefone, e-mail, dinheiro, CPF, CEP) =====
   Os campos recebem data-mask="tel|email|money|cpf|cep". O UI.field coloca o atributo sozinho
   (por tipo/nome do campo) e a formatação acontece enquanto a pessoa digita. */
const Masks = {
  digits: s => String(s ?? '').replace(/\D/g, ''),
  tel(v) {   // (31) 99999-9999 ou (31) 3333-4444
    let d = Masks.digits(v); if (d.length > 11 && d.startsWith('55')) d = d.slice(2);   // cola +55...
    d = d.slice(0, 11); if (!d) return '';
    if (d.length <= 2) return '(' + d;
    if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
    if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
    return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
  },
  email(v) {   // minúsculas, sem espaços/acentos e um único @
    const s = String(v ?? '').toLowerCase().replace(/[^a-z0-9@.!#$%&'*+/=?^_`{|}~-]/g, ''), i = s.indexOf('@');
    return i < 0 ? s : s.slice(0, i + 1) + s.slice(i + 1).replace(/@/g, '');
  },
  money(v) {   // 1.234,56 — os dígitos entram da direita para a esquerda (centavos primeiro)
    const d = Masks.digits(v).replace(/^0+/, '').slice(0, 10);   // até 99.999.999,99 (Numeric 10,2 do banco)
    if (!d) return '';
    const c = d.padStart(3, '0');
    return c.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + c.slice(-2);
  },
  moneyIn: n => (n === '' || n == null || isNaN(+n)) ? '' : Masks.money(String(Math.round(+n * 100))),   // número do banco -> texto do campo
  moneyOut: v => { const d = Masks.digits(v); return d ? (+d / 100).toFixed(2) : ''; },                   // texto do campo -> número para a API
  cpf(v) { const d = Masks.digits(v).slice(0, 11); return d.replace(/^(\d{3})(\d)/, '$1.$2').replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3').replace(/\.(\d{3})(\d)/, '.$1-$2'); },
  cep(v) { return Masks.digits(v).slice(0, 8).replace(/^(\d{5})(\d)/, '$1-$2'); },
  attrs: {
    tel: 'inputmode="tel" autocomplete="tel" maxlength="15" placeholder="(00) 00000-0000"',
    email: 'inputmode="email" autocapitalize="off" spellcheck="false" placeholder="nome@email.com"',
    money: 'inputmode="decimal" maxlength="13" placeholder="0,00"',
    cpf: 'inputmode="numeric" maxlength="14" placeholder="000.000.000-00"',
    cep: 'inputmode="numeric" maxlength="9" placeholder="00000-000"'
  },
  de(f) {   // qual máscara um campo do UI.field usa (f.m força uma; f.m === '' desliga)
    if (f.m != null) return f.m;
    if (f.t === 'tel' || f.n === 'telefone') return 'tel';
    if (f.t === 'email' || f.n === 'email') return 'email';
    if (['valor', 'preco', 'premio', 'qpreco'].includes(f.n)) return 'money';
    return '';
  },
  apply(el) {   // formata mantendo o cursor no lugar
    const k = el.dataset.mask, fn = Masks[k]; if (typeof fn !== 'function') return;
    const sig = k === 'email' ? /./ : /\d/, antes = el.value, ini = el.selectionStart;
    const n = ini == null ? null : [...antes.slice(0, ini)].filter(c => sig.test(c)).length;
    const novo = fn(antes); if (novo === antes) return;
    el.value = novo; if (n == null) return;
    let i = 0, c = 0; while (i < novo.length && c < n) { if (sig.test(novo[i])) c++; i++; }
    try { el.setSelectionRange(i, i); } catch { /* type=email não aceita cursor */ }
  }
};
document.addEventListener('input', e => { if (e.target.dataset?.mask) Masks.apply(e.target); });
document.addEventListener('formdata', e => {   // dinheiro vai para a API como número (1234.56), não como texto mascarado
  e.target.querySelectorAll?.('[data-mask=money]').forEach(el => e.formData.set(el.name, Masks.moneyOut(el.value)));
});

/* ===== Sessão (sessionStorage) ===== */
const Auth = {
  cur: () => JSON.parse(SS.getItem('fv2_sess') || 'null'),
  async login(email, senha) {
    const u = await http('POST', '/login', { email: (email || '').trim().toLowerCase(), senha });   // devolve o usuário + token JWT
    Token.set(u.token);
    SS.setItem('fv2_sess', JSON.stringify({ id: String(u.id), nome: u.nome }));
    await Promise.all([Api.list('usuarios'), Api.list('solicitacoes')]);   // aquece o cache
  },
  logout() { http('POST', '/logout', {}).catch(() => { }); Token.clear(); SS.removeItem('fv2_sess'); for (const k in Cache) delete Cache[k]; }
};
/* ===== Regras de negócio (Svc) ===== */
const Svc = {
  duplaDe: async uid => (await Api.list('duplas')).find(d => d.ativa && (d.j1 === uid || d.j2 === uid)),
  async salvarUsuario(f, id) {
    if (id && id !== Auth.cur()?.id) throw Error('Você só pode editar o seu próprio perfil.');   // consumidor edita só o próprio perfil
    if (!Validators.email(f.email)) throw Error('Informe um e-mail válido.');
    if (!Validators.tel(f.telefone)) throw Error('Informe um telefone válido, com DDD. Ex.: (31) 99999-9999.');
    if ((!id || f.senha) && !Validators.senha(f.senha)) throw Error('A senha deve ter no mínimo 6 caracteres.');
    const o = { nome: f.nome.trim(), telefone: f.telefone, nasc: f.nasc, nivel: f.nivel };
    for (const k of ['foto', 'sexo', 'perna', 'local', 'valor']) if (f[k]) o[k] = f[k];
    for (const k of ['hab', 'bio', 'video', 'videoUrl']) if (k in f) o[k] = (f[k] || '').trim();   // permite apagar (vazio)
    if (o.bio && o.bio.length > 500) throw Error('A descrição pode ter no máximo 500 caracteres.');
    if (o.videoUrl && !/^https?:\/\/\S+$/i.test(o.videoUrl)) throw Error('O link do vídeo precisa começar com http:// ou https://');
    if (!o.nasc) delete o.nasc;
    if (!id) {   // cadastro: POST /usuarios (o servidor guarda hash da senha e a data do aceite dos termos)
      return doApi('usuarios', await http('POST', '/usuarios', { ...paraApi('usuarios', o), email: f.email.trim().toLowerCase(), senha: f.senha, tipo: f.tipo || 'jogador', aceitou_termos: true }));
    }
    const r = doApi('usuarios', await http('PUT', '/meu-perfil', paraApi('usuarios', o)));   // e-mail e tipo não mudam por aqui
    if (f.senha) {
      if (!f.senha_atual) throw Error('Para trocar a senha, informe também a senha atual.');
      await http('PUT', '/meu-perfil/senha', { senha_atual: f.senha_atual, senha_nova: f.senha });
    }
    SS.setItem('fv2_sess', JSON.stringify({ id, nome: r.nome }));   // atualiza o nome no cabeçalho
    return r;
  },
  async criarDupla({ nome, j1, j2 }) { return Api.save('duplas', { nome, j1, j2 }); },   // o servidor valida e cancela as solicitações pendentes
  async desfazerDupla(id) { await http('POST', `/duplas/${id}/desfazer`, {}); },       // cancela as inscrições ativas e desativa a dupla
  async inscrever({ dupla, camp }) { return Api.save('inscricoes', { camp, dupla }); },  // vagas, nível e duplicidade são validados no servidor
  async criarPartida({ camp, quadra, a, b, sa, sb, data }) {
    sa = Number(sa); sb = Number(sb);
    if (a === b) throw Error('Escolha duas duplas diferentes.');
    if (![sa, sb].every(n => Number.isInteger(n) && n >= 0 && n <= PLACAR_MAX) || Math.max(sa, sb) !== PLACAR_MAX || sa === sb)
      throw Error(`O placar vai até ${PLACAR_MAX}: uma dupla precisa terminar com ${PLACAR_MAX} pontos e a outra com no máximo ${PLACAR_MAX - 1}.`);
    const p = { camp, a, b, sa, sb };   // vencedora (quem fez 18) é calculada no servidor
    if (quadra) p.quadra = quadra;
    if (data) p.data = data + 'T12:00:00';
    return Api.save('partidas', p);
  }
};

/* ===== "Procedures" (cada uma com a SQL equivalente) ===== */
async function sp_campeonatosDisponiveis(cat = '') {
  // SELECT c.*, c.limite - COUNT(i.id) AS vagas FROM campeonatos c LEFT JOIN inscricoes i ON i.campeonato_id = c.id AND i.ativa
  //  WHERE c.status = 'aberto' AND (:cat = '' OR c.nivel = :cat) GROUP BY c.id HAVING vagas > 0;
  const [cs, is] = await Promise.all([Api.list('campeonatos'), Api.list('inscricoes')]);
  return cs.filter(c => c.status === 'aberto' && (!cat || c.nivel === cat))
    .map(c => ({ ...c, vagas: c.vd ?? c.limite - is.filter(i => i.camp === c.id && i.ativa).length })).filter(c => c.vagas > 0);
}
async function sp_campeonatos(cat = '') {
  // Lista TODOS os campeonatos (abertos, lotados e encerrados) com as vagas livres de cada um
  const [cs, is] = await Promise.all([Api.list('campeonatos'), Api.list('inscricoes')]);
  return cs.filter(c => !cat || c.nivel === cat)
    .map(c => ({ ...c, vagas: Math.max(0, c.vd ?? c.limite - is.filter(i => i.camp === c.id && i.ativa).length) }))
    .sort((a, b) => (a.status === 'aberto' ? 0 : 1) - (b.status === 'aberto' ? 0 : 1) || (a.inicio || '').localeCompare(b.inicio || ''));
}
async function sp_classificacaoCamp(camp) {
  // Classificação só deste campeonato: acumulação de vitórias (inclui duplas inscritas sem jogos)
  // SELECT d.nome, COUNT(p.id_dupla_vencedora = d.id) vitorias FROM duplas d ... GROUP BY d.id ORDER BY vitorias DESC, d.nome;
  const [is, ds, ps] = await Promise.all([Api.list('inscricoes'), Api.list('duplas'), Api.list('partidas')]);
  const pc = ps.filter(p => p.camp === camp);
  const ids = new Set([...is.filter(i => i.camp === camp && i.ativa).map(i => i.dupla), ...pc.flatMap(p => [p.a, p.b])]);
  return [...ids].map(id => ({ nome: ds.find(d => d.id === id)?.nome ?? '—', v: pc.filter(p => p.venc === id).length }))
    .sort((x, y) => y.v - x.v || x.nome.localeCompare(y.nome));
}
async function sp_rankingDuplas() {
  // SELECT d.nome, COUNT(*) jogos, SUM(p.vencedora_id = d.id) vitorias, ROUND(100 * SUM(p.vencedora_id = d.id) / COUNT(*)) aproveitamento
  //  FROM duplas d JOIN partidas p ON d.id IN (p.dupla_a, p.dupla_b) GROUP BY d.id ORDER BY vitorias DESC, aproveitamento DESC;
  const [ds, ps] = await Promise.all([Api.list('duplas'), Api.list('partidas')]);
  return ds.map(d => { const j = ps.filter(p => p.a === d.id || p.b === d.id), v = j.filter(p => p.venc === d.id).length;
    return { nome: d.nome, jogos: j.length, v, ap: j.length ? Math.round(100 * v / j.length) : 0 }; })
    .filter(r => r.jogos).sort((x, y) => y.v - x.v || y.ap - x.ap);
}
async function sp_historicoPartidasUsuario(idUser) {
  // SELECT p.data, adversaria.nome, CONCAT(sets_meus,' x ',sets_deles) placar, IF(p.vencedora_id = minha.id,'V','D') resultado
  //  FROM partidas p JOIN duplas minha ON minha.id IN (p.dupla_a, p.dupla_b) AND :idUser IN (minha.jogador1_id, minha.jogador2_id)
  //  JOIN duplas adversaria ON adversaria.id IN (p.dupla_a, p.dupla_b) AND adversaria.id <> minha.id ORDER BY p.data DESC;
  const [ps, ds] = await Promise.all([Api.list('partidas'), Api.list('duplas')]);
  const meu = p => [p.a, p.b].find(id => { const d = ds.find(x => x.id === id); return d && (d.j1 === idUser || d.j2 === idUser); });
  return ps.filter(meu).map(p => { const m = meu(p), a = m === p.a;
    return { data: p.data, adv: ds.find(x => x.id === (a ? p.b : p.a))?.nome, placar: a ? `${p.sa} x ${p.sb}` : `${p.sb} x ${p.sa}`, res: p.venc === m ? 'V' : 'D' }; })
    .sort((x, y) => y.data.localeCompare(x.data));
}

/* ===== Interface: toast, modal, confirmação, formulário genérico, tabela ===== */
const UI = {
  toast(m, t = 'ok') {
    const e = document.createElement('div'); e.className = 'toast ' + t; e.textContent = m;
    $('#toasts').append(e); setTimeout(() => e.remove(), 4000);
  },
  modal(html) {   // <dialog> nativo: foco preso, Esc fecha, modais podem empilhar
    const d = document.createElement('dialog'); d.className = 'modal'; d.innerHTML = html;
    d.addEventListener('close', () => d.remove()); document.body.append(d); d.showModal(); return d;
  },
  confirm: msg => new Promise(res => {
    const d = UI.modal(`<form method="dialog"><h2>Confirmar</h2><p>${msg}</p><div class="row"><button class="btn ghost" value="n">Cancelar</button><button class="btn" value="s" autofocus>Confirmar</button></div></form>`);
    d.addEventListener('close', () => res(d.returnValue === 's'));
  }),
  empty: m => `<div class="empty">${ic('sol')}<p>${m}</p></div>`,
  badge: (t, c = '') => `<span class="badge ${c}">${esc(t)}</span>`,
  stat: (ok, a, b) => UI.badge(ok ? a : b, ok ? 'ok' : 'err'),
  table: (cols, rows, vazio) => rows.length
    ? `<div class="tw"><table class="table"><thead><tr>${cols.map(c => `<th scope="col">${c}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
    : UI.empty(vazio),
  field(f) {      // f = {n:nome, l:rótulo, t:tipo, o:opções, v:valor, r:0 (opcional), x:atributos extras}
    const id = 'f' + (UI.n = (UI.n || 0) + 1) + '_' + f.n, rq = f.r === 0 ? '' : 'required';
    if (f.t === 'img') return `<div class="fld"><span><strong>${f.l}</strong></span><div class="imgp">${f.v ? `<img src="${esc(f.v)}" alt="">` : '<span class="ph">Sem foto</span>'}<label class="btn sm ghost">Escolher foto<input type="file" accept="image/*" hidden data-imgf="${f.n}"></label><input type="hidden" name="${f.n}" value="${esc(f.v)}"></div></div>`;
    if (f.t === 'textarea') return `<div class="fld"><label for="${id}">${f.l}</label><textarea id="${id}" name="${f.n}" rows="5" ${rq} ${f.x || ''}>${esc(f.v)}</textarea></div>`;
    if (f.t === 'check') return `<label class="chk"><input type="checkbox" name="${f.n}" ${rq}><span>${f.l}</span></label>`;
    const o = (f.o || []).map(x => Array.isArray(x) ? x : [x, x[0].toUpperCase() + x.slice(1)]);
    const ctl = f.t === 'select'
      ? `<select id="${id}" name="${f.n}" ${rq}>${f.r === 0 ? '' : '<option value="">Selecione…</option>'}${o.map(([v, t]) => `<option value="${esc(v)}" ${v == f.v ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>`
      : (m => `<input id="${id}" name="${f.n}" type="${m === 'money' ? 'text' : f.t || 'text'}" value="${esc(m === 'money' ? Masks.moneyIn(f.v) : m ? Masks[m](f.v) : f.v)}" ${rq} ${m ? `data-mask="${m}" ${Masks.attrs[m]}` : ''} ${f.x || ''}>`)(Masks.de(f));
    return `<div class="fld"><label for="${id}">${f.l}</label>${ctl}</div>`;
  },
  form(titulo, campos, onSave, btnTxt = 'Salvar') {   // onSave(dados) devolve a mensagem de sucesso ou lança Error
    const d = UI.modal(`<form novalidate><h2>${titulo}</h2>${campos.map(UI.field).join('')}<p class="msg" role="alert"></p><div class="row"><button type="button" class="btn ghost" data-act="fechar">Cancelar</button><button class="btn">${btnTxt}</button></div></form>`);
    const f = $('form', d), btn = $('.btn:not(.ghost)', f), checks = [...f.querySelectorAll('.chk input')], msg = $('.msg', f);
    const sync = () => { btn.disabled = checks.some(c => !c.checked); };   // termos obrigatórios habilitam o botão
    sync(); f.addEventListener('change', sync);
    f.addEventListener('submit', async e => {
      e.preventDefault(); msg.textContent = ''; btn.disabled = true;
      const falta = [...f.elements].find(x => x.required && (x.type === 'checkbox' ? !x.checked : !x.value.trim()));
      try {
        if (falta) { falta.focus(); throw Error(falta.type === 'checkbox' ? 'É preciso aceitar os dois termos.' : `Preencha o campo "${falta.labels?.[0]?.textContent ?? falta.name}".`); }
        const ok = await onSave(Object.fromEntries(new FormData(f)));
        d.close(); UI.toast(ok); Router.render();
      } catch (ex) { msg.textContent = ex.message; } finally { sync(); }
    });
    return d;
  }
};

/* ===== Formulários de cada entidade ===== */
const Forms = {
  usuario(u) {
    const ed = !!u;
    const campos = [
      { n: 'nome', l: 'Nome completo', v: u?.nome }, { n: 'email', l: 'E-mail', t: 'email', v: u?.email },
      { n: 'senha', l: ed ? 'Nova senha (vazio mantém a atual)' : 'Senha (mínimo 6 caracteres)', t: 'password', r: ed ? 0 : 1 },
      { n: 'telefone', l: 'Telefone', t: 'tel', v: u?.telefone }, { n: 'nasc', l: 'Data de nascimento', t: 'date', v: u?.nasc },
      { n: 'nivel', l: 'Nível', t: 'select', o: NIVEIS, v: u?.nivel }
    ];
    if (!ed) campos.push(
      { n: 'uso', t: 'check', l: 'Li e aceito o <button type="button" class="link" data-act="termo" data-t="Termo de Uso">Termo de Uso</button>' },
      { n: 'lgpd', t: 'check', l: 'Li e concordo com o <button type="button" class="link" data-act="termo" data-t="Termo de Consentimento (LGPD)">Termo de Consentimento (LGPD)</button>' });
    UI.form(ed ? 'Editar usuário' : 'Cadastrar usuário', campos, async f => { await Svc.salvarUsuario(f, u?.id); return ed ? 'Usuário atualizado!' : 'Cadastro feito! Agora é só entrar.'; }, ed ? 'Salvar' : 'Cadastrar');
  },
  camp(c) {   // criar (sem c) ou editar campeonato próprio (com c)
    const ed = !!c;
    UI.form(ed ? 'Editar campeonato' : 'Criar campeonato', [
      { n: 'nome', l: 'Nome', v: c?.nome }, { n: 'local', l: 'Praia / local', v: c?.local },
      { n: 'genero', l: 'Tipo (quem pode jogar)', t: 'select', o: GENEROS, v: c?.genero || 'misto' }, { n: 'nivel', l: 'Categoria', t: 'select', o: NIVEIS, v: c?.nivel }, { n: 'inicio', l: 'Data de início', t: 'date', v: c?.inicio },
      { n: 'hora', l: 'Horário de início', t: 'time', r: 0, v: c?.hora }, { n: 'premio', l: 'Premiação total (R$)', t: 'number', r: 0, v: c?.premio || '', x: 'min="0" step="0.01"' },
      { n: 'limite', l: 'Limite de duplas', t: 'number', v: c?.limite }, { n: 'status', l: 'Status', t: 'select', o: ['aberto', 'encerrado'], r: 0, v: c?.status }, { n: 'desc', l: 'Descrição (premiação, horário de início e de término, regras…)', t: 'textarea', r: 0, v: c?.desc }, { n: 'foto', l: 'Foto do campeonato', t: 'img', r: 0, v: c?.foto }],
      async f => { await Svc.salvarCamp(f, c?.id); return ed ? 'Campeonato atualizado!' : 'Campeonato criado!'; }, ed ? 'Salvar' : 'Criar campeonato');
  },
  async partida(camp) {
    const [is, ds] = await lista('inscricoes', 'duplas'), dn = id => ds.find(d => d.id === id)?.nome ?? '—';
    const o = is.filter(i => i.camp === camp && i.ativa).map(i => [i.dupla, dn(i.dupla)]);
    if (o.length < 2) return UI.toast('É preciso ter pelo menos 2 duplas inscritas.', 'err');
    UI.form('Registrar partida', [{ n: 'a', l: 'Dupla A', t: 'select', o }, { n: 'b', l: 'Dupla B', t: 'select', o }, { n: 'sa', l: `Pontos da dupla A (0 a ${PLACAR_MAX})`, t: 'number', x: `min="0" max="${PLACAR_MAX}" step="1"` }, { n: 'sb', l: `Pontos da dupla B (0 a ${PLACAR_MAX})`, t: 'number', x: `min="0" max="${PLACAR_MAX}" step="1"` }, { n: 'data', l: 'Data', t: 'date', v: hoje() }],
      async f => { const p = await Svc.criarPartida({ ...f, camp }); return 'Partida registrada! Vencedora: ' + dn(p.venc); });
  }
};

// Regra do consumidor: cria campeonatos, mas só edita os que ele mesmo criou
Svc.salvarCamp = async (f, id) => {
  const me = Auth.cur(); if (!me) throw Error('Entre na sua conta para criar campeonatos.');
  if (!id && !await ehDono(me.id)) throw Error('Somente donos de quadra podem criar campeonatos.');
  if (+f.limite < 2) throw Error('O limite deve ser de pelo menos 2 duplas.');
  if (f.premio !== '' && f.premio != null && +f.premio < 0) throw Error('A premiação não pode ser negativa.');
  const c = id && await Api.get('campeonatos', id);
  if (c && c.dono !== me.id) throw Error('Você só pode editar campeonatos que criou.');
  return Api.save('campeonatos', { ...f, limite: +f.limite, premio: +f.premio || 0, desc: (f.desc || '').trim(), status: f.status || 'aberto', ...(id ? { id } : { dono: me.id }) });
};

// Solicitações de dupla: quem envia espera; só quem recebe aceita ou recusa (aceitar cria a dupla)
Svc.enviarSolicitacao = async (de, para) => Api.save('solicitacoes', { para });   // quem envia é o usuário do token
Svc.responderSolicitacao = async (id, aceitar) => {   // só quem recebeu responde; aceitar cria a dupla no servidor
  const r = await http('POST', `/solicitacoes/${id}/${aceitar ? 'aceitar' : 'recusar'}`, {});
  if (!aceitar) return null;
  const d = r?.dupla || r; return d && d.id ? doApi('duplas', d) : { id: null };
};
Svc.prepararDemo = async () => { };   // o modo demonstração acabou: os dados agora vêm do banco
Svc.cancelarSolicitacao = async id => { await http('POST', `/solicitacoes/${id}/cancelar`, {}); };

/* ===== Ilustração em SVG (hero e cartões): praia, mar, sol, palmeira, rede e bola ===== */
let _a = 0;
const arte = (c1, c2) => { const n = ++_a; return `<svg viewBox="0 0 600 360" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="g${n}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient><pattern id="p${n}" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M10 0H0V10" fill="none" stroke="#fff" stroke-opacity=".7"/></pattern></defs><rect width="600" height="360" fill="url(#g${n})"/><circle cx="470" cy="85" r="58" fill="#FFE7A3"/><path d="M0 190Q80 160 170 185T340 178T500 168T600 182V360H0Z" fill="#4A8C99"/><path d="M0 250Q300 222 600 255V360H0Z" fill="#F2D7A0"/><path d="M130 360L245 258H515L600 360" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="3"/><rect x="255" y="125" width="250" height="75" fill="url(#p${n})" stroke="#fff" stroke-width="3"/><rect x="249" y="118" width="9" height="148" fill="#164E5C"/><rect x="502" y="118" width="9" height="148" fill="#164E5C"/><path d="M62 310Q72 210 92 125" stroke="#164E5C" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M92 125Q40 90 8 135Q55 108 92 125ZM92 125Q110 70 150 62Q125 100 92 125ZM92 125Q150 100 190 140Q140 125 92 125Z" fill="#164E5C"/><ellipse cx="545" cy="304" rx="31" ry="6" fill="#000" opacity=".22"/><radialGradient id="b${n}" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#fff"/><stop offset=".7" stop-color="#e4e6e8"/><stop offset="1" stop-color="#9aa0a5"/></radialGradient><circle cx="545" cy="275" r="29" fill="url(#b${n})" stroke="#3b4248" stroke-width="1.2"/><path d="M545 261l11 8-4 13h-14l-4-13z" fill="#1d2328"/><path d="M545 261V247M556 269l12-4M552 282l8 11M538 282l-8 11M534 269l-12-4" stroke="#1d2328" stroke-width="1.8" fill="none"/><path d="M568 265l7 9-3 9-9-1zM522 265l-7 9 3 9 9-1zM532 297l13 5 13-5-6-9h-14z" fill="#1d2328" opacity=".85"/><ellipse cx="535" cy="262" rx="9" ry="5" fill="#fff" opacity=".55" transform="rotate(-30 535 262)"/></svg>`; };

/* ===== Perfis, quadras e WhatsApp ===== */
const TIPOS = [['jogador', 'Jogador'], ['dono', 'Dono de quadra'], ['professor', 'Professor']];
const MODOS = [['campeonato', 'Campeonatos'], ['aluguel', 'Aluguel'], ['ambos', 'Campeonatos e aluguel']];
const HABS = ['Chapa', 'Ombro', 'Peito', 'Shark', 'Defesa'];
const wa = (n, m) => `https://wa.me/${String(n || '').replace(/\D/g, '').replace(/^(?!55)/, '55')}?text=${encodeURIComponent(m)}`;
const zap = (n, m, t = 'Chamar no WhatsApp') => `<a class="btn sm wa" target="_blank" rel="noopener" href="${wa(n, m)}">${ic('whats')}${t}</a>`;
const mapa = l => `<a class="link" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(l)}">${ic('local')}${esc(l)}</a>`;
const menuUser = s => { const u = Storage.get('usuarios').find(x => x.id === s.id);
  return `<div class="um"><button class="um-btn" data-act="menu" aria-expanded="false" aria-haspopup="true">${av(u)}<span>${esc(s.nome.split(' ')[0])}</span><span aria-hidden="true">▾</span></button><div class="um-pop" hidden><a href="#minha-dupla">${ic('user')}${u?.tipo === 'dono' ? 'Meu perfil e quadra' : 'Meu perfil e dupla'}</a>${u?.adm ? `<a href="#admin">${ic('edit')}Painel de admin</a>` : ''}<button data-act="perfil">${ic('edit')}Editar perfil</button><button data-act="logout">${ic('exit')}Sair da conta</button></div></div>`; };
const irCad = ed => { F.edit = ed; location.hash === '#cadastro' ? Router.render() : (location.hash = '#cadastro'); };
const lerImg = (file, w, h) => new Promise((ok, no) => {   // recorta e reduz a imagem; devolve data URL
  const r = new FileReader(), img = new Image();
  r.onload = () => { img.src = r.result; };
  img.onload = () => { const c = document.createElement('canvas'), k = Math.max(w / img.width, h / img.height), sw = w / k, sh = h / k; c.width = w; c.height = h; c.getContext('2d').drawImage(img, (img.width - sw) / 2, (img.height - sh) / 2, sw, sh, 0, 0, w, h); ok(c.toDataURL('image/jpeg', .82)); };
  img.onerror = () => no(Error('Não foi possível ler a imagem.')); r.readAsDataURL(file);
});
const adm = () => !!Storage.get('usuarios').find(u => u.id === Auth.cur()?.id)?.adm;
const carregarImg = async i => {
  try {
    const v = await lerImg(i.files[0], +i.dataset.w || 800, +i.dataset.h || 450);
    if (i.dataset.imgf) { const box = i.closest('.imgp'); box.querySelector('input[type=hidden]').value = v; box.querySelector('img,.ph').outerHTML = `<img src="${v}" alt="Prévia">`; return; }
    if (!adm()) throw Error('Apenas o administrador pode trocar estas imagens.');
    await Api.save(i.dataset.col, { id: i.dataset.id, [i.dataset.field]: v }); UI.toast('Imagem atualizada.'); Router.render(true);
  } catch (x) { UI.toast(x.message, 'err'); }
};
async function painelDono(eu) {   // perfil do dono de quadra: só quadras e campeonatos próprios
  const [qs, cs] = await lista('quadras', 'campeonatos'), mq = qs.filter(q => q.dono === eu.id), mc = cs.filter(c => c.dono === eu.id), modos = Object.fromEntries(MODOS);
  return `<div class="grid two"><article class="card"><div class="who">${av(eu, 'big')}<p><strong>${esc(eu.nome)}</strong><br>${esc(eu.email)} · ${esc(eu.telefone)}<br>${UI.badge('Dono de quadra')} ${bSexo(eu)}</p></div><button class="btn sm ghost" data-act="perfil">Editar perfil</button></article>
    <article class="card"><h3>Minha gestão</h3><p>${mq.length} quadra(s) e ${mc.length} campeonato(s). Você gerencia apenas os seus.</p><div class="row l"><button class="btn sm" data-act="novaQuadra">+ Cadastrar quadra</button><button class="btn sm ghost" data-act="novoC">+ Criar campeonato</button></div></article></div>
    <h3>Minhas quadras</h3>${UI.table(['Foto', 'Quadra', 'Local', 'Uso', 'Preço', ''], mq.map(q => [q.foto ? `<img class="th" src="${esc(q.foto)}" alt="">` : '—', esc(q.nome), esc(q.local), esc(modos[q.modo]), q.preco ? R$(q.preco) : '—', `<button class="btn sm ghost" data-act="editarQ" data-id="${q.id}">Editar</button> <button class="btn sm danger" data-act="removerQ" data-id="${q.id}">Remover</button>`]), 'Você ainda não cadastrou quadras.')}
    <h3 style="margin-top:22px">Meus campeonatos</h3>${UI.table(['Campeonato', 'Início', 'Status', ''], mc.map(c => [esc(c.nome), fmt(c.inicio), UI.badge(c.status), `<button class="btn sm ghost" data-act="editarC" data-id="${c.id}">Editar</button>`]), 'Você ainda não criou campeonatos.')}`;
}
const ehDono = async id => (await Api.get('usuarios', id))?.tipo === 'dono';
const R$ = v => 'R$ ' + (+v || 0).toFixed(2).replace('.', ',');
const av = (u, c = '') => u?.foto ? `<img class="av ${c}" src="${esc(u.foto)}" alt="Foto de ${esc(u.nome)}">` : `<span class="av ${c}" aria-hidden="true">${esc((u?.nome || '?')[0])}</span>`;
Svc.valQuadra = f => {
  if (!f.nome?.trim() || !f.local?.trim()) throw Error('Informe o nome e a localização da quadra.');
  if (f.modo !== 'campeonato' && !(+f.preco > 0)) throw Error('Informe o preço do aluguel por hora.');
};
Svc.salvarQuadra = async (f, dono, id) => {
  Svc.valQuadra(f);
  if ((await Api.get('usuarios', dono))?.tipo !== 'dono') throw Error('Somente donos de quadra cadastram quadras.');
  if (id && (await Api.get('quadras', id))?.dono !== dono) throw Error('Você só pode gerenciar as suas próprias quadras.');
  return Api.save('quadras', { ...(id ? { id } : {}), nome: f.nome.trim(), local: f.local.trim(), modo: f.modo, preco: f.modo === 'campeonato' ? 0 : +f.preco, desc: (f.desc || '').trim(), dono, ...(f.foto ? { foto: f.foto } : {}) });
};
Svc.removerQuadra = async id => { if ((await Api.get('quadras', id))?.dono !== Auth.cur()?.id) throw Error('Você só pode remover as suas próprias quadras.'); await Api.remove('quadras', id); };
Forms.quadra = q => UI.form(q ? 'Editar quadra' : 'Cadastrar quadra', [{ n: 'nome', l: 'Nome da quadra', v: q?.nome }, { n: 'local', l: 'Localização (endereço ou praia)', v: q?.local }, { n: 'modo', l: 'Uso', t: 'select', o: MODOS, v: q?.modo }, { n: 'preco', l: 'Preço do aluguel por hora (R$)', t: 'number', r: 0, v: q?.preco || '', x: 'min="0" step="0.01"' }, { n: 'desc', l: 'Descrição da quadra (estrutura, horários, regras…)', t: 'textarea', r: 0, v: q?.desc }, { n: 'foto', l: 'Foto da quadra', t: 'img', r: 0, v: q?.foto }],
  async f => { await Svc.salvarQuadra(f, Auth.cur().id, q?.id); return q ? 'Quadra atualizada!' : 'Quadra cadastrada!'; }, q ? 'Salvar' : 'Cadastrar');
const TERMO = [
  ['Termo de Uso do Sistema “FTVWorld”', 'Este Termo de Uso (“Termo”) é um acordo legal entre você, usuário(a) do sistema “FTVWorld”, e os desenvolvedores do Projeto “FTVWorld”, um sistema pensado para o gerenciamento de campeonatos de futevôlei, permitindo o cadastro de jogadores, a formação de duplas, a inscrição em campeonatos, o agendamento de partidas em quadras parceiras e a consulta de rankings e relatórios estatísticos do esporte.', 'Ao acessar ou utilizar o “FTVWorld”, você manifesta sua concordância integral com este Termo, com a Política de Privacidade e com a Lei Geral de Proteção de Dados Pessoais (LGPD – Lei nº 13.709/2018). Se não concordar, não deverá utilizar o sistema.'],
  ['Cláusula 1 – Das condições gerais de uso', 'O “FTVWorld” é destinado à organização e gestão de campeonatos de futevôlei, permitindo que jogadores se cadastrem, formem duplas, se inscrevam em campeonatos, consultem quadras disponíveis, acompanhem o andamento de partidas e visualizem rankings e estatísticas de desempenho.'],
  ['Cláusula 2 – Da coleta e uso de dados pessoais', 'O usuário declara estar ciente da coleta e uso dos seguintes dados, que visam exclusivamente permitir o cadastro, a identificação e a organização de sua participação nos campeonatos:', ['<b>Nome completo</b> — identificação do jogador nas telas de campeonatos, duplas e partidas.', '<b>E-mail</b> — login de acesso e canal de comunicação sobre campeonatos e notificações.', '<b>Senha</b> — usada exclusivamente para autenticação, armazenada de forma protegida.', '<b>Telefone</b> — canal de contato alternativo sobre campeonatos e partidas.', '<b>Cidade</b> — usada para sugerir campeonatos e quadras próximas ao usuário.', '<b>Nível de jogo</b> — usado para organizar duplas e campeonatos compatíveis com a experiência do jogador.', '<b>Foto, vídeo e descrição do perfil (opcionais)</b> — exibidos no perfil público para outros jogadores que buscam dupla. E-mail e data de nascimento não são exibidos; o contato é feito por um botão de WhatsApp.']],
  ['Cláusula 3 – Finalidade da coleta', 'A coleta tem finalidades específicas e essenciais para a operação do “FTVWorld” e a conformidade com a LGPD:', ['Cadastro e autenticação do usuário no sistema.', 'Formação de duplas e organização de inscrições em campeonatos.', 'Agendamento e acompanhamento de partidas, incluindo quadra, horário e resultado.', 'Geração de rankings de duplas e relatórios de desempenho (ex.: número de vitórias, histórico de partidas).', 'Comunicação com o usuário sobre campeonatos, inscrições e notificações do sistema.', 'Envio, aceite e recusa de solicitações de dupla entre jogadores.']],
  ['Cláusula 4 – Vedações do uso', 'O usuário compromete-se a não utilizar o “FTVWorld” para qualquer finalidade ilícita ou que viole este Termo, incluindo:', ['Carregar conteúdo ilegal, difamatório, obsceno ou prejudicial.', 'Acessar, alterar ou danificar contas de outros usuários.', 'Cadastrar dados falsos de campeonatos, quadras, duplas ou resultados de partidas.', 'Violar direitos de propriedade intelectual ou outros direitos de terceiros.']],
  ['Cláusula 5 – Da ciência e aceite dos termos', 'O uso do sistema pressupõe a leitura prévia, a compreensão e a concordância com este Termo, com a Política de Privacidade e com a Lei nº 13.709/2018 (LGPD). O consentimento para o tratamento de dados pessoais é coletado de forma expressa, específica e destacada, conforme exige o art. 8º da LGPD, sendo vedada sua obtenção por aceitação genérica, tácita ou implícita. O titular que não concordar deverá abster-se de utilizar o sistema.'],
  ['Cláusula 6 – Da proteção dos dados', 'O “FTVWorld” compromete-se a adotar medidas técnicas e administrativas em conformidade com a LGPD e as normas ISO/IEC 27001, 27701 e 29100:', ['Senhas armazenadas com proteção adequada, nunca em texto simples.', 'Banco de dados com autenticação e acesso restrito à equipe responsável.', 'Políticas de segurança da informação e plano de resposta a incidentes.', 'Notificação ao titular e à Autoridade Nacional de Proteção de Dados (ANPD), em prazo razoável, nos casos de incidente de segurança que possa acarretar risco ou dano relevante (art. 48 da LGPD).']],
  ['Cláusula 7 – Do compartilhamento de dados', 'Os dados armazenados não serão compartilhados com terceiros, exceto:', ['Quando autorizado expressamente pelo titular.', 'Mediante obrigação legal ou ordem judicial.', 'Para auxílio técnico restrito e necessário à operação do sistema.']],
  ['Cláusula 8 – Dos direitos do titular dos dados', 'Em conformidade com a LGPD, o sistema deve permitir ao usuário exercer seus direitos, incluindo:', ['Confirmação da existência de tratamento e acesso aos dados (art. 18, I e II).', 'Correção de dados incompletos, inexatos ou desatualizados (art. 18, III).', 'Anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade com a LGPD (art. 18, IV).', 'Portabilidade dos dados a outro fornecedor, mediante requisição expressa, observados os segredos comercial e industrial (art. 18, V).', 'Eliminação dos dados tratados com base no consentimento, após sua revogação, ressalvadas as hipóteses legais de conservação (art. 18, VI, e art. 16).', 'Informação sobre as entidades com as quais o controlador realizou uso compartilhado de dados (art. 18, VII).', 'Informação sobre a possibilidade de não fornecer consentimento e sobre as consequências da negativa (art. 18, VIII).', 'Revogação do consentimento a qualquer momento, mediante manifestação expressa e gratuita (art. 18, IX, e art. 8º, § 5º).', 'Exclusão da conta e dos dados armazenados, mediante solicitação formal (art. 18, IV).', 'Petição à ANPD quando a resposta do controlador for insatisfatória (art. 18, § 1º).'], 'Os direitos podem ser exercidos a qualquer momento, mediante requerimento expresso ao controlador, que responderá em prazo não superior a 15 (quinze) dias (art. 18, § 3º). Canal do Encarregado (DPO): futevoleiworld@gmail.com.'],
  ['Cláusula 9 – Do responsável pelo tratamento', 'O Projeto “FTVWorld” é responsável pelo tratamento dos dados e indica como Encarregado de Dados (DPO): <b>Davi César</b>, Encarregado de Dados do Projeto. Contato: futevoleiworld@gmail.com.'],
  ['Cláusula 10 – Da exatidão dos dados', 'O usuário é responsável pela exatidão, veracidade e atualização dos dados fornecidos, incluindo cadastro, resultados de partidas e dados de campeonatos e quadras. O “FTVWorld” não se responsabiliza por inconsistências inseridas pelo usuário.'],
  ['Cláusula 11 – Da transparência', 'O “FTVWorld” garante transparência sobre o tratamento dos dados pessoais. Os requerimentos dos titulares serão atendidos em prazo não superior a 15 (quinze) dias (art. 18, § 3º). Caso a resposta não seja satisfatória, o titular poderá peticionar à ANPD (art. 18, § 1º). O tratamento de dados deve sempre estar fundamentado em base legal adequada (art. 7º da LGPD), indicada de forma específica para cada atividade de tratamento.'],
  ['Cláusula 12 – Dados de crianças e adolescentes', 'O “FTVWorld” pode ser utilizado por jogadores adolescentes e observa o art. 14 da LGPD:', ['Dados de crianças (menores de 12 anos) somente serão tratados mediante consentimento específico e em destaque de ao menos um dos pais ou responsável legal.', 'Dados de adolescentes (de 12 a 17 anos) serão tratados de forma prioritária no seu melhor interesse, garantindo segurança, privacidade e respeito ao desenvolvimento.', 'O sistema mantém controles técnicos e administrativos adequados, conforme a LGPD e a ISO/IEC 27701, para assegurar confidencialidade, integridade e uso responsável das informações.', 'O consentimento dos responsáveis poderá ser verificado no cadastro e revogado a qualquer momento.']],
  ['Cláusula 13 – Disposições gerais', 'Este Termo pode ser atualizado periodicamente para refletir mudanças legais ou operacionais. Em caso de alterações relevantes que afetem direitos dos titulares, o usuário será notificado pelo sistema ou por e-mail com antecedência mínima de 15 (quinze) dias, salvo determinação legal ou judicial que exija adoção imediata. O uso continuado após a notificação implica ciência e concordância.', 'Este Termo é regido pela legislação brasileira e pela LGPD. Os dados pessoais serão conservados pelo prazo estritamente necessário às finalidades da coleta (art. 15) e eliminados ao término do tratamento, salvo as hipóteses de conservação do art. 16 (obrigação legal ou regulatória, uso exclusivo do controlador com anonimização, transferência a terceiro mediante consentimento, ou pesquisa).'],
  ['Cláusula 14 – Do foro', 'Fica eleito o foro da comarca de Belo Horizonte/MG para dirimir eventuais controvérsias.']
];
const termoHtml = () => `<h2>Termo de Uso e Privacidade</h2><div class="termo">${TERMO.map(([t, ...ps]) => `<h3>${t}</h3>${ps.map(p => Array.isArray(p) ? `<ul>${p.map(x => `<li>${x}</li>`).join('')}</ul>` : `<p>${p}</p>`).join('')}`).join('')}</div><div class="row"><button class="btn" data-act="fechar" autofocus>Entendi</button></div>`;
const ICON = {
  termos: '<path d="M7 3h8l4 4v14H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
  local: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  camera: '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
  galeria: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M21 16l-5-5-8 8"/>'
};
Object.assign(ICON, {
  whats: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-5A8 8 0 1 1 21 12z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
  exit: '<path d="M10 4H5v16h5M15 8l4 4-4 4M19 12H9"/>',
  sol: '<circle cx="12" cy="9" r="4"/><path d="M12 2v2M4.2 5l1.4 1.4M19.8 5l-1.4 1.4M3 20c3-2 6-2 9 0s6 2 9 0"/>',
  quadra: '<rect x="3" y="6" width="18" height="12" rx="1"/><path d="M12 6v12M3 12h18"/>',
  trofeu: '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
  prof: '<path d="M3 9l9-5 9 5-9 5z"/><path d="M7 11.5V16c2.5 2 7.5 2 10 0v-4.5"/>',
  bola: '<circle cx="12" cy="12" r="9"/><path d="M12 8l3.5 2.5-1.3 4h-4.4l-1.3-4z"/>',
  seta: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14a6.5 6.5 0 0 1 3.5 6"/>',
  grafico: '<path d="M4 20V4M4 20h16M8 16v-4M12 16V8M16 16v-6"/>'
});
const IK = { jogador: 'bola', dono: 'quadra', professor: 'prof' };
const ic = k => `<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${ICON[k]}</svg>`;
const PASSOS = {   // aceites e permissões pedidos um após o outro, a cada entrada no site
  lgpd: { t: 'Consentimento LGPD', chk: true, req: true, d: 'Para usar o FTV World, precisamos do seu consentimento para tratar seus dados pessoais, conforme a Lei Geral de Proteção de Dados (Lei nº 13.709/2018).', c: 'Consinto, de forma livre, informada e específica, com o tratamento dos meus dados pessoais para as finalidades descritas no <button type="button" class="link" data-act="_t" data-t="Termo de Consentimento (LGPD)">Termo de Consentimento (LGPD)</button>. Posso revogar este consentimento a qualquer momento.', x: 'Encarregado de dados (DPO): futevoleiworld@gmail.com' },
  uso: { t: 'Termo de Uso', chk: true, req: true, d: 'Leia o termo e aceite para continuar usando o FTV World.', c: 'Li e aceito o <button type="button" class="link" data-act="termo">Termo de Uso</button> e a Política de Privacidade.' },
  local: { t: 'Localização', d: 'Permitir que o FTV World acesse a localização do seu aparelho?', u: 'Usada para sugerir quadras, professores e campeonatos próximos a você. Não é compartilhada com terceiros.', ask: () => new Promise((a, b) => navigator.geolocation.getCurrentPosition(a, b)) },
  camera: { t: 'Câmera', d: 'Permitir que o FTV World use a câmera do seu aparelho?', u: 'Usada somente quando você escolher tirar uma foto para o seu perfil. Nada é gravado sem a sua ação.', ask: async () => (await navigator.mediaDevices.getUserMedia({ video: true })).getTracks().forEach(t => t.stop()) },
  galeria: { t: 'Termo de acesso à galeria', chk: true, d: 'Para escolher a foto do perfil e o vídeo jogando, o FTV World precisa acessar as fotos e os vídeos do seu aparelho.', c: 'Autorizo o FTV World a acessar a galeria de fotos e vídeos do meu aparelho. Apenas o arquivo que eu selecionar será utilizado.' }
};
function pedirPermissoes() {   // toda entrada no site: LGPD, termo de uso, localização, câmera e, no celular, galeria
  const mobile = matchMedia('(pointer:coarse)').matches || /Android|iPhone|iPad/i.test(navigator.userAgent);
  const ord = ['lgpd', 'uso', 'local', 'camera', ...(mobile ? ['galeria'] : [])], reg = {}; let i = 0;
  const d = UI.modal(''); d.classList.add('perm'); d.addEventListener('cancel', e => e.preventDefault());
  const passo = () => {
    const k = ord[i], p = PASSOS[k];
    d.innerHTML = `<div class="steps" aria-hidden="true">${ord.map((_, j) => `<i class="${j <= i ? 'on' : ''}"></i>`).join('')}</div><p class="et">Etapa ${i + 1} de ${ord.length}</p><div class="pico"><svg class="pi" viewBox="0 0 24 24" aria-hidden="true">${ICON[k] || ICON.termos}</svg></div>` + (p.chk
      ? `<h2>${p.t}</h2><p>${p.d}</p><label class="chk"><input type="checkbox" data-c><span>${p.c}</span></label>${p.x ? `<p class="mut sm">${p.x}</p>` : ''}<div class="row"><button class="btn ghost" data-p="no">Recusar</button><button class="btn" data-p="ok" disabled>Aceitar e continuar</button></div>`
      : `<h2>${p.t}</h2><p>${p.d}</p><p class="mut">${p.u}</p><p class="mut sm">Você pode alterar essa permissão a qualquer momento nas configurações do navegador ou do aparelho.</p><div class="row"><button class="btn ghost" data-p="no">Recusar</button><button class="btn" data-p="ok" autofocus>Permitir</button></div>`);
  };
  d.addEventListener('change', e => { if (e.target.matches('[data-c]')) d.querySelector('[data-p=ok]').disabled = [...d.querySelectorAll('[data-c]')].some(c => !c.checked); });
  d.addEventListener('click', async e => {
    const b = e.target.closest('[data-p]'); if (!b) return; const k = ord[i], P = PASSOS[k], nao = b.dataset.p === 'no';
    if (nao && P.req) { bloqueio(k); return; }   // termo obrigatório recusado: não dá para usar o site
    b.disabled = true;
    if (nao) reg[k] = 'recusada';   // permissão opcional recusada: segue sem ela
    else if (P.chk) reg[k] = new Date().toISOString();   // data/hora do aceite
    else { try { await P.ask(); reg[k] = 'concedida'; } catch { reg[k] = 'negada'; } }   // se o navegador bloquear, segue sem travar o acesso
    if (++i < ord.length) passo(); else { LS.setItem('fv3_lgpd', JSON.stringify({ ...reg, versao: '2025' })); d.close(); UI.toast('Suas escolhas foram registradas.'); }
  });
  const bloqueio = k => {   // sem LGPD/Termo de Uso o sistema não pode ser usado
    d.innerHTML = `<div class="pico"><svg class="pi" viewBox="0 0 24 24" aria-hidden="true">${ICON.termos}</svg></div><h2>Não é possível continuar</h2><p>Sem aceitar o <strong>${PASSOS[k].t}</strong> não podemos tratar seus dados nem liberar o uso do FTV World.</p><p class="mut sm">Você pode voltar e rever os termos quando quiser. Se preferir, é só fechar esta página.</p><div class="row"><button class="btn" data-v autofocus>Voltar e revisar</button></div>`;
    d.querySelector('[data-v]').onclick = () => passo();
  };
  passo();
}





/* ===== Páginas ===== */
const lista = (...t) => Promise.all(t.map(Api.list));
const videoField = u => `<div class="fld"><span><strong>Vídeo jogando (opcional)</strong></span><div class="vid">${u?.video ? `<video controls playsinline preload="metadata" src="${esc(u.video)}"></video>` : '<span class="ph">Sem vídeo</span>'}<div class="row l"><label class="btn sm ghost">${ic('galeria')}Escolher vídeo<input type="file" accept="video/*" hidden data-video></label><button type="button" class="btn sm ghost" data-act="rmVideo">Remover vídeo</button></div><input type="hidden" name="video" value="${esc(u?.video)}"><p class="mut">Vídeo curto, até 1,5 MB. Para vídeos maiores, cole um link abaixo.</p></div></div>` + UI.field({ n: 'videoUrl', l: 'Ou link do vídeo (YouTube, Instagram…)', t: 'url', r: 0, v: u?.videoUrl, x: 'placeholder="https://"' });
const moeda = v => 'R$ ' + (+v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const sit = c => c.status !== 'aberto' ? UI.badge('Encerrado', 'err') : c.vagas <= 0 ? UI.badge('Lotado', 'err') : UI.badge(`${c.vagas} ${c.vagas === 1 ? 'vaga livre' : 'vagas livres'}`, 'ok');
const btnInsc = (c, insc, souDono) => souDono ? '' : insc ? `<button class="btn sm danger" data-act="cancelarInsc" data-id="${insc.id}">Cancelar inscrição</button>` : c.status !== 'aberto' || c.vagas <= 0 ? '' : `<button class="btn sm" data-act="inscMinha" data-id="${c.id}">Inscrever minha dupla</button>`;
async function abrirCamp(id) {   // página de detalhes do campeonato (modal)
  const me = Auth.cur(), [cs, is, ds, us] = await lista('campeonatos', 'inscricoes', 'duplas', 'usuarios');
  const c0 = cs.find(x => x.id === id); if (!c0) throw Error('Campeonato não encontrado.');
  const ativos = is.filter(i => i.camp === id && i.ativa), c = { ...c0, vagas: Math.max(0, c0.limite - ativos.length) };
  const eu = me && us.find(u => u.id === me.id), meu = me && c.dono === me.id;
  const minha = me && ds.find(d => d.ativa && (d.j1 === me.id || d.j2 === me.id)), insc = minha && ativos.find(i => i.dupla === minha.id);
  const org = us.find(u => u.id === c.dono), cl = await sp_classificacaoCamp(id);
  const info = [['Premiação', c.premio > 0 ? `<span class="pr">${moeda(c.premio)}</span>` : 'A definir'], ['Início', `${fmt(c.inicio)}${c.hora ? ' às ' + esc(c.hora) : ''}`], ['Local', mapa(c.local)],
    ['Vagas', `${c.vagas} livres de ${c.limite} <span class="mut">(${ativos.length} ${ativos.length === 1 ? 'dupla inscrita' : 'duplas inscritas'})</span>`]];
  const d = UI.modal(`<div class="dh">${c.foto ? `<img src="${esc(c.foto)}" alt="Foto de ${esc(c.nome)}">` : arte(...TONS[cs.indexOf(c0) % 3])}</div>
    <h2>${esc(c.nome)}</h2><p>${UI.badge(c.nivel)} ${bGen(c)} ${sit(c)}</p>
    <dl class="info">${info.map(([t, v]) => `<div><dt>${t}</dt><dd>${v}</dd></div>`).join('')}</dl>
    <h3>Sobre o campeonato</h3><p class="desc">${c.desc ? esc(c.desc) : 'O organizador ainda não adicionou uma descrição.'}</p>
    ${org ? `<p class="mut">Organizador: <strong>${esc(org.nome)}</strong></p>${org.telefone ? zap(org.telefone, `Olá! Vi o campeonato "${c.nome}" no FTV World e quero saber mais.`, 'Falar com o organizador') : ''}` : ''}
    <h3>Classificação</h3>${UI.table(['#', 'Dupla', 'Vitórias'], cl.map((r, i) => [i + 1 + 'º', esc(r.nome), r.v]), 'Nenhuma dupla inscrita ainda. A classificação aparece quando as partidas forem registradas.')}
    <div class="row l" style="margin-top:18px">${btnInsc(c, insc, eu?.tipo === 'dono')}${meu ? `<button class="btn sm ghost" data-act="editarC" data-id="${c.id}">Editar</button><button class="btn sm ghost" data-act="partida" data-id="${c.id}">Registrar partida</button>` : ''}<button class="btn sm ghost" data-act="fechar">Fechar</button></div>`);
  d.classList.add('det');
}
const btnSol = (me, uid, ds, ss) => {   // botão certo conforme a situação da solicitação com essa pessoa
  if (!me || me.id === uid || ds.some(d => d.ativa && (d.j1 === me.id || d.j2 === me.id))) return '';
  const p = ss.filter(s => s.status === 'pendente'), env = p.find(s => s.de === me.id && s.para === uid), rec = p.find(s => s.de === uid && s.para === me.id);
  if (env) return `${UI.badge('Solicitação enviada')}<button class="btn sm ghost" data-act="cancelarSol" data-id="${env.id}">Cancelar</button>`;
  if (rec) return `<button class="btn sm" data-act="aceitarSol" data-id="${rec.id}">Aceitar solicitação</button><button class="btn sm ghost" data-act="recusarSol" data-id="${rec.id}">Recusar</button>`;
  return `<button class="btn sm" data-act="enviarSol" data-id="${uid}">Enviar solicitação de dupla</button>`;
};
async function abrirPerfil(id) {   // perfil público: só apresentação + contato pelo WhatsApp (nunca e-mail, telefone escrito, nascimento ou senha)
  const me = Auth.cur(), [us, cs, ds, ss] = await lista('usuarios', 'candidatos', 'duplas', 'solicitacoes'), u = us.find(x => x.id === id);
  if (!u || (u.tipo || 'jogador') !== 'jogador') throw Error('Perfil não encontrado.');
  const c = cs.find(x => x.user === id), meu = me && me.id === id, habs = (u.hab || '').split(',').filter(Boolean);
  const video = u.video && /^data:video\//.test(u.video) ? `<video class="pv" controls playsinline preload="metadata" src="${esc(u.video)}"></video>`
    : u.videoUrl && /^https?:\/\//i.test(u.videoUrl) ? `<a class="btn sm" target="_blank" rel="noopener" href="${esc(u.videoUrl)}">Assistir ao vídeo</a>` : '<p class="mut">Ainda não adicionou um vídeo jogando.</p>';
  const d = UI.modal(`<div class="who">${av(u, 'big')}<div><h2>${esc(u.nome)}</h2><p style="margin:6px 0 0">${bSexo(u)} ${UI.badge(u.nivel || 'iniciante')} ${u.perna ? UI.badge('Perna ' + u.perna) : ''}</p></div></div>
    ${habs.length ? `<h3>Habilidades</h3><p>${habs.map(h => UI.badge(h)).join(' ')}</p>` : ''}
    <h3>Sobre</h3><p class="desc">${u.bio ? esc(u.bio) : 'Este jogador ainda não escreveu uma descrição.'}</p>
    ${c?.msg ? `<h3>Recado</h3><p class="desc">“${esc(c.msg)}”</p>` : ''}
    <h3>Vídeo jogando</h3>${video}
    <div class="row l" style="margin-top:18px">${meu ? '<button class="btn sm" data-act="perfil">Editar meu perfil</button>' : btnSol(me, u.id, ds, ss) + zap(u.telefone, `Olá, ${u.nome}! Vi seu perfil no FTV World e quero jogar com você.`, 'Chamar no WhatsApp')}<button class="btn sm ghost" data-act="fechar">Fechar</button></div>`);
  d.classList.add('det');
}
async function bannerSol(me) {   // destaque na página inicial: solicitação de dupla recebida
  if (!me) return '';
  const [ss, us] = await lista('solicitacoes', 'usuarios'), s = ss.find(x => x.status === 'pendente' && x.para === me.id), u = s && us.find(x => x.id === s.de);
  if (!u) return '';
  return `<section class="solb" aria-label="Solicitação de dupla"><div class="who">${av(u, 'big')}<div><span class="etq2">Nova solicitação de dupla</span><h3>${esc(u.nome)} quer formar dupla com você</h3><p>${bSexo(u)} ${UI.badge(u.nivel || 'iniciante')} ${u.perna ? UI.badge('Perna ' + u.perna) : ''}</p>${u.bio ? `<p class="bio">“${esc(u.bio)}”</p>` : ''}</div></div><div class="row l"><button class="btn" data-act="aceitarSol" data-id="${s.id}">Aceitar e formar dupla</button><button class="btn ghost" data-act="verPerfil" data-id="${u.id}">Ver perfil</button><button class="btn ghost" data-act="recusarSol" data-id="${s.id}">Recusar</button></div></section>`;
}
const F = { cat: '' };   // filtro de categoria ativo
const TONS = [['#F7B267', '#F9DDA4'], ['#8EC5B6', '#DDE9CC'], ['#9AA8C9', '#E6D6C3']];

/* ===== Painel de administração ===== */
const A = { aba: 'geral', q: '', tipo: '', st: '', pg: 1 };   // estado do painel: aba, busca, filtros e página
const PAG = 10, MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const ROT = { jogador: 'Jogador', dono: 'Dono de quadra', professor: 'Professor', admin: 'Administrador' };
const TP = u => u.adm ? 'admin' : (u.tipo || 'jogador');
const quando = u => u.criado || u.aceite || '';
const dataBr = s => s ? new Date(s).toLocaleDateString('pt-BR') : '—';
const norm = s => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const haDias = s => { if (!s) return '—'; const d = Math.floor((Date.now() - new Date(s)) / 864e5); return d <= 0 ? 'hoje' : d === 1 ? 'ontem' : `há ${d} dias`; };
const plural = (n, a, b) => `${n} ${n === 1 ? a : b}`;
const exigeAdm = () => { if (!adm()) throw Error('Apenas o administrador pode fazer isso.'); };
const logar = async () => { };   // o servidor registra o log sozinho a cada ação

Svc.adminBloquear = async id => {
  exigeAdm(); const u = await Api.get('usuarios', id);
  if (!u) throw Error('Usuário não encontrado.');
  if (u.adm) throw Error('Não é possível bloquear um administrador.');
  const b = !u.bloqueado; await Api.save('usuarios', { id, bloqueado: b, motivo: b ? 'Bloqueado pelo administrador' : '' });
  await logar(`${b ? 'Bloqueou' : 'Desbloqueou'} a conta de ${u.nome}`); return b;
};
Svc.adminToggleAdm = async id => {
  exigeAdm(); const u = await Api.get('usuarios', id);
  if (!u) throw Error('Usuário não encontrado.');
  if (id === Auth.cur()?.id || id === 'admin') throw Error('Não é possível alterar o acesso desta conta.');
  const v = !u.adm; await Api.save('usuarios', { id, adm: v });
  await logar(`${v ? 'Concedeu' : 'Removeu'} o acesso de administrador de ${u.nome}`); return v;
};
Svc.adminExcluirCamp = async id => { exigeAdm(); await Api.remove('campeonatos', id); };   // o servidor recusa (409) se houver registros vinculados
Svc.adminExcluirUsuario = async id => {
  exigeAdm(); const u = await Api.get('usuarios', id);
  if (!u) throw Error('Usuário não encontrado.');
  if (u.adm) throw Error('Não é possível excluir um administrador.');
  await Api.remove('usuarios', id);
};

async function admDados() {
  const [us, cs, qs, ds, is, ps, ss, cd, lg, cf] = await lista('usuarios', 'campeonatos', 'quadras', 'duplas', 'inscricoes', 'partidas', 'solicitacoes', 'candidatos', 'logs', 'config');
  const ativas = is.filter(i => i.ativa), t = k => us.filter(u => TP(u) === k);
  return { us, cs, qs, ds, is, ps, ss, cd, lg, cf, ativas, insc: id => ativas.filter(i => i.camp === id).length,
    jog: t('jogador'), don: t('dono'), prof: t('professor'), admins: t('admin'), ab: cs.filter(c => c.status === 'aberto'), en: cs.filter(c => c.status !== 'aberto') };
}

/* gráficos em SVG: as cores vêm do CSS (.s-j, .s-d, .s-p, .dn.j …) */
function gBarras(meses) {   // novos cadastros por mês, empilhados por tipo
  const W = 560, H = 250, L = 34, B = 30, T = 20, R = 8, top = Math.max(4, Math.ceil(Math.max(...meses.map(m => m.j + m.d + m.p)) / 4) * 4);
  const bw = (W - L - R) / meses.length, y = v => T + (H - T - B) * (1 - v / top);
  const grade = [0, .25, .5, .75, 1].map(f => { const v = Math.round(top * f), yy = y(v); return `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}" class="gl"/><text x="${L - 6}" y="${yy + 4}" text-anchor="end" class="gt">${v}</text>`; }).join('');
  const barras = meses.map((m, i) => {
    let ac = 0; const x = L + i * bw + bw * .2, w = bw * .6;
    const seg = [['j', m.j], ['d', m.d], ['p', m.p]].map(([k, v]) => { if (!v) return ''; const y0 = y(ac + v), h = y(ac) - y0; ac += v; return `<rect x="${x}" y="${y0}" width="${w}" height="${h}" rx="2" class="s-${k}"/>`; }).join('');
    return `${seg}<text x="${x + w / 2}" y="${y(ac) - 6}" text-anchor="middle" class="gv">${ac}</text><text x="${x + w / 2}" y="${H - 9}" text-anchor="middle" class="gt">${m.l}</text>`;
  }).join('');
  return `<svg viewBox="0 0 ${W} ${H}" class="gr" role="img" aria-label="Novos cadastros por mês, separados por jogadores, donos de quadra e professores">${grade}${barras}</svg>`;
}
function gRosca(fat, total) {   // fat: [[rótulo, valor, classe]]
  let ac = 0;
  const seg = fat.filter(f => f[1]).map(([, v, k]) => { const p = 100 * v / total, s = `<circle class="dn ${k}" r="15.9155" cx="21" cy="21" stroke-dasharray="${Math.max(p - .7, .2)} ${100 - Math.max(p - .7, .2)}" stroke-dashoffset="${25 - ac}"/>`; ac += p; return s; }).join('');
  return `<svg viewBox="0 0 42 42" class="rosca" role="img" aria-label="Usuários por tipo"><circle class="dn bg" r="15.9155" cx="21" cy="21"/>${seg}<text x="21" y="22.5" text-anchor="middle" class="rt">${total}</text><text x="21" y="27.5" text-anchor="middle" class="rs">usuários</text></svg>`;
}
const hbars = it => { const m = Math.max(1, ...it.map(x => x[1])); return it.map(([r, n]) => `<div class="hb"><span>${esc(r)}</span><div class="bar"><i style="width:${Math.round(100 * n / m)}%"></i></div><b>${n}</b></div>`).join(''); };
function gMeses(us) {   // últimos seis meses
  const h = new Date(), out = [];
  for (let i = 5; i >= 0; i--) { const d = new Date(h.getFullYear(), h.getMonth() - i, 1); out.push({ k: d.getFullYear() * 100 + d.getMonth(), l: MESES[d.getMonth()], j: 0, d: 0, p: 0 }); }
  us.forEach(u => { const c = new Date(quando(u)), m = out.find(x => x.k === c.getFullYear() * 100 + c.getMonth()); if (m) m[{ dono: 'd', professor: 'p' }[u.tipo] || 'j']++; });
  return out;
}
const kpi = (ico, n, rot, sub, cor = '') => `<article class="kpi ${cor}"><span class="ki">${ic(ico)}</span><div><b>${n}</b><span class="kl">${rot}</span><small>${sub}</small></div></article>`;
const mini = (n, t) => `<span class="mini"><b>${n}</b>${t}</span>`;
const acard = (t, sub, corpo, cls = '') => `<section class="card ac-card ${cls}"><h3>${t}</h3>${sub ? `<p class="mut ac-sub">${sub}</p>` : ''}${corpo}</section>`;

async function admGeral(D) {
  const { us, cs, qs, ds, ps, ss, ab, en, jog, don, prof, lg } = D, ago = Date.now() - 30 * 864e5;
  const dAt = ds.filter(d => d.ativa), emDupla = new Set(dAt.flatMap(d => [d.j1, d.j2])), jogEm = jog.filter(j => emDupla.has(j.id)).length;
  const novos = us.filter(u => new Date(quando(u)).getTime() >= ago).length, media = prof.length ? prof.reduce((s, p) => s + (+p.valor || 0), 0) / prof.length : 0;
  const premioAb = ab.reduce((s, c) => s + (+c.premio || 0), 0), pend = ss.filter(s => s.status === 'pendente').length;
  const lotados = ab.filter(c => D.insc(c.id) >= c.limite), vazios = ab.filter(c => !D.insc(c.id)), bloq = us.filter(u => u.bloqueado), semFoto = qs.filter(q => !q.foto);
  const semDupla = jog.filter(j => !emDupla.has(j.id) && !j.bloqueado).length, rank = (await sp_rankingDuplas()).slice(0, 5), meses = gMeses(us);
  const tipos = [['Jogadores', jog.length, 'j'], ['Donos de quadra', don.length, 'd'], ['Professores', prof.length, 'p'], ['Administradores', D.admins.length, 'a']];
  const niv = NIVEIS.map(n => [n[0].toUpperCase() + n.slice(1), jog.filter(j => j.nivel === n).length]);
  const alertas = [[bloq.length, plural(bloq.length, 'conta bloqueada', 'contas bloqueadas'), 'usuarios', '', 'bloqueado'], [lotados.length, plural(lotados.length, 'campeonato lotado', 'campeonatos lotados'), 'campeonatos', '', 'lotado'],
    [vazios.length, plural(vazios.length, 'campeonato aberto sem inscrições', 'campeonatos abertos sem inscrições'), 'campeonatos', '', 'aberto'], [semDupla, plural(semDupla, 'jogador sem dupla', 'jogadores sem dupla'), 'usuarios', 'jogador', ''],
    [semFoto.length, plural(semFoto.length, 'quadra sem foto', 'quadras sem foto'), 'imagens', '', ''], [pend, plural(pend, 'solicitação de dupla pendente', 'solicitações de dupla pendentes'), '', '', '']].filter(a => a[0]);
  const ocup = ab.slice().sort((a, b) => (a.inicio || '').localeCompare(b.inicio || '')).map(c => { const n = D.insc(c.id), p = Math.min(100, Math.round(100 * n / c.limite)), cheio = n >= c.limite;
    return `<div class="oc"><div class="oc-l"><span><strong>${esc(c.nome)}</strong><br><span class="mut">${esc(c.local)} · ${fmt(c.inicio)}</span></span><b>${n}/${c.limite}${cheio ? ' · lotado' : ''}</b></div><div class="bar"><i class="${cheio ? 'full' : ''}" style="width:${p}%"></i></div></div>`; }).join('');
  const recentes = us.slice().sort((a, b) => quando(b).localeCompare(quando(a))).slice(0, 6).map(u => `<li>${av(u)}<div><strong>${esc(u.nome)}</strong><br><span class="mut">${ROT[TP(u)]} · ${haDias(quando(u))}</span></div></li>`).join('');
  const acoes = lg.slice().sort((a, b) => b.data.localeCompare(a.data)).slice(0, 6).map(l => `<li><span>${esc(l.acao)}</span><span class="mut">${esc(l.quem)} · ${haDias(l.data)}</span></li>`).join('');
  return `<div class="kpis">${kpi('users', us.length, 'Usuários', `+${novos} nos últimos 30 dias`)}${kpi('trofeu', cs.length, 'Campeonatos', `${ab.length} abertos · ${en.length} encerrados`, 'por')}${kpi('bola', jog.length, 'Jogadores', `${jogEm} em dupla`, 'aq')}${kpi('quadra', don.length, 'Donos de quadra', plural(qs.length, 'quadra cadastrada', 'quadras cadastradas'), 'sol')}${kpi('prof', prof.length, 'Professores', `média de ${R$(media)} por aula`, 'mar')}</div>
    <div class="minis">${mini(dAt.length, 'duplas ativas')}${mini(D.ativas.length, 'inscrições ativas')}${mini(ps.length, 'partidas registradas')}${mini(moeda(premioAb), 'em premiação aberta')}${mini(pend, 'solicitações pendentes')}${mini(bloq.length, bloq.length === 1 ? 'conta bloqueada' : 'contas bloqueadas')}</div>
    <div class="agrid c2">${acard('Novos cadastros por mês', 'Últimos seis meses, por tipo de conta.', gBarras(meses) + '<p class="lg"><span><i class="j"></i>Jogadores</span><span><i class="d"></i>Donos de quadra</span><span><i class="p"></i>Professores</span></p>')}
      ${acard('Usuários por tipo', 'Distribuição de todas as contas.', `<div class="rw">${gRosca(tipos, us.length)}<ul class="lgl">${tipos.map(([r, n, k]) => `<li><i class="${k}"></i><span>${r}</span><b>${n}</b><span class="mut">${us.length ? Math.round(100 * n / us.length) : 0}%</span></li>`).join('')}</ul></div>`)}</div>
    <div class="agrid e2">${acard('Ocupação dos campeonatos abertos', 'Duplas inscritas em relação ao limite de vagas.', ocup || UI.empty('Nenhum campeonato aberto.'))}
      ${acard('Alertas e pendências', 'O que merece a sua atenção agora.', alertas.length ? `<ul class="al">${alertas.map(([, t, aba, tipo, st]) => `<li><span>${t}</span>${aba ? `<button class="btn sm ghost" data-act="admIr" data-aba="${aba}" data-tipo="${tipo}" data-st="${st}">Ver</button>` : ''}</li>`).join('')}</ul>` : '<p>Tudo em ordem por aqui.</p>')}</div>
    <div class="agrid e2">${acard('Cadastros recentes', '', `<ul class="rc">${recentes}</ul>`)}
      ${acard('Ranking das duplas', 'Cinco melhores aproveitamentos nas partidas registradas.', UI.table(['#', 'Dupla', 'Jogos', 'Vitórias', '%'], rank.map((x, i) => [i + 1, esc(x.nome), x.jogos, x.v, x.ap + '%']), 'Ainda não há partidas registradas.'))}</div>
    <div class="agrid e2">${acard('Jogadores por nível', `${jog.length} jogadores cadastrados.`, hbars(niv))}
      ${acard('Registro de ações do administrador', 'As mudanças mais recentes feitas neste painel.', acoes ? `<ul class="lo">${acoes}</ul>` : '<p class="mut">Nenhuma ação registrada ainda.</p>')}</div>`;
}

const stC = (D, c) => c.status !== 'aberto' ? 'encerrado' : D.insc(c.id) >= c.limite ? 'lotado' : 'aberto';
function admFiltrarUsuarios(D, q) {
  return D.us.filter(u => (!A.tipo || TP(u) === A.tipo) && (!A.st || (A.st === 'bloqueado') === !!u.bloqueado) && (!q || [u.nome, u.email, u.telefone, u.local].some(x => norm(x).includes(q))))
    .sort((a, b) => quando(b).localeCompare(quando(a)));
}
function admBarra() {
  const sel = (id, k, op, rot) => `<select id="${id}" data-filtro="${k}" aria-label="${rot}">${op.map(([v, t]) => `<option value="${v}" ${A[k] === v ? 'selected' : ''}>${t}</option>`).join('')}</select>`;
  const busca = ph => `<div class="busca"><input id="admBusca" type="search" data-busca placeholder="${ph}" aria-label="${ph}" value="${esc(A.q)}" autocomplete="off"></div>`;
  if (A.aba === 'usuarios') return `<div class="tb">${busca('Buscar por nome, e-mail, telefone ou cidade')}${sel('admTipo', 'tipo', [['', 'Todos os tipos'], ['jogador', 'Jogadores'], ['dono', 'Donos de quadra'], ['professor', 'Professores'], ['admin', 'Administradores']], 'Filtrar por tipo')}${sel('admStatus', 'st', [['', 'Todos os status'], ['ativo', 'Ativos'], ['bloqueado', 'Bloqueados']], 'Filtrar por status')}<button class="btn sm ghost" data-act="admCsv">Copiar lista (CSV)</button></div>`;
  if (A.aba === 'campeonatos') return `<div class="tb">${busca('Buscar por nome, local ou organizador')}${sel('admStatus', 'st', [['', 'Todos os status'], ['aberto', 'Abertos'], ['lotado', 'Lotados'], ['encerrado', 'Encerrados']], 'Filtrar por status')}</div>`;
  return `<div class="tb">${busca('Buscar por nome, cidade ou responsável')}</div>`;
}
async function admLista() {
  exigeAdm(); const D = await admDados(), q = norm(A.q), nome = id => D.us.find(u => u.id === id)?.nome;
  if (A.aba === 'usuarios') {
    const l = admFiltrarUsuarios(D, q), pgs = Math.max(1, Math.ceil(l.length / PAG)); A.pg = Math.min(Math.max(1, A.pg), pgs);
    const duplaDe = id => D.ds.find(d => d.ativa && (d.j1 === id || d.j2 === id));
    const det = u => { const t = TP(u); return t === 'jogador' ? `${esc(u.nivel || '—')}${duplaDe(u.id) ? ' · dupla ' + esc(duplaDe(u.id).nome) : ' · sem dupla'}` : t === 'dono' ? plural(D.qs.filter(x => x.dono === u.id).length, 'quadra', 'quadras') : t === 'professor' ? `${esc(u.local || '—')} · ${R$(u.valor)}` : 'Acesso total'; };
    const lin = l.slice((A.pg - 1) * PAG, A.pg * PAG).map(u => [`<div class="who">${av(u)}<div><strong>${esc(u.nome)}</strong><br><span class="mut">${esc(u.email)}</span></div></div>`, UI.badge(ROT[TP(u)], TP(u) === 'admin' ? 'ok' : ''), `<span class="mut">${det(u)}</span>`, esc(u.telefone || '—'), dataBr(quando(u)), u.bloqueado ? UI.badge('Bloqueado', 'err') : UI.badge('Ativo', 'ok'),
      `<div class="ac"><button class="btn sm ghost" data-act="admVer" data-id="${u.id}">Ver</button>${u.adm ? '' : `<button class="btn sm ghost" data-act="admBloq" data-id="${u.id}">${u.bloqueado ? 'Desbloquear' : 'Bloquear'}</button><button class="btn sm danger" data-act="admExcluir" data-id="${u.id}">Excluir</button>`}</div>`]);
    return `<p class="mut cont">${plural(l.length, 'usuário encontrado', 'usuários encontrados')} de ${D.us.length}</p>` + UI.table(['Usuário', 'Tipo', 'Detalhes', 'Telefone', 'Cadastro', 'Status', 'Ações'], lin, 'Nenhum usuário encontrado com esses filtros.')
      + `<div class="pg"><button class="btn sm ghost" data-act="admPg" data-d="-1" ${A.pg <= 1 ? 'disabled' : ''}>Anterior</button><span>Página ${A.pg} de ${pgs}</span><button class="btn sm ghost" data-act="admPg" data-d="1" ${A.pg >= pgs ? 'disabled' : ''}>Próxima</button></div>`;
  }
  if (A.aba === 'campeonatos') {
    const l = D.cs.filter(c => (!A.st || stC(D, c) === A.st) && (!q || [c.nome, c.local, nome(c.dono)].some(x => norm(x).includes(q)))).sort((a, b) => (b.inicio || '').localeCompare(a.inicio || ''));
    const lin = l.map(c => [`<strong>${esc(c.nome)}</strong><br><span class="mut">${esc(c.local)}</span>`, esc(nome(c.dono) || '—'), UI.badge(c.nivel) + ' ' + bGen(c), fmt(c.inicio), `${D.insc(c.id)}/${c.limite}`, c.premio > 0 ? moeda(c.premio) : '—',
      { aberto: UI.badge('Aberto', 'ok'), lotado: UI.badge('Lotado', 'err'), encerrado: UI.badge('Encerrado') }[stC(D, c)],
      `<div class="ac"><button class="btn sm ghost" data-act="verC" data-id="${c.id}">Ver</button><button class="btn sm ghost" data-act="admStatusC" data-id="${c.id}">${c.status === 'aberto' ? 'Encerrar' : 'Reabrir'}</button><button class="btn sm danger" data-act="admExcluirC" data-id="${c.id}">Excluir</button></div>`]);
    return `<p class="mut cont">${plural(l.length, 'campeonato', 'campeonatos')} · premiação somada ${moeda(l.reduce((s, c) => s + (+c.premio || 0), 0))}</p>` + UI.table(['Campeonato', 'Organizador', 'Categoria', 'Início', 'Duplas', 'Premiação', 'Status', 'Ações'], lin, 'Nenhum campeonato encontrado.');
  }
  const modos = Object.fromEntries(MODOS);
  const lq = D.qs.filter(x => !q || [x.nome, x.local, nome(x.dono)].some(v => norm(v).includes(q))), lp = D.prof.filter(p => !q || [p.nome, p.local].some(v => norm(v).includes(q)));
  return `<h3 class="sec">${ic('quadra')}Quadras <span class="cnt">${lq.length}</span></h3>` + UI.table(['Foto', 'Quadra', 'Local', 'Uso', 'Preço', 'Responsável', 'Ações'], lq.map(x => [x.foto ? `<img class="th" src="${esc(x.foto)}" alt="">` : '—', `<strong>${esc(x.nome)}</strong>`, esc(x.local), esc(modos[x.modo] || '—'), x.preco ? R$(x.preco) + '/h' : '—', esc(nome(x.dono) || '—'), `<div class="ac"><button class="btn sm ghost" data-act="admVer" data-id="${x.dono}">Ver dono</button><button class="btn sm danger" data-act="admRemoverQ" data-id="${x.id}">Remover</button></div>`]), 'Nenhuma quadra encontrada.')
    + `<h3 class="sec">${ic('prof')}Professores <span class="cnt">${lp.length}</span></h3>` + UI.table(['Professor', 'Onde dá aula', 'Valor da aula', 'WhatsApp', 'Cadastro', 'Ações'], lp.map(p => [`<div class="who">${av(p)}<strong>${esc(p.nome)}</strong></div>`, esc(p.local || '—'), R$(p.valor), esc(p.telefone || '—'), dataBr(quando(p)), `<div class="ac"><button class="btn sm ghost" data-act="admVer" data-id="${p.id}">Ver</button></div>`]), 'Nenhum professor encontrado.');
}
async function admRefresh() { const b = $('#admLista'); if (b) b.innerHTML = await admLista(); }

function admImagens(D) {
  const site = D.cf?.find(x => x.id === 'site') || {}, th = v => v ? `<img class="th" src="${esc(v)}" alt="">` : '—';
  const ac = (col, id, f, w, h) => `<label class="btn sm ghost">Trocar<input type="file" accept="image/*" hidden data-img data-col="${col}" data-id="${id}" data-field="${f}" data-w="${w}" data-h="${h}"></label> <button class="btn sm danger" data-act="rmImg" data-col="${col}" data-id="${id}" data-field="${f}">Remover</button>`;
  const tb = (rows, vazio) => UI.table(['Imagem', 'Item', 'Ação'], rows, vazio);
  return `<p class="mut">Substitua as imagens do site. Ao remover, volta a ilustração padrão.</p><h3>Banner da página inicial</h3>${tb([[th(site.hero), 'Imagem de destaque', ac('config', 'site', 'hero', 1400, 560)]])}
    <details><summary>Campeonatos (${D.cs.length})</summary>${tb(D.cs.map(c => [th(c.foto), esc(c.nome), ac('campeonatos', c.id, 'foto', 800, 450)]), 'Nenhum campeonato.')}</details>
    <details><summary>Quadras (${D.qs.length})</summary>${tb(D.qs.map(q => [th(q.foto), esc(q.nome), ac('quadras', q.id, 'foto', 800, 450)]), 'Nenhuma quadra.')}</details>
    <details><summary>Fotos de perfil (${D.us.length})</summary>${tb(D.us.map(u => [th(u.foto), esc(u.nome), ac('usuarios', u.id, 'foto', 200, 200)]), 'Nenhum usuário.')}</details>`;
}

async function admVerUsuario(id) {
  exigeAdm(); const D = await admDados(), u = D.us.find(x => x.id === id); if (!u) throw Error('Usuário não encontrado.');
  const t = TP(u), dp = D.ds.find(d => d.ativa && (d.j1 === id || d.j2 === id)), par = dp && D.us.find(x => x.id === (dp.j1 === id ? dp.j2 : dp.j1));
  const nIns = dp ? D.ativas.filter(i => i.dupla === dp.id).length : 0, jogos = dp ? D.ps.filter(p => p.a === dp.id || p.b === dp.id).length : 0, mq = D.qs.filter(q => q.dono === id).length, mc = D.cs.filter(c => c.dono === id).length;
  const info = [['E-mail', esc(u.email)], ['WhatsApp', esc(u.telefone || '—')], ['Sexo', u.sexo ? (u.sexo === 'feminino' ? 'Feminino' : 'Masculino') : '—'], ['Nascimento', fmt(u.nasc)], ['Cadastro', dataBr(quando(u))], ['Aceite dos termos', dataBr(u.aceite)],
    ...(t === 'jogador' ? [['Nível', esc(u.nivel || '—')], ['Dupla', dp ? esc(dp.nome) + (par ? ` (com ${esc(par.nome.split(' ')[0])})` : '') : 'Sem dupla'], ['Inscrições ativas', nIns], ['Partidas da dupla', jogos]]
      : t === 'dono' ? [['Quadras', mq], ['Campeonatos criados', mc]] : t === 'professor' ? [['Onde dá aula', esc(u.local || '—')], ['Valor da aula', R$(u.valor)]] : [['Acesso', 'Administração total']])];
  const d = UI.modal(`<div class="who">${av(u, 'big')}<div><h2>${esc(u.nome)}</h2><p style="margin:6px 0 0">${UI.badge(ROT[t], t === 'admin' ? 'ok' : '')} ${u.bloqueado ? UI.badge('Bloqueado', 'err') : UI.badge('Ativo', 'ok')}</p></div></div>
    ${u.bloqueado && u.motivo ? `<p class="mut">Motivo do bloqueio: ${esc(u.motivo)}</p>` : ''}<dl class="info">${info.map(([a, b]) => `<div><dt>${a}</dt><dd>${b}</dd></div>`).join('')}</dl>
    <div class="row l" style="margin-top:14px">${u.adm ? '' : `<button class="btn sm ghost" data-act="admBloq" data-id="${id}">${u.bloqueado ? 'Desbloquear conta' : 'Bloquear conta'}</button>`}${u.id === 'admin' || u.id === Auth.cur()?.id ? '' : `<button class="btn sm ghost" data-act="admAdm" data-id="${id}">${u.adm ? 'Remover acesso de admin' : 'Tornar administrador'}</button>`}${u.adm ? '' : `<button class="btn sm danger" data-act="admExcluir" data-id="${id}">Excluir conta</button>`}<button class="btn sm ghost" data-act="fechar">Fechar</button></div>`);
  d.classList.add('det');
}

const Views = {
  async campeonatos() {
    const me = Auth.cur(), [ds, is, cf] = await lista('duplas', 'inscricoes', 'config'), cfg = cf.find(x => x.id === 'site') || {}, eu = me && await Api.get('usuarios', me.id), souDono = eu?.tipo === 'dono', cs = await sp_campeonatos(F.cat);
    const minha = me && ds.find(d => d.ativa && (d.j1 === me.id || d.j2 === me.id));
    const card = (c, i) => {
      const dono = me && c.dono === me.id, insc = minha && is.find(x => x.camp === c.id && x.dupla === minha.id && x.ativa);
      const meu = dono ? `<button class="btn sm ghost" data-act="editarC" data-id="${c.id}">Editar</button><button class="btn sm ghost" data-act="partida" data-id="${c.id}">Registrar partida</button>` : '';
      return `<article class="cc" data-open="${c.id}"><div class="art">${c.foto ? `<img src="${esc(c.foto)}" alt="" style="width:100%;height:100%;object-fit:cover;display:block">` : arte(...TONS[i % 3])}<span class="tag">${esc(c.local)}</span><span class="prem">${ic('trofeu')}${c.premio > 0 ? moeda(c.premio) : 'Premiação a definir'}</span></div><div class="body"><h3>${esc(c.nome)}</h3><p>${UI.badge(c.nivel)} ${bGen(c)} ${sit(c)}<br>Início em ${fmt(c.inicio)}${c.hora ? ' às ' + esc(c.hora) : ''} · ${c.limite - c.vagas}/${c.limite} duplas${dono ? ' · criado por você' : ''}</p><div class="row l"><button class="btn sm ghost" data-act="verC" data-id="${c.id}">Ver detalhes</button>${btnInsc(c, insc, souDono)}${meu}</div></div></article>`;
    };
    return (await bannerSol(me)) + `<section class="hero">${cfg.hero ? `<img src="${esc(cfg.hero)}" alt="">` : arte('#F7B267', '#F6DCA0')}<div class="in"><span class="etq">Da areia para o seu próximo desafio</span><h1>SOL, AREIA E BOLA NO ALTO.</h1><p>Encontre seu campeonato, reúna sua dupla e leve seu jogo para a praia.</p><button class="btn" data-act="explorar">Explorar campeonatos ${ic('seta')}</button></div></section>
    <section id="lista"><div class="sh"><div><h2>SEU PRÓXIMO CAMPEONATO</h2><p>Escolha a praia. A gente cuida do encontro.</p></div><span>Temporada 2026</span></div>
    <div class="fl"><div class="chips" role="group" aria-label="Filtrar por categoria">${['', ...NIVEIS].map(n => `<button class="chip" aria-pressed="${F.cat === n}" data-act="filtro" data-n="${n}">${n ? n[0].toUpperCase() + n.slice(1) : 'Todos'}</button>`).join('')}</div><div class="row"><span>${cs.length} campeonato${cs.length === 1 ? '' : 's'}</span><button class="btn sm" data-act="novoC">+ Criar campeonato</button></div></div>
    ${cs.length ? `<div class="cards">${cs.map(card).join('')}</div>` : UI.empty('Nenhum campeonato nesta categoria. Que tal criar o primeiro?')}</section>`;
  },
  async cadastro() {
    const me = Auth.cur(), ed = !!(me && F.edit), u = ed ? await Api.get('usuarios', me.id) : null, t = u?.tipo || F.tipo || 'jogador', hs = (u?.hab || '').split(','); F.edit = false;
    const sec = (k, h) => `<div data-for="${k}" ${k === t ? '' : 'hidden'}>${h}</div>`;
    const termo = (x, n) => `<button type="button" class="link" data-act="termo" data-t="${n}">${x}</button>`;
    return `<div class="head"><h2>${u ? 'MEU PERFIL' : 'CADASTRO'}</h2>${me ? '' : '<p>Crie sua conta para entrar no modo demonstração do FTV World.</p>'}</div>${me && !u ? `<p>Você está na conta de <strong>${esc(me.nome)}</strong>. Criar uma nova conta troca para ela. <button type="button" class="link" data-act="perfil">Editar meu perfil</button></p>` : ''}<form id="cadForm" class="card" novalidate ${u ? 'data-edit="1"' : ''}>
    ${u ? '' : `<div class="chips" role="group" aria-label="Tipo de conta" style="margin-bottom:16px">${TIPOS.map(([k, l]) => `<button type="button" class="chip" aria-pressed="${k === t}" data-act="tipo" data-t="${k}">${ic(IK[k])}${l}</button>`).join('')}</div>`}
    <input type="hidden" name="tipo" value="${t}"><input type="hidden" name="foto" id="fotoVal" value="${esc(u?.foto)}">
    <div class="who ft">${av(u, 'big')}<div class="row l"><label class="btn sm ghost">${ic('galeria')}Adicionar foto<input type="file" accept="image/*" data-foto hidden></label><label class="btn sm ghost">${ic('camera')}Tirar foto<input type="file" accept="image/*" capture="user" data-foto hidden></label></div></div>
    ${[{ n: 'nome', l: 'Nome completo', v: u?.nome }, { n: 'email', l: u ? 'E-mail (não pode ser alterado)' : 'E-mail', t: 'email', v: u?.email, ...(u ? { x: 'readonly' } : {}) }, { n: 'senha', l: u ? 'Nova senha (vazio mantém a atual)' : 'Senha (mínimo 6 caracteres)', t: 'password', r: u ? 0 : 1 }, ...(u ? [{ n: 'senha_atual', l: 'Senha atual (só para trocar a senha)', t: 'password', r: 0 }] : []), { n: 'telefone', l: 'WhatsApp com DDD', t: 'tel', v: u?.telefone }, { n: 'nasc', l: 'Data de nascimento', t: 'date', v: u?.nasc, r: 0 }, { n: 'sexo', l: 'Sexo (aparece no seu perfil)', t: 'select', o: SEXOS, v: u?.sexo }].map(UI.field).join('')}
    ${sec('jogador', UI.field({ n: 'nivel', l: 'Nível', t: 'select', o: NIVEIS, v: u?.nivel, r: 0 }) + UI.field({ n: 'perna', l: 'Perna dominante', t: 'select', o: [['direita', 'Direita'], ['esquerda', 'Esquerda'], ['ambas', 'Ambidestro']], v: u?.perna, r: 0 }) + `<fieldset class="fld"><legend><strong>Habilidades</strong></legend><div class="chips">${HABS.map(h => `<label class="chip"><input type="checkbox" name="hab" value="${h}" ${hs.includes(h) ? 'checked' : ''}>${h}</label>`).join('')}</div></fieldset>` + UI.field({ n: 'bio', l: 'Sobre mim (aparece no seu perfil público)', t: 'textarea', r: 0, v: u?.bio, x: 'maxlength="500"' }) + videoField(u))}
    ${sec('dono', u ? '<p>Cadastre e gerencie suas quadras em “Quadras e aulas”.</p>' : '<h3>Sua primeira quadra</h3>' + [{ n: 'qnome', l: 'Nome da quadra' }, { n: 'qlocal', l: 'Localização (endereço ou praia)' }, { n: 'qmodo', l: 'Uso da quadra', t: 'select', o: MODOS, r: 0 }, { n: 'qpreco', l: 'Preço do aluguel por hora (R$)', t: 'number', r: 0, x: 'min="0" step="0.01"' }, { n: 'qdesc', l: 'Descrição da quadra (opcional)', t: 'textarea', r: 0 }].map(UI.field).join(''))}
    ${sec('professor', [{ n: 'local', l: 'Onde você dá aula (praia, arena, cidade)', v: u?.local }, { n: 'valor', l: 'Valor da aula (R$)', t: 'number', v: u?.valor, x: 'min="0" step="0.01"' }].map(UI.field).join(''))}
    ${u ? '' : UI.field({ n: 'uso', t: 'check', l: `Obrigatório: li e aceito o ${termo('Termo de Uso', 'Termo de Uso')} e o ${termo('Termo de Consentimento (LGPD)', 'Termo de Consentimento (LGPD)')}` })}
    <p class="msg" role="alert"></p><button class="btn" ${u ? '' : 'disabled'}>${u ? 'Salvar perfil' : 'Criar conta'}</button></form>${me ? '' : '<p class="center mut">Já tem conta? <button type="button" class="link" data-act="demo">Entrar</button></p>'}`;
  },
  async quadras() {
    const me = Auth.cur(), [us, qs] = await lista('usuarios', 'quadras'), u = id => us.find(x => x.id === id), modos = Object.fromEntries(MODOS);
    const dono = me && u(me.id)?.tipo === 'dono', profs = us.filter(x => x.tipo === 'professor');
    const qc = (q, i) => { const d = u(q.dono), meu = me && q.dono === me.id;
      return `<article class="cc qd"><div class="art">${q.foto ? `<img src="${esc(q.foto)}" alt="Foto de ${esc(q.nome)}" data-act="ampliar" title="Clique para ampliar">` : arte(...TONS[i % 3])}<span class="tag">${ic('quadra')}${esc(modos[q.modo])}</span>${q.preco ? `<span class="prem">${R$(q.preco)}/hora</span>` : ''}</div>
        <div class="body"><h3>${esc(q.nome)}</h3><p class="loc">${mapa(q.local)}</p>${q.desc ? `<p class="desc">${esc(q.desc)}</p>` : ''}<p class="resp">Responsável: <strong>${esc(d?.nome)}</strong></p>
        <div class="row l">${meu ? '' : zap(d?.telefone, `Olá! Vi a quadra "${q.nome}" no FTV World e quero saber mais.`)}${meu ? `<button class="btn sm ghost" data-act="editarQ" data-id="${q.id}">${q.foto ? 'Editar' : 'Editar e adicionar foto'}</button><button class="btn sm danger" data-act="removerQ" data-id="${q.id}">Remover</button>` : ''}</div></div></article>`; };
    const pc = p => `<article class="cc pf"><div class="body"><div class="who">${av(p, 'big')}<div><h3>${esc(p.nome)}</h3>${bSexo(p)}${p.local ? `<p class="loc">${mapa(p.local)}</p>` : ''}</div></div><p class="price">${R$(p.valor)} <small>por aula</small></p>${zap(p.telefone, `Olá, ${p.nome}! Vi seu perfil no FTV World e quero agendar uma aula de futevôlei.`, 'Agendar aula pelo WhatsApp')}</div></article>`;
    const sec = (ico, t, n) => `<h3 class="sec">${ic(ico)}${t} <span class="cnt">${n}</span></h3>`;
    return `<div class="sh"><div><h2>QUADRAS E AULAS</h2><p>Veja a foto e os detalhes de cada quadra e encontre professores para evoluir seu jogo.</p></div>${dono ? '<button class="btn sm" data-act="novaQuadra">+ Cadastrar quadra</button>' : ''}</div>`
      + sec('quadra', 'Quadras', qs.length) + (qs.length ? `<div class="cards">${qs.map(qc).join('')}</div>` : UI.empty('Nenhuma quadra cadastrada ainda.'))
      + sec('prof', 'Professores', profs.length) + (profs.length ? `<div class="cards">${profs.map(pc).join('')}</div>` : UI.empty('Nenhum professor cadastrado ainda.'));
  },
  async 'encontre-dupla'() {
    const me = Auth.cur(), [us, ds, cs, ss] = await lista('usuarios', 'duplas', 'candidatos', 'solicitacoes');
    const livre = id => !ds.some(d => d.ativa && (d.j1 === id || d.j2 === id));
    const ativos = cs.filter(c => livre(c.user) && us.some(u => u.id === c.user)), mine = me && cs.find(c => c.user === me.id);
    const pend = ss.filter(s => s.status === 'pendente' && livre(s.de) && livre(s.para));
    const rec = me ? pend.filter(s => s.para === me.id) : [], env = me ? pend.filter(s => s.de === me.id) : [];
    const card = c => { const u = us.find(x => x.id === c.user);
      return `<article class="card" data-perfil="${u.id}"><div class="who">${av(u, 'big')}<div><h3>${esc(u.nome)}</h3>${bSexo(u)} ${UI.badge(u.nivel || 'iniciante')} ${u.perna ? UI.badge('Perna ' + u.perna) : ''}</div></div><p>${(u.hab || '').split(',').filter(Boolean).map(h => UI.badge(h)).join(' ')}</p>${c.msg ? `<p>“${esc(c.msg)}”</p>` : ''}<div class="row l"><button class="btn sm ghost" data-act="verPerfil" data-id="${u.id}">Ver perfil</button>${me && c.user === me.id ? '<button class="btn sm danger" data-act="removerCand">Remover minha candidatura</button>' : btnSol(me, u.id, ds, ss)}</div></article>`; };
    const linha = (s, outro, recebida) => { const u = us.find(x => x.id === outro); if (!u) return '';
      return `<article class="card" data-perfil="${u.id}"><div class="who">${av(u, 'big')}<div><h3>${esc(u.nome)}</h3>${UI.badge(u.nivel || 'iniciante')}</div></div><div class="row l" style="margin-top:12px"><button class="btn sm ghost" data-act="verPerfil" data-id="${u.id}">Ver perfil</button>${recebida ? `<button class="btn sm" data-act="aceitarSol" data-id="${s.id}">Aceitar</button><button class="btn sm danger" data-act="recusarSol" data-id="${s.id}">Recusar</button>` : `${UI.badge('Aguardando resposta')}<button class="btn sm ghost" data-act="cancelarSol" data-id="${s.id}">Cancelar</button>`}</div></article>`; };
    const sec = (t, a, f) => a.length ? `<h3 style="margin:22px 0 10px">${t}</h3><div class="cards">${a.map(f).join('')}</div>` : '';
    return `<div class="sh"><div><h2>ENCONTRE SUA DUPLA</h2><p>Candidate-se e envie uma solicitação de dupla. Quando a pessoa aceitar, vocês viram dupla.</p></div>${!me ? '<button class="btn sm" data-act="demo">Entrar para me candidatar</button>' : mine ? '' : '<button class="btn sm" data-act="candidatar">+ Quero encontrar dupla</button>'}</div>`
      + sec('Solicitações recebidas', rec, s => linha(s, s.de, true)) + sec('Solicitações enviadas', env, s => linha(s, s.para, false))
      + `<h3 style="margin:22px 0 10px">Jogadores procurando dupla</h3>` + (ativos.length ? `<div class="cards">${ativos.map(card).join('')}</div>` : UI.empty('Ninguém procurando dupla agora. Seja o primeiro!'));
  },
  async admin() {
    const me = Auth.cur(), eu = me && await Api.get('usuarios', me.id);
    const cab = `<div class="sh"><div><h2>PAINEL DE ADMIN</h2><p>${eu?.adm ? `Olá, ${esc(eu.nome.split(' ')[0])}. Acompanhe a plataforma e gerencie usuários, campeonatos e quadras.` : 'Área restrita.'}</p></div><span>${new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}</span></div>`;
    if (!eu?.adm) return cab + UI.empty('Acesso restrito ao administrador.');
    const D = await admDados();
    const abas = [['geral', 'grafico', 'Visão geral'], ['usuarios', 'users', `Usuários <span class="cnt">${D.us.length}</span>`], ['campeonatos', 'trofeu', `Campeonatos <span class="cnt">${D.cs.length}</span>`], ['quadras', 'quadra', 'Quadras e professores'], ['imagens', 'galeria', 'Imagens do site']];
    if (!abas.some(a => a[0] === A.aba)) A.aba = 'geral';
    const corpo = A.aba === 'geral' ? await admGeral(D) : A.aba === 'imagens' ? admImagens(D) : admBarra() + `<div id="admLista">${await admLista()}</div>`;
    return cab + `<div class="atabs" role="group" aria-label="Seções do painel">${abas.map(([k, i, t]) => `<button class="chip" aria-pressed="${A.aba === k}" data-act="admAba" data-aba="${k}">${ic(i)}${t}</button>`).join('')}</div><div class="adm">${corpo}</div>`;
  },
  async ranking() {
    const r = await sp_rankingDuplas();
    return `<div class="head"><h2>RANKING DE DUPLAS</h2></div>` + UI.table(['Pos.', 'Dupla', 'Jogos', 'Vitórias', 'Aproveit.'], r.map((x, i) => [i + 1, esc(x.nome), x.jogos, x.v, x.ap + '%']), 'Ainda não há partidas registradas.');
  },
  async 'minha-dupla'() {   // rota protegida: exige login
    const me = Auth.cur(), cab = '<div class="head"><h2>MINHA DUPLA</h2></div>';
    if (!me) return cab + UI.empty('Ative o modo demonstração para formar dupla e se inscrever em campeonatos.') + '<p class="center"><button class="btn" data-act="demo">Entrar</button></p>';
    const [us, ds, is, cs, ss] = await lista('usuarios', 'duplas', 'inscricoes', 'campeonatos', 'solicitacoes'), eu = us.find(u => u.id === me.id);
    if (eu.tipo === 'dono') return '<div class="head"><h2>MINHA QUADRA</h2></div>' + await painelDono(eu);
    const d = ds.find(x => x.ativa && (x.j1 === me.id || x.j2 === me.id)), minhas = d ? is.filter(i => i.dupla === d.id && i.ativa) : [], jogos = await sp_historicoPartidasUsuario(me.id);
    const par = d && us.find(u => u.id === (d.j1 === me.id ? d.j2 : d.j1)), vit = jogos.filter(x => x.res === 'V').length, ap = jogos.length ? Math.round(100 * vit / jogos.length) : 0;
    const nrec = ss.filter(s => s.status === 'pendente' && s.para === me.id).length;
    const jog = (u, voce) => `<div class="jg"><button type="button" class="avb" data-act="verPerfil" data-id="${u.id}" aria-label="Ver perfil de ${esc(u.nome)}">${av(u, 'big')}</button><div><button type="button" class="link jn" data-act="verPerfil" data-id="${u.id}">${esc(u.nome)}</button>${voce ? ' <span class="mut2">(você)</span>' : ''}<br>${bSexo(u)} ${UI.badge(u.nivel || 'iniciante')} ${u.perna ? UI.badge('Perna ' + u.perna) : ''}</div></div>`;
    const hero = d && par
      ? `<section class="dupla"><span class="etq2">Sua dupla</span><h3>${esc(d.nome)}</h3><div class="jgs">${jog(eu, true)}<span class="vs" aria-hidden="true">&amp;</span>${jog(par)}</div>
          <div class="stats"><div><b>${jogos.length}</b><span>jogos</span></div><div><b>${vit}</b><span>vitórias</span></div><div><b>${ap}%</b><span>aproveitamento</span></div><div><b>${minhas.length}</b><span>inscrições</span></div></div>
          <div class="row l"><button class="btn sm" data-act="verPerfil" data-id="${par.id}">Ver perfil de ${esc(par.nome.split(' ')[0])}</button><button class="btn sm ghost" data-act="desfazer" data-id="${d.id}">Desfazer dupla</button></div></section>`
      : `<section class="dupla vazio">${ic('bola')}<h3>Você ainda não tem dupla</h3><p>Veja quem está procurando parceiro, confira o perfil e envie uma solicitação. Quando a pessoa aceitar, vocês viram dupla.</p>${nrec ? `<p><strong>${nrec}</strong> ${nrec === 1 ? 'solicitação esperando' : 'solicitações esperando'} sua resposta.</p>` : ''}<button class="btn" data-act="formarDupla">Encontrar dupla</button></section>`;
    return cab + hero + `<article class="card meu"><div class="who">${av(eu, 'big')}<div><h3>${esc(eu.nome)}</h3><p class="mut" style="margin:4px 0 8px">${esc(eu.email)} · ${esc(eu.telefone)}</p>${UI.badge(Object.fromEntries(TIPOS)[eu.tipo || 'jogador'])} ${eu.nivel ? UI.badge(eu.nivel) : ''} ${bSexo(eu)} ${eu.perna ? UI.badge('Perna ' + eu.perna) : ''}<p style="margin:8px 0 0">${(eu.hab || '').split(',').filter(Boolean).map(h => UI.badge(h)).join(' ')}</p></div></div><div class="row l" style="margin-top:14px"><button class="btn sm ghost" data-act="perfil">Editar perfil</button><button class="btn sm ghost" data-act="verPerfil" data-id="${eu.id}">Ver como os outros veem</button></div></article>
      <h3 style="margin-top:26px">Minhas inscrições</h3>${UI.table(['Campeonato', 'Data', ''], minhas.map(i => [nm(cs, i.camp), fmt(i.data), `<button class="btn sm danger" data-act="cancelarInsc" data-id="${i.id}">Cancelar</button>`]), 'Nenhuma inscrição ativa. Escolha um campeonato na página inicial.')}
      <h3 style="margin-top:26px">Meus jogos</h3>${UI.table(['Data', 'Adversários', 'Placar', 'Resultado'], jogos.map(x => [fmt(x.data), esc(x.adv), x.placar, UI.badge(x.res, x.res === 'V' ? 'ok' : 'err')]), 'Você ainda não disputou partidas.')}`;
  }
};

/* ===== Ações (delegação de eventos via data-act) ===== */
const minhaDupla = async () => {
  const me = Auth.cur();
  if (!me) { Act.login(); throw Error('Entre na sua conta para continuar.'); }
  const d = await Svc.duplaDe(me.id);
  if (!d) throw Error('Você ainda não tem dupla. Forme uma em "Minha dupla".');
  return d;
};
const Act = {
  fechar: el => el.closest('dialog').close(),
  admAba: el => { exigeAdm(); Object.assign(A, { aba: el.dataset.aba, q: '', tipo: '', st: '', pg: 1 }); Router.render(true); },
  admIr: el => { exigeAdm(); Object.assign(A, { aba: el.dataset.aba, q: '', tipo: el.dataset.tipo || '', st: el.dataset.st || '', pg: 1 }); Router.render(true); scrollTo(0, 0); },
  admPg: el => { exigeAdm(); A.pg += +el.dataset.d; admRefresh(); },
  admVer: async el => { await admVerUsuario(el.dataset.id); },
  admBloq: async el => { const b = await Svc.adminBloquear(el.dataset.id); el.closest('dialog')?.close(); UI.toast(b ? 'Conta bloqueada. A pessoa não consegue mais entrar.' : 'Conta desbloqueada.'); Router.render(true); },
  admAdm: async el => { const v = await Svc.adminToggleAdm(el.dataset.id); el.closest('dialog')?.close(); UI.toast(v ? 'Acesso de administrador concedido.' : 'Acesso de administrador removido.'); Router.render(true); },
  admExcluir: async el => {
    const u = await Api.get('usuarios', el.dataset.id); if (!u) throw Error('Usuário não encontrado.');
    if (!await UI.confirm(`Excluir a conta de <strong>${esc(u.nome)}</strong>? Se a pessoa tiver dupla, quadra ou campeonato vinculados, o servidor não permite a exclusão — nesse caso use <strong>Bloquear</strong>. Esta ação não pode ser desfeita.`)) return;
    await Svc.adminExcluirUsuario(u.id); el.closest('dialog')?.close(); UI.toast('Conta excluída.'); Router.render(true);
  },
  admStatusC: async el => {
    const c = await Api.get('campeonatos', el.dataset.id); exigeAdm(); const st = c.status === 'aberto' ? 'encerrado' : 'aberto';
    await Api.save('campeonatos', { id: c.id, status: st }); await logar(`${st === 'encerrado' ? 'Encerrou' : 'Reabriu'} o campeonato "${c.nome}"`); UI.toast(st === 'encerrado' ? 'Campeonato encerrado.' : 'Campeonato reaberto.'); Router.render(true);
  },
  admExcluirC: async el => {
    const c = await Api.get('campeonatos', el.dataset.id); if (!c) throw Error('Campeonato não encontrado.');
    if (!await UI.confirm(`Excluir o campeonato <strong>${esc(c.nome)}</strong>? Se já houver inscrições ou partidas, o servidor não permite a exclusão — use <strong>Encerrar</strong>. Esta ação não pode ser desfeita.`)) return;
    await Svc.adminExcluirCamp(c.id); UI.toast('Campeonato excluído.'); Router.render(true);
  },
  admRemoverQ: async el => {
    const q = await Api.get('quadras', el.dataset.id); if (!q) throw Error('Quadra não encontrada.'); exigeAdm();
    if (!await UI.confirm(`Remover a quadra <strong>${esc(q.nome)}</strong>?`)) return;
    await Api.remove('quadras', q.id); await logar(`Removeu a quadra "${q.nome}"`); UI.toast('Quadra removida.'); Router.render(true);
  },
  admCsv: async () => {
    exigeAdm(); const D = await admDados(), l = admFiltrarUsuarios(D, norm(A.q)), c = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const txt = [['Nome', 'E-mail', 'Telefone', 'Tipo', 'Nível', 'Cadastro', 'Status'].map(c).join(','), ...l.map(u => [u.nome, u.email, u.telefone, ROT[TP(u)], u.nivel, dataBr(quando(u)), u.bloqueado ? 'Bloqueado' : 'Ativo'].map(c).join(','))].join('\n');
    try { await navigator.clipboard.writeText(txt); UI.toast(`Lista copiada (${plural(l.length, 'usuário', 'usuários')}). Cole em uma planilha.`); } catch { UI.toast('Não foi possível copiar. O navegador bloqueou a área de transferência.', 'err'); }
  },
  tipo: el => { const f = el.closest('form'); f.elements.tipo.value = F.tipo = el.dataset.t; f.querySelectorAll('[data-act=tipo]').forEach(b => b.setAttribute('aria-pressed', b === el)); f.querySelectorAll('[data-for]').forEach(s => s.hidden = s.dataset.for !== el.dataset.t); },
  novaQuadra: () => Forms.quadra(),
  editarQ: async el => Forms.quadra(await Api.get('quadras', el.dataset.id)),
  removerQ: async el => { if (!await UI.confirm('Remover esta quadra?')) return; await Svc.removerQuadra(el.dataset.id); UI.toast('Quadra removida.'); Router.render(true); },
  rmImg: async el => { if (!adm()) throw Error('Apenas o administrador pode remover estas imagens.'); await Api.save(el.dataset.col, { id: el.dataset.id, [el.dataset.field]: '' }); UI.toast('Imagem removida.'); Router.render(true); },
  menu: el => { const p = el.nextElementSibling; p.hidden = !p.hidden; el.setAttribute('aria-expanded', !p.hidden); },
  termo: () => UI.modal(termoHtml()),
  _t: el => UI.modal(`<h2>${esc(el.dataset.t)}</h2><p>Texto de exemplo: ao usar a plataforma você se compromete a jogar com respeito, informar dados verdadeiros e permite que o organizador trate seus dados (nome, contato, nível e resultados) apenas para gerir campeonatos, duplas e rankings, conforme a LGPD. Você pode pedir acesso, correção ou exclusão dos seus dados quando quiser.</p><div class="row"><button class="btn" data-act="fechar" autofocus>Entendi</button></div>`),
  login: () => Act.demo(),
  _l: () => UI.form('Entrar', [{ n: 'email', l: 'E-mail', t: 'email' }, { n: 'senha', l: 'Senha', t: 'password' }],
    async f => { await Auth.login(f.email, f.senha); return `Bem-vindo(a), ${Auth.cur().nome}!`; }, 'Entrar'),
  demo: () => {   // pede login (admin / 123 já preenchidos) ou cadastro
    const d = UI.form('Entrar', [{ n: 'email', l: 'E-mail', x: 'autocapitalize="off" autocomplete="username" spellcheck="false"' }, { n: 'senha', l: 'Senha', t: 'password', x: 'autocomplete="current-password"' }],
      async f => { await Auth.login(f.email, f.senha); location.hash = '#campeonatos'; return `Bem-vindo(a), ${Auth.cur().nome}!`; }, 'Entrar');
    $('form', d).insertAdjacentHTML('beforeend', '<p class="center">Ainda não tem conta? <button type="button" class="link" data-act="irCadastro">Criar conta</button></p>');
  },
  irCadastro: el => { el.closest('dialog').close(); irCad(false); },
  candidatar: async () => {
    const me = Auth.cur(), eu = await Api.get('usuarios', me.id);
    if ((eu.tipo || 'jogador') !== 'jogador') throw Error('Só jogadores podem procurar dupla.');
    if (await Svc.duplaDe(me.id)) throw Error('Você já tem uma dupla ativa.');
    UI.form('Encontre sua dupla', [{ n: 'msg', l: 'Recado para os parceiros (opcional)', r: 0 }], async f => { await Api.save('candidatos', { user: me.id, msg: f.msg.trim() }); return 'Candidatura publicada!'; }, 'Publicar');
  },
  removerCand: async () => { await http('DELETE', '/candidatos/minha'); UI.toast('Candidatura removida.'); Router.render(true); },
  permNao: el => { LS.setItem('fv2_perm', '0'); el.closest('dialog').close(); },
  permSim: async el => {
    LS.setItem('fv2_perm', '1'); el.closest('dialog').close(); const ok = [];
    try { await new Promise((a, b) => navigator.geolocation.getCurrentPosition(a, b)); ok.push('localização'); } catch { }
    try { (await navigator.mediaDevices.getUserMedia({ video: true })).getTracks().forEach(t => t.stop()); ok.push('câmera'); } catch { }
    ok.length ? UI.toast('Permitido: ' + ok.join(' e ') + '.') : UI.toast('Permissões não concedidas. Você pode liberar nas configurações do navegador.', 'err');
  },
  logout: () => { Auth.logout(); UI.toast('Você saiu da conta.'); Router.render(); },
  cadastrar: () => irCad(false),
  perfil: el => { el.closest('dialog')?.close(); irCad(true); },   // só o próprio perfil
  filtro: el => { F.cat = el.dataset.n; Router.render(true); },
  explorar: () => $('#lista')?.scrollIntoView({ behavior: 'smooth' }),
  novoC: async () => {
    const me = Auth.cur(); if (!me) { UI.toast('Entre para criar um campeonato.', 'err'); return Act.login(); }
    if (!await ehDono(me.id)) throw Error('Somente donos de quadra podem criar campeonatos.');
    Forms.camp();
  },
  verC: el => abrirCamp(el.dataset.id),
  verPerfil: el => abrirPerfil(el.dataset.id),
  ampliar: el => UI.modal(`<img class="amp" src="${esc(el.getAttribute('src'))}" alt="${esc(el.alt)}"><div class="row"><button class="btn sm ghost" data-act="fechar" autofocus>Fechar</button></div>`).classList.add('det'),
  enviarSol: async el => { const me = Auth.cur(); if (!me) return Act.login(); await Svc.enviarSolicitacao(me.id, el.dataset.id); el.closest('dialog')?.close(); UI.toast('Solicitação enviada! Agora é só esperar a resposta.'); Router.render(true); },
  cancelarSol: async el => { await Svc.cancelarSolicitacao(el.dataset.id); el.closest('dialog')?.close(); UI.toast('Solicitação cancelada.'); Router.render(true); },
  recusarSol: async el => { await Svc.responderSolicitacao(el.dataset.id, false); el.closest('dialog')?.close(); UI.toast('Solicitação recusada.'); Router.render(true); },
  aceitarSol: async el => { const dp = await Svc.responderSolicitacao(el.dataset.id, true); el.closest('dialog')?.close(); UI.toast(`Dupla formada: ${dp.nome}!`); location.hash === '#minha-dupla' ? Router.render() : (location.hash = '#minha-dupla'); },
  rmVideo: el => { const b = el.closest('.vid'); b.querySelector('input[type=hidden]').value = ''; b.querySelector('input[data-video]').value = ''; b.querySelector('video,.ph').outerHTML = '<span class="ph">Sem vídeo</span>'; },
  editarC: async el => { const c = await Api.get('campeonatos', el.dataset.id); el.closest('dialog')?.close(); Forms.camp(c); },
  partida: el => { el.closest('dialog')?.close(); return Forms.partida(el.dataset.id); },
  formarDupla: () => { UI.toast('Escolha uma pessoa e envie uma solicitação de dupla.'); location.hash = '#encontre-dupla'; },   // dupla só nasce quando a outra pessoa aceita
  desfazer: async el => {
    const n = (await Api.list('inscricoes')).filter(i => i.dupla === el.dataset.id && i.ativa).length;
    if (!await UI.confirm(`Desfazer a dupla?${n ? ` <strong>${n} inscrição(ões) ativa(s) será(ão) cancelada(s).</strong>` : ''}`)) return;
    await Svc.desfazerDupla(el.dataset.id); UI.toast('Dupla desfeita.'); Router.render();
  },
  inscMinha: async el => { const d = await minhaDupla(); await Svc.inscrever({ dupla: d.id, camp: el.dataset.id }); el.closest('dialog')?.close(); UI.toast('Dupla inscrita!'); Router.render(true); },
  cancelarInsc: async el => {
    if (!await UI.confirm('Cancelar esta inscrição?')) return;
    await http('POST', `/inscricoes/${el.dataset.id}/cancelar`, {}); el.closest('dialog')?.close(); UI.toast('Inscrição cancelada.'); Router.render(true);
  }
};

/* ===== Router (hash) ===== */
const Router = {
  async render(quiet) {   // quiet = não mostra "Carregando…" (mantém a rolagem)
    if (Auth.cur() && Token.get()) { try { await Promise.all([Api.list('usuarios'), Api.list('solicitacoes')]); } catch (e) { UI.toast(e.message, 'err'); } }
    else if (Auth.cur()) { SS.removeItem('fv2_sess'); }
    { const c = Auth.cur(), x = c && Storage.get('usuarios').find(u => u.id === c.id); if (c && (!x || x.bloqueado)) { Auth.logout(); UI.toast(x ? 'Sua conta foi bloqueada pelo administrador.' : 'Sua conta não existe mais.', 'err'); } }
    const r = location.hash.slice(1), main = $('#view'), s = Auth.cur(), rota = !s ? 'cadastro' : Object.hasOwn(Views, r) && (r !== 'admin' || adm()) ? r : 'campeonatos';
    document.body.classList.toggle('gate', !s);
    const eu0 = s && Storage.get('usuarios').find(x => x.id === s.id); $('#nav a[href="#minha-dupla"]').textContent = eu0?.tipo === 'dono' ? 'Minha quadra' : 'Minha dupla'; $('#navAdmin').hidden = !eu0?.adm;
    const np = s ? Storage.get('solicitacoes').filter(x => x.status === 'pendente' && x.para === s.id).length : 0;   // solicitações recebidas
    $('#nav a[href="#encontre-dupla"]').innerHTML = 'Encontre sua dupla' + (np ? ` <span class="nb" aria-label="${np} solicitações pendentes">${np}</span>` : '');
    document.querySelectorAll('#nav a').forEach(a => a.getAttribute('href') === '#' + rota ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
    $('#auth').innerHTML = s ? `${menuUser(s)}` : '';
    if (!quiet) main.innerHTML = '<p class="loading" role="status">Carregando…</p>';
    try { main.innerHTML = await Views[rota](); } catch (e) { main.innerHTML = UI.empty('Algo deu errado: ' + esc(e.message)); }
  }
};

/* ===== Dados de exemplo (primeira execução) ===== */

/* ===== Eventos globais e início ===== */
document.addEventListener('click', async e => {
  const el = e.target.closest('[data-act]');
  if (el) try { await Act[el.dataset.act](el); } catch (x) { UI.toast(x.message, 'err'); }
});
document.addEventListener('click', e => { const o = e.target.closest('[data-perfil]'); if (o && !e.target.closest('button,a,input,label')) abrirPerfil(o.dataset.perfil).catch(x => UI.toast(x.message, 'err')); });
document.addEventListener('click', e => { const o = e.target.closest('[data-open]'); if (o && !e.target.closest('button,a,input,label')) abrirCamp(o.dataset.open).catch(x => UI.toast(x.message, 'err')); });
document.addEventListener('click', e => { if (!e.target.closest('.um-btn')) document.querySelectorAll('.um-pop').forEach(p => p.hidden = true); });
document.addEventListener('change', e => {   // foto: recorta em quadrado 200px e guarda como data URL
  const i = e.target; if (i.matches?.('[data-imgf],[data-img]') && i.files[0]) return carregarImg(i);
  if (i.matches?.('[data-video]')) {   // vídeo curto guardado no navegador (demo); limite para caber no armazenamento
    const f = i.files[0]; if (!f) return;
    if (!f.type.startsWith('video/')) { i.value = ''; return UI.toast('Escolha um arquivo de vídeo.', 'err'); }
    if (f.size > 1.5 * 1024 * 1024) { i.value = ''; return UI.toast('Vídeo muito grande (máx. 1,5 MB). Use um vídeo curto ou cole um link.', 'err'); }
    const r = new FileReader(); r.onload = () => { const box = i.closest('.vid'); box.querySelector('input[type=hidden]').value = r.result; box.querySelector('video,.ph').outerHTML = `<video controls playsinline preload="metadata" src="${r.result}"></video>`; };
    r.onerror = () => UI.toast('Não foi possível ler o vídeo.', 'err'); r.readAsDataURL(f); return;
  }
  if (i.name === 'uso') i.form.querySelector('button.btn:not(.ghost)').disabled = !i.checked;
  if (!i.matches?.('[data-foto]') || !i.files[0]) return;
  const r = new FileReader(), img = new Image();
  r.onload = () => { img.src = r.result; };
  img.onload = () => { const c = document.createElement('canvas'), s = Math.min(img.width, img.height); c.width = c.height = 200;
    c.getContext('2d').drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, 200, 200);
    const v = $('#fotoVal').value = c.toDataURL('image/jpeg', .8); $('.ft .av').outerHTML = `<img class="av big" src="${v}" alt="Prévia da foto">`; };
  img.onerror = () => UI.toast('Não foi possível ler a imagem.', 'err');
  r.readAsDataURL(i.files[0]);
});
document.addEventListener('submit', async e => {
  const f = e.target; if (f.id !== 'cadForm') return; e.preventDefault();
  const fd = new FormData(f), d = Object.fromEntries(fd), me = f.dataset.edit ? Auth.cur() : null, t = d.tipo, msg = $('.msg', f);
  d.hab = fd.getAll('hab').join(',');
  if (t !== 'jogador') ['nivel', 'perna', 'hab', 'bio', 'video', 'videoUrl'].forEach(k => delete d[k]);
  if (t !== 'professor') ['local', 'valor'].forEach(k => delete d[k]);
  try {
    if (!d.nome.trim()) throw Error('Informe seu nome.');
    if (!['feminino', 'masculino'].includes(d.sexo)) throw Error('Selecione o sexo: feminino ou masculino.');
    if (!Validators.tel(d.telefone)) throw Error('Informe um WhatsApp válido, com DDD. Ex.: (31) 99999-9999.');
    if (!me && !f.elements.uso.checked) throw Error('É preciso aceitar os termos.');
    if (t === 'professor' && (!d.local.trim() || !(+d.valor > 0))) throw Error('Informe onde você dá aula e o valor da aula.');
    const q = { nome: d.qnome, local: d.qlocal, modo: d.qmodo, preco: d.qpreco, desc: d.qdesc };
    if (t === 'dono' && !me) Svc.valQuadra(q);
    const r = await Svc.salvarUsuario(d, me?.id);
    if (!me) { await Auth.login(d.email, d.senha); if (t === 'dono') await Svc.salvarQuadra(q, r.id); }
    UI.toast(me ? 'Perfil atualizado!' : 'Conta criada! Você já está dentro.'); location.hash = '#campeonatos'; Router.render();
  } catch (x) { msg.textContent = x.name === 'QuotaExceededError' ? 'Sem espaço no navegador para salvar o vídeo. Use um vídeo menor ou cole um link.' : x.message; }
});
document.addEventListener('input', e => { if (e.target.matches?.('[data-busca]')) { A.q = e.target.value; A.pg = 1; admRefresh(); } });
document.addEventListener('change', e => { const s = e.target.closest?.('[data-filtro]'); if (s) { A[s.dataset.filtro] = s.value; A.pg = 1; admRefresh(); } });
$('.burger').addEventListener('click', e => { const o = $('#nav').classList.toggle('open'); e.currentTarget.setAttribute('aria-expanded', o); });
window.addEventListener('hashchange', () => { $('#nav').classList.remove('open'); $('.burger').setAttribute('aria-expanded', 'false'); Router.render(); scrollTo(0, 0); });
Router.render().then(pedirPermissoes);
})();

