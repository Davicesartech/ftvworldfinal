# controllers dos relatorios (funcionalidades avançadas)
# mesmo estilo das outras controllers: classe simples, so recebe a requisição e devolve o resultado
# nenhuma regra de negocio ou de permissao fica aqui: tudo isso esta em services/relatorio_service.py
# (o @exigir_login so identifica QUEM esta chamando e entrega g.usuario para o service decidir)
# os relatorios chamam procedures do mysql (veja database/procedures.sql)
# erros: PermissionError -> 403

from flask import request, jsonify, g

from controllers.protecao import exigir_login
from services.relatorio_service import (
    CampeonatosDisponiveisService,
    TodosCampeonatosService,
    ClassificacaoCampeonatoService,
    RankingDuplasService,
    InscritosCampeonatoService,
    HistoricoPartidasUsuarioService,
    QuadrasMaisUtilizadasService,
    ResumoAdminService,
)


class RelatorioController:

    def campeonatos_disponiveis(self):
        categoria = request.args.get('categoria') or None
        nivel = request.args.get('nivel') or None
        resultado = CampeonatosDisponiveisService.executar(categoria, nivel)
        return jsonify(resultado), 200

    def todos_campeonatos(self):
        nivel = request.args.get('nivel') or None
        resultado = TodosCampeonatosService.executar(nivel)
        return jsonify(resultado), 200

    def classificacao_campeonato(self, id_campeonato):
        resultado = ClassificacaoCampeonatoService.executar(id_campeonato)
        return jsonify(resultado), 200

    def ranking_duplas(self):
        resultado = RankingDuplasService.executar()
        return jsonify(resultado), 200

    @exigir_login
    def inscritos_campeonato(self, id_campeonato):
        try:
            resultado = InscritosCampeonatoService.executar(id_campeonato, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(resultado), 200

    @exigir_login
    def historico_usuario(self, id_usuario):
        try:
            resultado = HistoricoPartidasUsuarioService.executar(id_usuario, g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(resultado), 200

    def quadras_mais_utilizadas(self):
        resultado = QuadrasMaisUtilizadasService.executar()
        return jsonify(resultado), 200

    @exigir_login
    def resumo_admin(self):
        try:
            resultado = ResumoAdminService.executar(g.usuario)
        except PermissionError as erro:
            return jsonify({"erro": str(erro)}), 403
        return jsonify(resultado), 200


relatorio_controller = RelatorioController()


def registrar_rotas_relatorios(app):
    app.add_url_rule('/api/relatorios/campeonatos-disponiveis', endpoint='campeonatos_disponiveis', view_func=relatorio_controller.campeonatos_disponiveis, methods=['GET'])
    app.add_url_rule('/api/relatorios/campeonatos', endpoint='todos_campeonatos', view_func=relatorio_controller.todos_campeonatos, methods=['GET'])
    app.add_url_rule('/api/relatorios/classificacao-campeonato/<int:id_campeonato>', endpoint='classificacao_campeonato', view_func=relatorio_controller.classificacao_campeonato, methods=['GET'])
    app.add_url_rule('/api/relatorios/ranking-duplas', endpoint='ranking_duplas', view_func=relatorio_controller.ranking_duplas, methods=['GET'])
    app.add_url_rule('/api/relatorios/inscritos-campeonato/<int:id_campeonato>', endpoint='inscritos_campeonato', view_func=relatorio_controller.inscritos_campeonato, methods=['GET'])
    app.add_url_rule('/api/relatorios/historico-usuario/<int:id_usuario>', endpoint='historico_usuario', view_func=relatorio_controller.historico_usuario, methods=['GET'])
    app.add_url_rule('/api/relatorios/quadras-mais-utilizadas', endpoint='quadras_mais_utilizadas', view_func=relatorio_controller.quadras_mais_utilizadas, methods=['GET'])
    app.add_url_rule('/api/relatorios/resumo-admin', endpoint='resumo_admin', view_func=relatorio_controller.resumo_admin, methods=['GET'])