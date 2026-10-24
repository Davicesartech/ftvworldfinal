# junta o registro de rotas de todas as controllers num lugar so
# o app.py chama apenas registrar_todas_as_rotas(app)

from controllers.usuario_controller import registrar_rotas_usuario
from controllers.campeonato_controller import registrar_rotas_campeonato
from controllers.quadra_controller import registrar_rotas_quadra
from controllers.inscricao_controller import registrar_rotas_inscricao
from controllers.dupla_controller import registrar_rotas_dupla
from controllers.partida_controller import registrar_rotas_partida
from controllers.notificacao_controller import registrar_rotas_notificacao
from controllers.solicitacao_controller import registrar_rotas_solicitacao
from controllers.candidato_controller import registrar_rotas_candidato
from controllers.log_controller import registrar_rotas_log
from controllers.config_controller import registrar_rotas_config
from controllers.relatorio_controller import registrar_rotas_relatorios
from controllers.login_controller import registrar_rotas_login
from controllers.perfil_controller import registrar_rotas_perfil


def registrar_todas_as_rotas(app):
    registrar_rotas_usuario(app)
    registrar_rotas_campeonato(app)
    registrar_rotas_quadra(app)
    registrar_rotas_inscricao(app)
    registrar_rotas_dupla(app)
    registrar_rotas_partida(app)
    registrar_rotas_notificacao(app)
    registrar_rotas_solicitacao(app)
    registrar_rotas_candidato(app)
    registrar_rotas_log(app)
    registrar_rotas_config(app)
    registrar_rotas_relatorios(app)
    registrar_rotas_login(app)
    registrar_rotas_perfil(app)
