# services da config do site (imagens do banner etc.)

from models import Config
from services.comum import REGEX_CHAVE, eh_admin, registrar_log


class ListarConfigService:
    @staticmethod
    def executar(usuario=None):
        # lista de {chave, valor}: o front faz .map() nela (antes voltava um dicionario e quebrava)
        return [c.to_dict() for c in Config.listar_todos()]


class SalvarConfigService:
    @staticmethod
    def executar(chave, valor, usuario=None):
        if not eh_admin(usuario):
            raise PermissionError("acesso restrito ao administrador")
        if not REGEX_CHAVE.match(chave or ''):
            raise ValueError("chave inválida: use letras minúsculas, números, - e _")
        config = Config.salvar(chave, valor)
        registrar_log(usuario, f'Atualizou a configuração "{chave}"')
        return config


class ExcluirConfigService:
    @staticmethod
    def executar(chave, usuario=None):
        if not eh_admin(usuario):
            raise PermissionError("acesso restrito ao administrador")
        sucesso = Config.deletar(chave)
        if sucesso:
            registrar_log(usuario, f'Removeu a configuração "{chave}"')
        return sucesso