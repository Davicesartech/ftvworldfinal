from models.db_instance import db, serializar, preparar_dados
from sqlalchemy.exc import IntegrityError


class Partida(db.Model):
    __tablename__ = 'partidas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fase = db.Column(db.String(50))
    placar_dupla1 = db.Column(db.Integer, default=0)
    placar_dupla2 = db.Column(db.Integer, default=0)
    data_hora = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='finalizada')
    id_campeonato = db.Column(db.Integer, db.ForeignKey('campeonatos.id'))
    id_dupla1 = db.Column(db.Integer, db.ForeignKey('duplas.id'))
    id_dupla2 = db.Column(db.Integer, db.ForeignKey('duplas.id'))
    id_dupla_vencedora = db.Column(db.Integer, db.ForeignKey('duplas.id'))  # calculada pelo service (sem empate)
    id_quadra = db.Column(db.Integer, db.ForeignKey('quadras.id'))

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Partida(**preparar_dados(Partida, dados))
        db.session.add(novo)
        try:
            db.session.commit()
        except IntegrityError:
            # id de outra tabela que nao existe, e-mail repetido etc.
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return novo

    @staticmethod
    def listar_todos():
        return Partida.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Partida, id)

    @staticmethod
    def atualizar(id, dados):
        partida = db.session.get(Partida, id)
        if not partida:
            return None
        for campo, valor in preparar_dados(Partida, dados).items():
            setattr(partida, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return partida

    @staticmethod
    def deletar(id):
        partida = db.session.get(Partida, id)
        if not partida:
            return False
        db.session.delete(partida)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True