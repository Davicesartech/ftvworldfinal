# controller de solicitacoes
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_admin, exigir_login
from controllers.respostas import resposta_erro
from services.solicitacao_service import (
    ListarSolicitacaoService,
    BuscarSolicitacaoPorIdService,
    CriarSolicitacaoService,
    AtualizarSolicitacaoService,
    ExcluirSolicitacaoService,
    ResponderSolicitacaoService,
    CancelarSolicitacaoService,
)


class SolicitacaoController:
    @exigir_login
    def listar(self):
        itens = ListarSolicitacaoService.executar(g.usuario)
        return jsonify([i.to_dict() for i in itens]), 200

    @exigir_admin
    def buscar(self, id):
        item = BuscarSolicitacaoPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "solicitação não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_login
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarSolicitacaoService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_admin
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarSolicitacaoService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "solicitação não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_admin
    def deletar(self, id):
        try:
            sucesso = ExcluirSolicitacaoService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "solicitação não encontrada"}), 404
        return jsonify({"mensagem": "solicitação removida"}), 200

    # --- aceitar / recusar / cancelar ---

    def _responder(self, id, aceitar):
        try:
            resultado = ResponderSolicitacaoService.executar(id, aceitar, g.usuario)
        except ValueError as e:
            return resposta_erro(str(e), 400)
        except PermissionError as e:
            return resposta_erro(str(e), 403)
        if not resultado:
            return resposta_erro("solicitação não encontrada", 404)
        solicitacao, dupla = resultado
        return jsonify({"solicitacao": solicitacao.to_dict(), "dupla": dupla.to_dict() if dupla else None}), 200

    @exigir_login
    def aceitar(self, id):
        return self._responder(id, True)

    @exigir_login
    def recusar(self, id):
        return self._responder(id, False)

    @exigir_login
    def cancelar(self, id):
        try:
            solicitacao = CancelarSolicitacaoService.executar(id, g.usuario)
        except ValueError as e:
            return resposta_erro(str(e), 400)
        except PermissionError as e:
            return resposta_erro(str(e), 403)
        if not solicitacao:
            return resposta_erro("solicitação não encontrada", 404)
        return jsonify(solicitacao.to_dict()), 200


solicitacao_controller = SolicitacaoController()


def registrar_rotas_solicitacao(app):
    app.add_url_rule('/api/solicitacoes', endpoint='listar_solicitacoes', view_func=solicitacao_controller.listar, methods=['GET'])
    app.add_url_rule('/api/solicitacoes', endpoint='criar_solicitacao', view_func=solicitacao_controller.criar, methods=['POST'])
    app.add_url_rule('/api/solicitacoes/<int:id>', endpoint='buscar_solicitacao', view_func=solicitacao_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/solicitacoes/<int:id>', endpoint='atualizar_solicitacao', view_func=solicitacao_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/solicitacoes/<int:id>', endpoint='deletar_solicitacao', view_func=solicitacao_controller.deletar, methods=['DELETE'])
    app.add_url_rule('/api/solicitacoes/<int:id>/aceitar', endpoint='aceitar_solicitacao', view_func=solicitacao_controller.aceitar, methods=['POST'])
    app.add_url_rule('/api/solicitacoes/<int:id>/recusar', endpoint='recusar_solicitacao', view_func=solicitacao_controller.recusar, methods=['POST'])
    app.add_url_rule('/api/solicitacoes/<int:id>/cancelar', endpoint='cancelar_solicitacao', view_func=solicitacao_controller.cancelar, methods=['POST'])
