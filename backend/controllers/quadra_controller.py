# controller de quadras
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_login
from services.quadra_service import (
    ListarQuadraService,
    BuscarQuadraPorIdService,
    CriarQuadraService,
    AtualizarQuadraService,
    ExcluirQuadraService,
)


class QuadraController:
    def listar(self):
        itens = ListarQuadraService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    def buscar(self, id):
        item = BuscarQuadraPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "quadra não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarQuadraService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_login
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarQuadraService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "quadra não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def deletar(self, id):
        try:
            sucesso = ExcluirQuadraService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "quadra não encontrada"}), 404
        return jsonify({"mensagem": "quadra removida"}), 200


quadra_controller = QuadraController()


def registrar_rotas_quadra(app):
    app.add_url_rule('/api/quadras', endpoint='listar_quadras', view_func=quadra_controller.listar, methods=['GET'])
    app.add_url_rule('/api/quadras', endpoint='criar_quadra', view_func=quadra_controller.criar, methods=['POST'])
    app.add_url_rule('/api/quadras/<int:id>', endpoint='buscar_quadra', view_func=quadra_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/quadras/<int:id>', endpoint='atualizar_quadra', view_func=quadra_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/quadras/<int:id>', endpoint='deletar_quadra', view_func=quadra_controller.deletar, methods=['DELETE'])
