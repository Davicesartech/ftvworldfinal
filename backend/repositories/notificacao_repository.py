# consultas especiais da notificacao
# o CRUD simples fica direto na model Notificacao

from models import db, Notificacao


class NotificacaoRepository:

    @staticmethod
    def listar_do_usuario(id_usuario):
        # as mais novas primeiro
        return Notificacao.query.filter_by(id_usuario=id_usuario).order_by(Notificacao.id.desc()).all()

    @staticmethod
    def marcar_todas_como_lidas(id_usuario):
        total = Notificacao.query.filter_by(id_usuario=id_usuario, lida=False).update({'lida': True})
        db.session.commit()
        return total