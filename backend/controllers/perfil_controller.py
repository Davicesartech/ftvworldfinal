# controller do "meu perfil" - rota protegida, usada pelo PROPRIO jogador
# pra editar os dados dele mesmo. diferente da rota generica /api/usuarios/<id>
# (que o admin usa pra editar qualquer usuario), essa aqui exige um token
# valido e so deixa a pessoa editar o proprio cadastro - nunca o de outra pessoa

from flask import request, jsonify, g

from controllers.protecao import exigir_login
from services.usuario_service import AtualizarMeuPerfilService, AlterarSenhaService


class PerfilController:
    @exigir_login
    def atualizar_meu_perfil(self):
        dados = request.get_json(silent=True) or {}
        try:
            usuario = AtualizarMeuPerfilService.executar(g.usuario.id, dados)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400

        if not usuario:
            return jsonify({"erro": "usuário não encontrado"}), 404
        return jsonify(usuario.to_dict()), 200

    @exigir_login
    def alterar_senha(self):
        dados = request.get_json(silent=True) or {}
        try:
            AlterarSenhaService.executar(g.usuario, dados.get('senha_atual'), dados.get('senha_nova'))
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        return jsonify({"mensagem": "senha alterada"}), 200


perfil_controller = PerfilController()


def registrar_rotas_perfil(app):
    app.add_url_rule(
        '/api/meu-perfil',
        endpoint='atualizar_meu_perfil',
        view_func=perfil_controller.atualizar_meu_perfil,
        methods=['PUT']
    )
    app.add_url_rule(
        '/api/meu-perfil/senha',
        endpoint='alterar_minha_senha',
        view_func=perfil_controller.alterar_senha,
        methods=['PUT']
    )
