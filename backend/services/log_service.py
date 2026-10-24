# services do log (so leitura: a trilha de auditoria nao pode ser alterada pela API)

from models import Log
from repositories.log_repository import LogRepository


class ListarLogService:
    @staticmethod
    def executar(usuario=None):
        return LogRepository.listar_recentes(500)


class BuscarLogPorIdService:
    @staticmethod
    def executar(id):
        return Log.buscar_por_id(id)