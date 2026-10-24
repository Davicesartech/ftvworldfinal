# controller de duplas
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_admin, exigir_login
from controllers.respostas import resposta_erro
from services.dupla_service import (
    ListarDuplaService,
    BuscarDuplaPorIdService,
    CriarDuplaService,
    AtualizarDuplaService,
    ExcluirDuplaService,
    DesfazerDuplaService,
)


class DuplaController:
    @exigir_login
    def listar(self):
        itens = ListarDuplaService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    @exigir_login
    def buscar(self, id):
        item = BuscarDuplaPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "dupla não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarDuplaService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_admin
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarDuplaService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "dupla não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_admin
    def deletar(self, id):
        try:
            sucesso = ExcluirDuplaService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "dupla não encontrada"}), 404
        return jsonify({"mensagem": "dupla removida"}), 200

    @exigir_login
    def desfazer(self, id):
        try:
            dupla = DesfazerDuplaService.executar(id, g.usuario)
        except PermissionError as e:
            return resposta_erro(str(e), 403)
        if not dupla:
            return resposta_erro("dupla não encontrada", 404)
        return jsonify(dupla.to_dict()), 200


dupla_controller = DuplaController()


def registrar_rotas_dupla(app):
    app.add_url_rule('/api/duplas', endpoint='listar_duplas', view_func=dupla_controller.listar, methods=['GET'])
    app.add_url_rule('/api/duplas', endpoint='criar_dupla', view_func=dupla_controller.criar, methods=['POST'])
    app.add_url_rule('/api/duplas/<int:id>', endpoint='buscar_dupla', view_func=dupla_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/duplas/<int:id>', endpoint='atualizar_dupla', view_func=dupla_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/duplas/<int:id>', endpoint='deletar_dupla', view_func=dupla_controller.deletar, methods=['DELETE'])
    app.add_url_rule('/api/duplas/<int:id>/desfazer', endpoint='desfazer_dupla', view_func=dupla_controller.desfazer, methods=['POST'])
