# service de login (autenticacao)

from repositories.usuario_repository import UsuarioRepository
from services.usuario_service import senha_confere


class LoginService:
    @staticmethod
    def executar(email, senha):
        usuario = UsuarioRepository.buscar_por_email((email or '').strip().lower())
        if not usuario or not senha_confere(usuario, senha):
            raise ValueError("e-mail ou senha incorretos")
        if usuario.bloqueado:
            raise ValueError("esta conta foi bloqueada pelo administrador")
        return usuario
