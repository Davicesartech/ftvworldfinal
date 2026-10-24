# controller de candidatos
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_admin, exigir_login
from controllers.respostas import resposta_erro
from services.candidato_service import (
    ListarCandidatoService,
    BuscarCandidatoPorIdService,
    CriarCandidatoService,
    AtualizarCandidatoService,
    ExcluirCandidatoService,
    ExcluirMinhaCandidaturaService,
)


class CandidatoController:
    @exigir_login
    def listar(self):
        itens = ListarCandidatoService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    @exigir_login
    def buscar(self, id):
        item = BuscarCandidatoPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "candidato não encontrado"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarCandidatoService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_admin
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarCandidatoService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "candidato não encontrado"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_admin
    def deletar(self, id):
        try:
            sucesso = ExcluirCandidatoService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "candidato não encontrado"}), 404
        return jsonify({"mensagem": "candidato removido"}), 200

    # --- candidatura propria ("encontre sua dupla") ---

    @exigir_login
    def remover_minha(self):
        if not ExcluirMinhaCandidaturaService.executar(g.usuario):
            return resposta_erro("você não tem candidatura publicada", 404)
        return jsonify({"mensagem": "candidatura removida"}), 200


candidato_controller = CandidatoController()


def registrar_rotas_candidato(app):
    app.add_url_rule('/api/candidatos', endpoint='listar_candidatos', view_func=candidato_controller.listar, methods=['GET'])
    app.add_url_rule('/api/candidatos', endpoint='criar_candidato', view_func=candidato_controller.criar, methods=['POST'])
    app.add_url_rule('/api/candidatos/<int:id>', endpoint='buscar_candidato', view_func=candidato_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/candidatos/<int:id>', endpoint='atualizar_candidato', view_func=candidato_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/candidatos/<int:id>', endpoint='deletar_candidato', view_func=candidato_controller.deletar, methods=['DELETE'])
    app.add_url_rule('/api/candidatos/minha', endpoint='remover_minha_candidatura', view_func=candidato_controller.remover_minha, methods=['DELETE'])
