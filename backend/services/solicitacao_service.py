# services da solicitacao de dupla: quem envia espera; so quem recebe aceita ou recusa (aceitar cria a dupla)

from models import Solicitacao, Usuario
from repositories.dupla_repository import DuplaRepository
from repositories.solicitacao_repository import SolicitacaoRepository
from services.comum import como_inteiro, eh_admin, exigir_login, notificar, registrar_log
from services.dupla_service import formar_dupla


def solicitacao_pendente(id):
    solicitacao = Solicitacao.buscar_por_id(id)
    if solicitacao and solicitacao.status != 'pendente':
        raise ValueError("esta solicitação não está mais disponível")
    return solicitacao


class CriarSolicitacaoService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario)
        de = usuario.id
        para = como_inteiro(dados.get('id_para'), 'id_para')
        if de == para:
            raise ValueError("você não pode enviar uma solicitação para si mesmo")
        alvo = Usuario.buscar_por_id(para)
        if not alvo or alvo.bloqueado:
            raise ValueError("jogador não encontrado")
        if 'dono' in (usuario.tipo, alvo.tipo):
            raise ValueError("donos de quadra não participam de duplas")
        if DuplaRepository.buscar_ativa_do_usuario(de) or DuplaRepository.buscar_ativa_do_usuario(para):
            raise ValueError("um dos jogadores já está em uma dupla ativa")
        if SolicitacaoRepository.buscar_pendente_entre(de, para):
            raise ValueError("já existe uma solicitação pendente entre vocês")
        solicitacao = Solicitacao.salvar({'id_de': de, 'id_para': para, 'status': 'pendente'})
        notificar(para, f"{usuario.nome} quer formar dupla com você.")
        return solicitacao


class ListarSolicitacaoService:
    @staticmethod
    def executar(usuario=None):
        # admin ve todas; o resto so as que enviou ou recebeu
        if eh_admin(usuario):
            return Solicitacao.listar_todos()
        return SolicitacaoRepository.listar_do_usuario(usuario.id)


class BuscarSolicitacaoPorIdService:
    @staticmethod
    def executar(id):
        return Solicitacao.buscar_por_id(id)


class AtualizarSolicitacaoService:
    @staticmethod
    def executar(id, dados, usuario=None):
        return Solicitacao.atualizar(id, dados)


class ExcluirSolicitacaoService:
    @staticmethod
    def executar(id, usuario=None):
        return Solicitacao.deletar(id)


class ResponderSolicitacaoService:
    # devolve (solicitacao, dupla): a dupla so existe quando a pessoa aceitou
    @staticmethod
    def executar(id, aceitar, usuario=None):
        exigir_login(usuario)
        solicitacao = solicitacao_pendente(id)
        if not solicitacao:
            return None
        if solicitacao.id_para != usuario.id:
            raise PermissionError("só quem recebeu a solicitação pode responder")
        if not aceitar:
            solicitacao = Solicitacao.atualizar(id, {'status': 'recusada'})
            notificar(solicitacao.id_de, f"{usuario.nome} recusou a solicitação de dupla.")
            return solicitacao, None
        dupla = formar_dupla(None, solicitacao.id_de, solicitacao.id_para)
        # formar_dupla cancela as pendentes, entao a solicitacao so eh marcada como aceita depois
        solicitacao = Solicitacao.atualizar(id, {'status': 'aceita'})
        notificar(solicitacao.id_de, f'{usuario.nome} aceitou! A dupla "{dupla.nome}" foi formada.')
        registrar_log(usuario, f'Formou a dupla "{dupla.nome}"')
        return solicitacao, dupla


class CancelarSolicitacaoService:
    @staticmethod
    def executar(id, usuario=None):
        exigir_login(usuario)
        solicitacao = solicitacao_pendente(id)
        if not solicitacao:
            return None
        if solicitacao.id_de != usuario.id:
            raise PermissionError("só quem enviou pode cancelar a solicitação")
        return Solicitacao.atualizar(id, {'status': 'cancelada'})