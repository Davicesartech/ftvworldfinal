# controller de logs (so leitura: a trilha de auditoria nao pode ser alterada pela API)
# so recebe a requisicao, chama o service certo e devolve a resposta - nada de regra de negocio aqui
# erros: ValueError -> 400 (no excluir, 409), PermissionError -> 403, registro nao achado -> 404

from flask import jsonify

from controllers.protecao import exigir_admin
from services.log_service import (
    ListarLogService,
    BuscarLogPorIdService,
)


class LogController:
    @exigir_admin
    def listar(self):
        itens = ListarLogService.executar()
        return jsonify([i.to_dict() for i in itens]), 200

    @exigir_admin
    def buscar(self, id):
        item = BuscarLogPorIdService.executar(id)
        if not item:
            return jsonify({"erro": "log não encontrado"}), 404
        return jsonify(item.to_dict()), 200


log_controller = LogController()


def registrar_rotas_log(app):
    app.add_url_rule('/api/logs', endpoint='listar_logs', view_func=log_controller.listar, methods=['GET'])
    app.add_url_rule('/api/logs/<int:id>', endpoint='buscar_log', view_func=log_controller.buscar, methods=['GET'])
