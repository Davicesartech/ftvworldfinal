# services da notificacao

from models import Notificacao
from repositories.notificacao_repository import NotificacaoRepository
from services.comum import exigir_login


class CriarNotificacaoService:
    @staticmethod
    def executar(dados, usuario=None):
        return Notificacao.salvar(dados)


class ListarNotificacaoService:
    @staticmethod
    def executar(usuario=None):
        # com usuario: so as dele (mais novas primeiro). sem usuario: todas (admin)
        if usuario:
            return NotificacaoRepository.listar_do_usuario(usuario.id)
        return Notificacao.listar_todos()


class BuscarNotificacaoPorIdService:
    @staticmethod
    def executar(id):
        return Notificacao.buscar_por_id(id)


class AtualizarNotificacaoService:
    @staticmethod
    def executar(id, dados, usuario=None):
        return Notificacao.atualizar(id, dados)


class ExcluirNotificacaoService:
    @staticmethod
    def executar(id, usuario=None):
        return Notificacao.deletar(id)


class MarcarNotificacaoLidaService:
    @staticmethod
    def executar(id, usuario=None):
        exigir_login(usuario)
        notificacao = Notificacao.buscar_por_id(id)
        if not notificacao:
            return None
        if notificacao.id_usuario != usuario.id:
            raise PermissionError("essa notificação não é sua")
        return Notificacao.atualizar(id, {'lida': True})


class MarcarTodasNotificacoesLidasService:
    @staticmethod
    def executar(usuario=None):
        exigir_login(usuario)
        return NotificacaoRepository.marcar_todas_como_lidas(usuario.id)