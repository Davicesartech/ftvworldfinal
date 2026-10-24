# services dos relatorios (funcionalidades mais avançadas)
# cada um chama o repository, que é quem fala com o banco de verdade
# as regras de permissao dos relatorios ficam AQUI (a controller so recebe a requisicao e devolve a resposta):
#   PermissionError -> a controller traduz para 403

from repositories.relatorio_repository import RelatorioRepository
from services.comum import eh_admin, exigir_login


class CampeonatosDisponiveisService:
    @staticmethod
    def executar(categoria=None, nivel=None):
        return RelatorioRepository.campeonatos_disponiveis(categoria, nivel)


class TodosCampeonatosService:
    @staticmethod
    def executar(nivel=None):
        return RelatorioRepository.campeonatos(nivel)


class ClassificacaoCampeonatoService:
    @staticmethod
    def executar(id_campeonato):
        return RelatorioRepository.classificacao_campeonato(id_campeonato)


class RankingDuplasService:
    @staticmethod
    def executar():
        return RelatorioRepository.ranking_duplas()


class InscritosCampeonatoService:
    @staticmethod
    def executar(id_campeonato, usuario=None):
        exigir_login(usuario)
        return RelatorioRepository.inscritos_campeonato(id_campeonato)


class HistoricoPartidasUsuarioService:
    @staticmethod
    def executar(id_usuario, usuario=None):
        exigir_login(usuario)
        # cada um so ve o proprio historico (o admin ve o de todo mundo)
        if not (eh_admin(usuario) or usuario.id == id_usuario):
            raise PermissionError("você só pode ver o seu próprio histórico")
        return RelatorioRepository.historico_partidas_usuario(id_usuario)


class QuadrasMaisUtilizadasService:
    @staticmethod
    def executar():
        return RelatorioRepository.quadras_mais_utilizadas()


class ResumoAdminService:
    @staticmethod
    def executar(usuario=None):
        if not eh_admin(usuario):
            raise PermissionError("acesso restrito ao administrador")
        linhas = RelatorioRepository.resumo_admin()
        return linhas[0] if linhas else {}