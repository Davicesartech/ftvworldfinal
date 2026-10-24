# consultas especiais da solicitacao de dupla
# o CRUD simples fica direto na model Solicitacao

from sqlalchemy import and_, or_

from models import db, Solicitacao


class SolicitacaoRepository:

    @staticmethod
    def listar_do_usuario(id_usuario):
        # so as que a pessoa enviou ou recebeu, mais novas primeiro
        return Solicitacao.query.filter(
            or_(Solicitacao.id_de == id_usuario, Solicitacao.id_para == id_usuario)
        ).order_by(Solicitacao.id.desc()).all()

    @staticmethod
    def buscar_pendente_entre(id_a, id_b):
        # pendente em qualquer direcao (a -> b ou b -> a)
        return Solicitacao.query.filter(
            Solicitacao.status == 'pendente',
            or_(and_(Solicitacao.id_de == id_a, Solicitacao.id_para == id_b),
                and_(Solicitacao.id_de == id_b, Solicitacao.id_para == id_a))
        ).first()

    @staticmethod
    def cancelar_pendentes_dos_usuarios(ids):
        # todas as pendentes enviadas ou recebidas por esses usuarios viram "cancelada"
        total = Solicitacao.query.filter(
            Solicitacao.status == 'pendente',
            or_(Solicitacao.id_de.in_(ids), Solicitacao.id_para.in_(ids))
        ).update({'status': 'cancelada'}, synchronize_session='fetch')
        db.session.commit()
        return total