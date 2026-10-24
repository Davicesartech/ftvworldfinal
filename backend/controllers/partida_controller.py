# controller de partidas
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_login
from services.partida_service import (
    ListarPartidaService,
    BuscarPartidaPorIdService,
    CriarPartidaService,
    AtualizarPartidaService,
    ExcluirPartidaService,
)


class PartidaController:
    def listar(self):
        itens = ListarPartidaService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    def buscar(self, id):
        item = BuscarPartidaPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "partida não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarPartidaService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_login
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarPartidaService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "partida não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def deletar(self, id):
        try:
            sucesso = ExcluirPartidaService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "partida não encontrada"}), 404
        return jsonify({"mensagem": "partida removida"}), 200


partida_controller = PartidaController()


def registrar_rotas_partida(app):
    app.add_url_rule('/api/partidas', endpoint='listar_partidas', view_func=partida_controller.listar, methods=['GET'])
    app.add_url_rule('/api/partidas', endpoint='criar_partida', view_func=partida_controller.criar, methods=['POST'])
    app.add_url_rule('/api/partidas/<int:id>', endpoint='buscar_partida', view_func=partida_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/partidas/<int:id>', endpoint='atualizar_partida', view_func=partida_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/partidas/<int:id>', endpoint='deletar_partida', view_func=partida_controller.deletar, methods=['DELETE'])
