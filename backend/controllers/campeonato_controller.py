# controller de campeonatos
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_login
from services.campeonato_service import (
    ListarCampeonatoService,
    BuscarCampeonatoPorIdService,
    CriarCampeonatoService,
    AtualizarCampeonatoService,
    ExcluirCampeonatoService,
)


class CampeonatoController:
    def listar(self):
        itens = ListarCampeonatoService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    def buscar(self, id):
        item = BuscarCampeonatoPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "campeonato não encontrado"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarCampeonatoService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_login
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarCampeonatoService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "campeonato não encontrado"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def deletar(self, id):
        try:
            sucesso = ExcluirCampeonatoService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "campeonato não encontrado"}), 404
        return jsonify({"mensagem": "campeonato removido"}), 200


campeonato_controller = CampeonatoController()


def registrar_rotas_campeonato(app):
    app.add_url_rule('/api/campeonatos', endpoint='listar_campeonatos', view_func=campeonato_controller.listar, methods=['GET'])
    app.add_url_rule('/api/campeonatos', endpoint='criar_campeonato', view_func=campeonato_controller.criar, methods=['POST'])
    app.add_url_rule('/api/campeonatos/<int:id>', endpoint='buscar_campeonato', view_func=campeonato_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/campeonatos/<int:id>', endpoint='atualizar_campeonato', view_func=campeonato_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/campeonatos/<int:id>', endpoint='deletar_campeonato', view_func=campeonato_controller.deletar, methods=['DELETE'])
