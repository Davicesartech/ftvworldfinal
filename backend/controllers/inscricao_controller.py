# controller de inscricoes
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_admin, exigir_login
from controllers.respostas import resposta_erro
from services.inscricao_service import (
    ListarInscricaoService,
    BuscarInscricaoPorIdService,
    CriarInscricaoService,
    AtualizarInscricaoService,
    ExcluirInscricaoService,
    CancelarInscricaoService,
)


class InscricaoController:
    @exigir_login
    def listar(self):
        itens = ListarInscricaoService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    @exigir_login
    def buscar(self, id):
        item = BuscarInscricaoPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "inscrição não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarInscricaoService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_admin
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarInscricaoService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "inscrição não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_admin
    def deletar(self, id):
        try:
            sucesso = ExcluirInscricaoService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "inscrição não encontrada"}), 404
        return jsonify({"mensagem": "inscrição removida"}), 200

    @exigir_login
    def cancelar(self, id):
        try:
            inscricao = CancelarInscricaoService.executar(id, g.usuario)
        except ValueError as e:
            return resposta_erro(str(e), 400)
        except PermissionError as e:
            return resposta_erro(str(e), 403)
        if not inscricao:
            return resposta_erro("inscrição não encontrada", 404)
        return jsonify(inscricao.to_dict()), 200


inscricao_controller = InscricaoController()


def registrar_rotas_inscricao(app):
    app.add_url_rule('/api/inscricoes', endpoint='listar_inscricoes', view_func=inscricao_controller.listar, methods=['GET'])
    app.add_url_rule('/api/inscricoes', endpoint='criar_inscricao', view_func=inscricao_controller.criar, methods=['POST'])
    app.add_url_rule('/api/inscricoes/<int:id>', endpoint='buscar_inscricao', view_func=inscricao_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/inscricoes/<int:id>', endpoint='atualizar_inscricao', view_func=inscricao_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/inscricoes/<int:id>', endpoint='deletar_inscricao', view_func=inscricao_controller.deletar, methods=['DELETE'])
    app.add_url_rule('/api/inscricoes/<int:id>/cancelar', endpoint='cancelar_inscricao', view_func=inscricao_controller.cancelar, methods=['POST'])
