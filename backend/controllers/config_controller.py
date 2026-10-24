# controller da configuracao do site (imagens do banner etc.)
# a leitura eh publica (o banner aparece na pagina inicial); salvar e excluir so o admin

from flask import request, jsonify, g

from controllers.protecao import exigir_admin
from controllers.respostas import resposta_erro
from services.config_service import ListarConfigService, SalvarConfigService, ExcluirConfigService


class ConfigController:
    def listar(self):
        return jsonify(ListarConfigService.executar()), 200

    @exigir_admin
    def salvar(self, chave):
        dados = request.get_json(silent=True) or {}
        if 'valor' not in dados:
            return resposta_erro("envie o campo \"valor\"", 400)
        try:
            config = SalvarConfigService.executar(chave, dados['valor'], g.usuario)
        except ValueError as e:
            return resposta_erro(str(e), 400)
        return jsonify(config.to_dict()), 200

    @exigir_admin
    def excluir(self, chave):
        if not ExcluirConfigService.executar(chave, g.usuario):
            return resposta_erro("configuração não encontrada", 404)
        return jsonify({"mensagem": "configuração removida"}), 200


config_controller = ConfigController()


def registrar_rotas_config(app):
    app.add_url_rule('/api/config', endpoint='listar_config', view_func=config_controller.listar, methods=['GET'])
    app.add_url_rule('/api/config/<chave>', endpoint='salvar_config', view_func=config_controller.salvar, methods=['PUT'])
    app.add_url_rule('/api/config/<chave>', endpoint='excluir_config', view_func=config_controller.excluir, methods=['DELETE'])
