# FTV World — Sistema de Gestão de Futevôlei e Vôlei de Praia

Plataforma para organizar campeonatos, formar duplas, inscrever duplas, registrar partidas e acompanhar rankings.
API em **Flask + SQLAlchemy + MySQL** e front-end em HTML/CSS/JavaScript puro (`fetch()` para a API).

## Arquitetura (back-end)

Fluxo: `controllers` → `services` → `models` (CRUD simples) e `repositories` (consultas especiais).

| Camada | Pasta | Responsabilidade |
|---|---|---|
| Controller | `backend/controllers/` | Só recebe a requisição, chama o service e devolve a resposta HTTP. Sem regra de negócio e sem regra de permissão (inclusive a de quem vê o quê num perfil, que está em `VisualizarUsuarioService`). |
| Service | `backend/services/` | Regras de negócio, validações e permissões. Nas operações simples de CRUD chama **diretamente a Model**. |
| Model | `backend/models/` | Entidade + acesso a dados do CRUD: `salvar()`, `listar_todos()`, `buscar_por_id()`, `atualizar()`, `deletar()`. |
| Repository | `backend/repositories/` | **Somente consultas especiais**: filtros, buscas por critério, contagens e chamadas às procedures (`relatorio_repository`). Existem repositories apenas para `usuario`, `dupla`, `inscricao`, `solicitacao`, `notificacao`, `candidato`, `log` e `relatorio`. |

Não existem repositories que apenas repetem o CRUD: `campeonato`, `quadra`, `partida` e `config` usam só a Model (por isso não têm repository).

## Diagrama de classes

O diagrama das 11 entidades (atributos, chaves estrangeiras, métodos reais das Models, composição e agregação; não há herança entre as Models) está em Mermaid em:

- `docs/diagrama_classes.md`

## Funcionalidades

Tudo abaixo existe no código (front-end, controllers, services, models e procedures):

1. **Cadastro de usuário** com aceite obrigatório do Termo de Uso e do Termo de Consentimento (LGPD); a data do aceite é gravada no banco.
2. **Três tipos de conta** (jogador, professor e dono de quadra), cada um com campos próprios: jogador informa nível, perna dominante, sexo e habilidades; professor informa onde dá aula e o valor da aula; dono cadastra a primeira quadra já no cadastro.
3. **Login e logout** com e-mail e senha, senha guardada com hash, token JWT com validade de 8 horas e revogação do token no logout.
4. **Recuperação da sessão** pelo token (`GET /api/eu`), mantendo a pessoa logada ao recarregar a página.
5. **Edição do próprio perfil** (foto, vídeo ou link de vídeo, bio de até 500 caracteres, habilidades, cidade, telefone); e-mail, senha, tipo e permissão de administrador são ignorados nessa rota.
6. **Troca de senha** exigindo a senha atual e uma nova senha com no mínimo 6 caracteres.
7. **Perfil público**: usuários comuns veem só os dados públicos dos outros; o próprio dono do perfil e o administrador veem tudo.
8. **Listagem de campeonatos** com filtro por categoria (iniciante, intermediário, avançado ou livre) e com vagas livres de cada um.
9. **Criação de campeonato** (somente dono de quadra ou administrador): nome, descrição, data, horário, nível, gênero (masculino, feminino ou misto), limite de duplas, cidade, premiação e foto.
10. **Edição, encerramento, reabertura e exclusão de campeonato**, permitidos apenas a quem o criou (ou ao administrador); o limite de duplas não pode ficar abaixo das inscrições ativas.
11. **Cadastro, edição e exclusão de quadras** pelo dono responsável: endereço, cidade, número de quadras, contato, foto, uso (campeonato, aluguel ou ambos) e preço do aluguel por hora (obrigatório quando há aluguel).
12. **Página "Quadras e aulas"** com a lista de quadras e de professores e botão de contato por WhatsApp.
13. **"Encontre sua dupla"**: o jogador publica uma candidatura com recado de até 255 caracteres (publicar de novo só atualiza o recado) e pode remover a própria candidatura.
14. **Solicitação de dupla**: envio para outro jogador, bloqueando envio para si mesmo, para dono de quadra, para quem já tem dupla ativa e solicitações pendentes repetidas.
15. **Resposta às solicitações**: só quem recebeu aceita ou recusa; só quem enviou cancela; a solicitação recebida aparece em destaque na página inicial.
16. **Formação automática da dupla** ao aceitar a solicitação: nome "Primeiro nome & Primeiro nome", categoria pelo nível em comum e cancelamento das demais solicitações pendentes dos dois jogadores.
17. **Regra de uma dupla ativa por jogador** e página "Minha dupla".
18. **Desfazer dupla**: a dupla fica inativa (o histórico é preservado), as inscrições ativas são canceladas e as vagas dos campeonatos são recalculadas.
19. **Inscrição de dupla em campeonato** validando dupla ativa, campeonato aberto, vagas disponíveis, inscrição repetida, nível compatível (campeonato livre aceita todos) e gênero compatível.
20. **Cancelamento de inscrição** pela dupla, pelo dono do campeonato ou pelo administrador, com recálculo automático de `vagas_disponiveis`.
21. **Registro de partidas** pelo criador do campeonato: fase, data e hora, quadra e placar até 18 pontos sem empate; a dupla vencedora é calculada automaticamente; também permite editar e excluir.
22. **Classificação do campeonato** (vitórias por dupla) e **ranking geral das duplas** (jogos, vitórias e aproveitamento).
23. **Histórico de partidas do usuário** (cada um vê o próprio; o administrador vê o de qualquer pessoa).
24. **Relatórios por procedures MySQL**: campeonatos disponíveis, todos os campeonatos, classificação, ranking, inscritos de um campeonato, histórico do usuário, quadras mais utilizadas e resumo do administrador.
25. **Notificações (o sino)**: geradas automaticamente ao enviar, aceitar ou recusar solicitação de dupla e quando uma dupla se inscreve em um campeonato; é possível marcar uma ou todas como lidas.
26. **Painel do administrador** com indicadores, gráficos, ranking e listas de usuários, campeonatos e quadras com busca e filtros.
27. **Bloqueio e desbloqueio de usuários** e exclusão de usuário (as notificações, candidatura e solicitações saem junto; se houver duplas, quadras ou campeonatos vinculados a exclusão é recusada com erro 409).
28. **Cópia da lista de usuários em formato CSV** para colar em uma planilha (painel do administrador).
29. **Log de auditoria** somente leitura (criação de campeonato, quadra, dupla, partida, bloqueios, exclusões e alterações de configuração), visível apenas ao administrador.
30. **Configuração do site** (imagens do banner da página inicial) editável pelo administrador e lida por todos.
31. **Termo de Uso e Termo de Consentimento (LGPD)** consultáveis no rodapé e solicitados na entrada do site, junto com as permissões de localização e câmera.

## Como rodar

1. Instale o Python 3.11+ e o MySQL (XAMPP/phpMyAdmin serve).
2. No phpMyAdmin, rode `backend/database/criar_banco.sql` e depois, dentro do banco `ftvworld`, `backend/database/procedures.sql`.
3. No terminal, dentro da pasta `backend`:
   ```
   python -m venv venv
   venv\Scripts\activate        (Linux/Mac: source venv/bin/activate)
   pip install -r requirements.txt
   python app.py
   ```
   As tabelas são criadas sozinhas. A API sobe em `http://127.0.0.1:5000`.

**Já tinha o banco criado antes do campo "sexo"?** Rode uma vez `backend/database/atualizar_sexo.sql` (a coluna `sexo` guarda `feminino` ou `masculino`).

**Banco que já existia com o back-end antigo?** Rode uma vez `backend/database/atualizar_novas_colunas.sql` (as senhas antigas continuam valendo e são convertidas para hash no primeiro login).

### Variáveis de ambiente (opcionais)

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | Outro banco. Padrão: `mysql+pymysql://root:@localhost/ftvworld` |
| `FTVWORLD_SECRET` | Chave que assina os tokens JWT. Defina uma fixa em produção; sem ela uma chave é criada em `backend/.ftvworld_secret` |
| `ADMIN_EMAIL` e `ADMIN_SENHA` | Criam o administrador na primeira execução (senha com 6+ caracteres) |

### Como rodar o front-end

Com o backend no ar, dentro da pasta `frontend`:
```
python -m http.server 5500
```
e abra `http://127.0.0.1:5500`. O endereço da API fica em `API_CONFIG.baseUrl` no topo do `app.js` (padrão `http://127.0.0.1:5000/api`). O primeiro administrador vem das variáveis `ADMIN_EMAIL` e `ADMIN_SENHA` do backend; o banco começa vazio.

## Login

`POST /api/login` com `{"email", "senha"}` devolve o usuário e um `token`.
Nas demais rotas protegidas envie `Authorization: Bearer <token>`. O token vale 8 horas.

Legenda: 🌐 pública · 🔑 precisa de login · 👑 só administrador

## Rotas

**Conta**
- 🌐 `POST /api/usuarios` cadastro (exige `aceitou_termos`) · 🌐 `POST /api/login` · 🔑 `POST /api/logout` · 🔑 `GET /api/eu`
- 🔑 `PUT /api/meu-perfil` edita o próprio perfil · 🔑 `PUT /api/meu-perfil/senha` com `senha_atual` e `senha_nova`
- 🔑 `GET /api/usuarios` e `/api/usuarios/<id>` (não-admin vê só os dados públicos) · 👑 `PUT`/`DELETE /api/usuarios/<id>` (bloquear = `{"bloqueado": true}`)

**Campeonatos e quadras** (🌐 leitura · 🔑 escrita; só dono de quadra cria e só quem criou edita/exclui)
- `GET|POST /api/campeonatos`, `GET|PUT|DELETE /api/campeonatos/<id>`
- `GET|POST /api/quadras`, `GET|PUT|DELETE /api/quadras/<id>`

**Duplas, solicitações, inscrições e partidas**
- 🔑 `GET /api/solicitacoes` (as suas) · 🔑 `POST /api/solicitacoes` com `{"id_para"}` · 🔑 `POST /api/solicitacoes/<id>/aceitar|recusar|cancelar`
- 🔑 `GET|POST /api/duplas` · 🔑 `POST /api/duplas/<id>/desfazer`
- 🔑 `GET|POST /api/inscricoes` · 🔑 `POST /api/inscricoes/<id>/cancelar`
- `GET|POST /api/partidas` (🌐 leitura; só o criador do campeonato registra)
- 🔑 `GET|POST /api/candidatos` · 🔑 `DELETE /api/candidatos/minha`

**Notificações**
- 🔑 `GET /api/minhas-notificacoes` · 🔑 `PUT /api/minhas-notificacoes/<id>/ler` · 🔑 `PUT /api/minhas-notificacoes/ler-todas`

**Relatórios (procedures)**: a permissão de cada relatório é decidida no `relatorio_service.py`
- 🌐 `GET /api/relatorios/campeonatos-disponiveis?categoria=&nivel=` · 🌐 `/campeonatos?nivel=` · 🌐 `/classificacao-campeonato/<id>` · 🌐 `/ranking-duplas` · 🌐 `/quadras-mais-utilizadas`
- 🔑 `/inscritos-campeonato/<id>` · 🔑 `/historico-usuario/<id>` (só o próprio ou admin) · 🔑 `/resumo-admin` (só admin)

**Admin e site**
- 👑 `GET /api/logs` · 🌐 `GET /api/config` · 👑 `PUT|DELETE /api/config/<chave>` com `{"valor": ...}`
- 👑 CRUD genérico em `/api/notificacoes`, e `PUT`/`DELETE` de duplas, inscrições, solicitações e candidatos.

## Regras de negócio (nos services)

- Dono de quadra não forma dupla; um jogador só tem uma dupla ativa; solicitações pendentes são canceladas quando a dupla nasce.
- Inscrição: dupla ativa, campeonato aberto, vagas disponíveis, sem inscrição repetida, nível e gênero compatíveis.
- `vagas_disponiveis` é recalculado a cada inscrição, cancelamento ou mudança de limite.
- Partida: duplas diferentes e inscritas no campeonato; placar até 18, sem empate; vencedora calculada.
- Relatórios: histórico só do próprio usuário (ou admin) e resumo só para admin, verificados em `relatorio_service.py`.
- Erros voltam como `{"erro": "mensagem"}`: 400 dado inválido, 401 sem login, 403 sem permissão, 404 não achou, 409 não dá para excluir (registros vinculados).

## Estrutura do projeto

```text
├── backend/
│   ├── app.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── controllers/            # recebem a requisição e devolvem a resposta (sem regra de negócio)
│   │   ├── rotas.py            # registra as rotas de todas as controllers
│   │   ├── protecao.py         # decoradores @exigir_login / @exigir_admin
│   │   ├── respostas.py        # resposta de erro padrão
│   │   ├── usuario_controller.py, login_controller.py, perfil_controller.py,
│   │   │   campeonato_controller.py, quadra_controller.py, inscricao_controller.py,
│   │   │   dupla_controller.py, partida_controller.py, solicitacao_controller.py,
│   │   │   candidato_controller.py, notificacao_controller.py, log_controller.py,
│   │   │   config_controller.py, relatorio_controller.py
│   ├── services/               # regras de negócio e permissões (chamam as Models no CRUD simples)
│   │   ├── comum.py            # constantes e funções de apoio (permissões, validações, log)
│   │   ├── sessao.py           # token JWT
│   │   ├── usuario_service.py, auth_service.py, campeonato_service.py, quadra_service.py,
│   │   │   inscricao_service.py, dupla_service.py, partida_service.py, notificacao_service.py,
│   │   │   solicitacao_service.py, candidato_service.py, log_service.py, config_service.py,
│   │   │   relatorio_service.py
│   ├── repositories/           # SOMENTE consultas especiais (filtros, buscas, contagens, procedures)
│   │   ├── usuario_repository.py, dupla_repository.py, inscricao_repository.py,
│   │   │   solicitacao_repository.py, notificacao_repository.py, candidato_repository.py,
│   │   │   log_repository.py
│   │   └── relatorio_repository.py   # chama as procedures do MySQL
│   ├── models/                 # entidades + CRUD (salvar, listar_todos, buscar_por_id, atualizar, deletar)
│   │   ├── db_instance.py
│   │   └── usuario.py, campeonato.py, quadra.py, dupla.py, inscricao.py, partida.py,
│   │       solicitacao.py, notificacao.py, candidato.py, log.py, config.py
│   └── database/               # scripts SQL (criar_banco, procedures, atualizações)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/
│   └── diagrama_classes.md
├── .gitignore
└── README.md
```