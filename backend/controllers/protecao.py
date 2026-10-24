# protecao das rotas - decoradores que olham o token JWT antes da controller rodar
# @exigir_login: precisa de token valido e a conta nao pode estar bloqueada
# @exigir_admin: alem do login, a conta precisa ser de administrador
# quem passou fica em g.usuario pra controller entregar pro service
# (aqui so se confere QUEM eh a pessoa; as regras de negocio ficam nos services)

from functools import wraps

from flask import request, jsonify, g

from models import Usuario
from services.sessao import usuario_do_token


def exigir_login(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        id_usuario = usuario_do_token(request.headers.get('Authorization'))
        usuario = Usuario.buscar_por_id(id_usuario) if id_usuario else None
        if not usuario or usuario.bloqueado:
            return jsonify({"erro": "não autorizado, faça login novamente"}), 401
        g.usuario = usuario
        return funcao(*args, **kwargs)
    return verificar


def exigir_admin(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if not g.usuario.adm:
            return jsonify({"erro": "acesso restrito ao administrador"}), 403
        return funcao(*args, **kwargs)
    return exigir_login(verificar)
