# controller de login - separado do resto, so cuida de autenticar o usuario
# nao mexe em nada das outras controllers

from flask import request, jsonify, g

from controllers.protecao import exigir_login
from services.auth_service import LoginService
from services.sessao import gerar_token, remover_token


class LoginController:
    def login(self):
        dados = request.get_json(silent=True) or {}
        try:
            usuario = LoginService.executar(dados.get('email'), dados.get('senha'))
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 401

        resposta = usuario.to_dict()
        resposta['token'] = gerar_token(usuario.id)
        return jsonify(resposta), 200

    def logout(self):
        remover_token(request.headers.get('Authorization'))
        return jsonify({"mensagem": "logout feito"}), 200

    @exigir_login
    def eu(self):
        # devolve quem esta logado (o front usa pra recuperar a sessao)
        return jsonify(g.usuario.to_dict()), 200


login_controller = LoginController()


def registrar_rotas_login(app):
    app.add_url_rule('/api/login', endpoint='login', view_func=login_controller.login, methods=['POST'])
    app.add_url_rule('/api/logout', endpoint='logout', view_func=login_controller.logout, methods=['POST'])
    app.add_url_rule('/api/eu', endpoint='eu', view_func=login_controller.eu, methods=['GET'])
