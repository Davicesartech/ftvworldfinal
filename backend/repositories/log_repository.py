# consultas especiais do log (a trilha de auditoria so eh lida pela API)
# gravar e buscar por id ficam direto na model Log

from models import Log


class LogRepository:

    @staticmethod
    def listar_recentes(limite=500):
        return Log.query.order_by(Log.id.desc()).limit(limite).all()