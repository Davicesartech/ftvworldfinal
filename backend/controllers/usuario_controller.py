# controller de usuarios
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_admin, exigir_login
from services.usuario_service import (
    ListarUsuarioService,
    BuscarUsuarioPorIdService,
    CriarUsuarioService,
    AtualizarUsuarioService,
    ExcluirUsuarioService,
    VisualizarUsuarioService,
)


class UsuarioController:
    @exigir_login
    def listar(self):
        itens = ListarUsuarioService.executar()
        return jsonify([VisualizarUsuarioService.executar(i, g.usuario) for i in itens]), 200

    @exigir_login
    def buscar(self, id):
        item = BuscarUsuarioPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "usuário não encontrado"}), 404
        return jsonify(VisualizarUsuarioService.executar(item, g.usuario)), 200

    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarUsuarioService.executar(dados, None)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_admin
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarUsuarioService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "usuário não encontrado"}), 404
        return jsonify(VisualizarUsuarioService.executar(item, g.usuario)), 200

    @exigir_admin
    def deletar(self, id):
        try:
            sucesso = ExcluirUsuarioService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "usuário não encontrado"}), 404
        return jsonify({"mensagem": "usuário removido"}), 200


usuario_controller = UsuarioController()


def registrar_rotas_usuario(app):
    app.add_url_rule('/api/usuarios', endpoint='listar_usuarios', view_func=usuario_controller.listar, methods=['GET'])
    app.add_url_rule('/api/usuarios', endpoint='criar_usuario', view_func=usuario_controller.criar, methods=['POST'])
    app.add_url_rule('/api/usuarios/<int:id>', endpoint='buscar_usuario', view_func=usuario_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/usuarios/<int:id>', endpoint='atualizar_usuario', view_func=usuario_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/usuarios/<int:id>', endpoint='deletar_usuario', view_func=usuario_controller.deletar, methods=['DELETE'])
