# controller de notificacoes
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import request, jsonify, g

from controllers.protecao import exigir_admin, exigir_login
from controllers.respostas import resposta_erro
from services.notificacao_service import (
    ListarNotificacaoService,
    BuscarNotificacaoPorIdService,
    CriarNotificacaoService,
    AtualizarNotificacaoService,
    ExcluirNotificacaoService,
    MarcarNotificacaoLidaService,
    MarcarTodasNotificacoesLidasService,
)


class NotificacaoController:
    @exigir_admin
    def listar(self):
        itens = ListarNotificacaoService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    @exigir_admin
    def buscar(self, id):
        item = BuscarNotificacaoPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "notificação não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_admin
    def criar(self):
        dados = request.get_json(silent=True) or {}
        try:
            item = CriarNotificacaoService.executar(dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(item.to_dict()), 201

    @exigir_admin
    def atualizar(self, id):
        dados = request.get_json(silent=True) or {}
        try:
            item = AtualizarNotificacaoService.executar(id, dados, g.usuario)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        if not item:
            return jsonify({"erro": "notificação não encontrada"}), 404
        return jsonify(item.to_dict()), 200

    @exigir_admin
    def deletar(self, id):
        try:
            sucesso = ExcluirNotificacaoService.executar(id, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 409
        if not sucesso:
            return jsonify({"erro": "notificação não encontrada"}), 404
        return jsonify({"mensagem": "notificação removida"}), 200

    # --- notificacoes do proprio usuario (o sino do cabecalho) ---

    @exigir_login
    def minhas(self):
        notificacoes = ListarNotificacaoService.executar(g.usuario)
        return jsonify([n.to_dict() for n in notificacoes]), 200

    @exigir_login
    def marcar_lida(self, id):
        try:
            notificacao = MarcarNotificacaoLidaService.executar(id, g.usuario)
        except PermissionError as e:
            return resposta_erro(str(e), 403)
        if not notificacao:
            return resposta_erro("notificação não encontrada", 404)
        return jsonify(notificacao.to_dict()), 200

    @exigir_login
    def marcar_todas_lidas(self):
        total = MarcarTodasNotificacoesLidasService.executar(g.usuario)
        return jsonify({"mensagem": "notificações marcadas como lidas", "total": total}), 200


notificacao_controller = NotificacaoController()


def registrar_rotas_notificacao(app):
    app.add_url_rule('/api/notificacoes', endpoint='listar_notificacoes', view_func=notificacao_controller.listar, methods=['GET'])
    app.add_url_rule('/api/notificacoes', endpoint='criar_notificacao', view_func=notificacao_controller.criar, methods=['POST'])
    app.add_url_rule('/api/notificacoes/<int:id>', endpoint='buscar_notificacao', view_func=notificacao_controller.buscar, methods=['GET'])
    app.add_url_rule('/api/notificacoes/<int:id>', endpoint='atualizar_notificacao', view_func=notificacao_controller.atualizar, methods=['PUT'])
    app.add_url_rule('/api/notificacoes/<int:id>', endpoint='deletar_notificacao', view_func=notificacao_controller.deletar, methods=['DELETE'])
    app.add_url_rule('/api/minhas-notificacoes', endpoint='minhas_notificacoes', view_func=notificacao_controller.minhas, methods=['GET'])
    app.add_url_rule('/api/minhas-notificacoes/ler-todas', endpoint='marcar_todas_lidas', view_func=notificacao_controller.marcar_todas_lidas, methods=['PUT'])
    app.add_url_rule('/api/minhas-notificacoes/<int:id>/ler', endpoint='marcar_lida', view_func=notificacao_controller.marcar_lida, methods=['PUT'])
