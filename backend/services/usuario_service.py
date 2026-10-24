# services do usuario (tem validação extra por causa da LGPD)

import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from models import Usuario
from models.db_instance import agora
from repositories.usuario_repository import UsuarioRepository
from services.comum import (
    REGEX_EMAIL, REGEX_LINK, NIVEIS, TIPOS_USUARIO, PERNAS, SEXOS,
    como_numero, exigir_login, registrar_log,
)

CAMPOS_CADASTRO = {'nome', 'email', 'senha', 'telefone', 'data_nascimento', 'nivel', 'cidade', 'tipo', 'sexo',
                   'perna', 'habilidades', 'local', 'valor', 'bio', 'foto', 'video', 'video_url'}


def validar_perfil(dados):
    # valida (e ajeita) so os campos do perfil que vieram no pedido
    if dados.get('bio') and len(dados['bio']) > 500:
        raise ValueError("a descrição pode ter no máximo 500 caracteres")
    if dados.get('video_url') and not REGEX_LINK.match(dados['video_url']):
        raise ValueError("o link do vídeo precisa começar com http:// ou https://")
    if dados.get('nivel') and dados['nivel'] not in NIVEIS:
        raise ValueError("nível inválido")
    if dados.get('tipo') and dados['tipo'] not in TIPOS_USUARIO:
        raise ValueError("tipo de usuário inválido")
    if dados.get('sexo') and dados['sexo'] not in SEXOS:
        raise ValueError("sexo inválido: escolha feminino ou masculino")
    if dados.get('perna') and dados['perna'] not in PERNAS:
        raise ValueError("perna dominante inválida")
    if dados.get('valor') not in (None, '') and como_numero(dados['valor'], 'valor') < 0:
        raise ValueError("o valor não pode ser negativo")
    if isinstance(dados.get('habilidades'), list):
        dados['habilidades'] = ','.join(str(h).strip() for h in dados['habilidades'] if str(h).strip())
    if dados.get('habilidades') and len(dados['habilidades']) > 255:
        raise ValueError("lista de habilidades muito grande")


def senha_confere(usuario, senha):
    senha = senha or ''
    guardada = usuario.senha or ''
    if guardada.startswith(('scrypt:', 'pbkdf2:')):
        return check_password_hash(guardada, senha)
    # banco antigo: a senha estava salva sem hash. confere e ja converte pra hash
    if hmac.compare_digest(guardada.encode(), senha.encode()):
        Usuario.atualizar(usuario.id, {'senha': generate_password_hash(senha)})
        return True
    return False


class CriarUsuarioService:
    @staticmethod
    def executar(dados, usuario=None):
        nome = (dados.get('nome') or '').strip()
        email = (dados.get('email') or '').strip().lower()
        senha = str(dados.get('senha') or '')

        if not nome:
            raise ValueError("o nome é obrigatório")
        if not REGEX_EMAIL.match(email):
            raise ValueError("informe um e-mail válido")
        if len(senha) < 6:
            raise ValueError("a senha deve ter no mínimo 6 caracteres")
        if UsuarioRepository.buscar_por_email(email):
            raise ValueError("já existe um usuário cadastrado com esse e-mail")

        # a LGPD exige que o consentimento fique registrado - por isso a gente
        # bloqueia o cadastro se a pessoa nao marcou que aceita os termos
        if not dados.get('aceitou_termos'):
            raise ValueError("é necessário aceitar o termo de uso e o termo de consentimento para se cadastrar")

        # so entram os campos do cadastro: "adm" e "bloqueado" nunca vem de fora
        novos = {campo: dados[campo] for campo in CAMPOS_CADASTRO if campo in dados}
        novos.update(nome=nome, email=email, senha=generate_password_hash(senha),
                     aceitou_termos=True, data_aceite_termos=agora())
        novos['tipo'] = novos.get('tipo') or 'jogador'
        validar_perfil(novos)
        return Usuario.salvar(novos)


class VisualizarUsuarioService:
    # decide o que cada pessoa pode ver de um usuario (regra de permissao fica no service, nao na controller):
    # admin e o proprio dono do perfil veem tudo; o resto so ve os dados publicos
    @staticmethod
    def executar(alvo, solicitante):
        if solicitante.adm or solicitante.id == alvo.id:
            return alvo.to_dict()
        return alvo.to_public_dict()


class ListarUsuarioService:
    @staticmethod
    def executar(usuario=None):
        return Usuario.listar_todos()


class BuscarUsuarioPorIdService:
    @staticmethod
    def executar(id):
        return Usuario.buscar_por_id(id)


class AtualizarUsuarioService:
    # usado pelo admin (rota protegida): pode mexer em qualquer usuario, inclusive adm e bloqueado
    @staticmethod
    def executar(id, dados, usuario=None):
        novos = {campo: dados[campo] for campo in (CAMPOS_CADASTRO | {'adm', 'bloqueado'}) if campo in dados}
        if 'email' in novos:
            novos['email'] = (novos['email'] or '').strip().lower()
            if not REGEX_EMAIL.match(novos['email']):
                raise ValueError("informe um e-mail válido")
            if UsuarioRepository.buscar_outro_com_email(novos['email'], id):
                raise ValueError("já existe um usuário cadastrado com esse e-mail")
        if 'senha' in novos:
            if not novos['senha']:
                del novos['senha']
            elif len(str(novos['senha'])) < 6:
                raise ValueError("a senha deve ter no mínimo 6 caracteres")
            else:
                novos['senha'] = generate_password_hash(str(novos['senha']))
        validar_perfil(novos)
        atualizado = Usuario.atualizar(id, novos)
        if atualizado and 'bloqueado' in novos:
            registrar_log(usuario, f'{"Bloqueou" if atualizado.bloqueado else "Desbloqueou"} o usuário "{atualizado.nome}"')
        return atualizado


class ExcluirUsuarioService:
    @staticmethod
    def executar(id, usuario=None):
        alvo = Usuario.buscar_por_id(id)
        if not alvo:
            return False
        # notificacoes, candidatura e solicitacoes saem junto com a conta (sem isso o banco recusava a
        # exclusao de quase todo mundo). duplas, quadras e campeonatos continuam protegidos: se existirem,
        # Usuario.deletar desfaz tudo (rollback) e avisa com 409
        UsuarioRepository.remover_vinculos(id)
        sucesso = Usuario.deletar(id)
        if sucesso:
            registrar_log(usuario, f'Excluiu o usuário "{alvo.nome}"')
        return sucesso


class AtualizarMeuPerfilService:
    # service usado quando o PROPRIO usuario edita o perfil dele (nao o admin editando qualquer um)
    # por seguranca, so deixa alterar os campos do perfil - mesmo que o pedido tente mandar
    # "email", "senha", "tipo", "adm" ou "bloqueado", esses campos sao ignorados aqui
    CAMPOS_PERMITIDOS = CAMPOS_CADASTRO - {'email', 'senha', 'tipo'}

    @staticmethod
    def executar(id_usuario, dados):
        dados_filtrados = {
            campo: valor for campo, valor in dados.items()
            if campo in AtualizarMeuPerfilService.CAMPOS_PERMITIDOS
        }
        if 'nome' in dados_filtrados and not (dados_filtrados['nome'] or '').strip():
            raise ValueError("o nome é obrigatório")
        validar_perfil(dados_filtrados)
        return Usuario.atualizar(id_usuario, dados_filtrados)


class AlterarSenhaService:
    @staticmethod
    def executar(usuario, senha_atual, senha_nova):
        exigir_login(usuario)
        if not senha_confere(usuario, senha_atual):
            raise ValueError("a senha atual está incorreta")
        if len(str(senha_nova or '')) < 6:
            raise ValueError("a senha nova deve ter no mínimo 6 caracteres")
        return Usuario.atualizar(usuario.id, {'senha': generate_password_hash(str(senha_nova))})