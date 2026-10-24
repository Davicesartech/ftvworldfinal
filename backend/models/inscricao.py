from models.db_instance import db, serializar, preparar_dados, hoje
from sqlalchemy.exc import IntegrityError


class Inscricao(db.Model):
    __tablename__ = 'inscricoes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.String(50), default='ativa')  # ativa ou cancelada
    data_inscricao = db.Column(db.Date, default=hoje)
    id_campeonato = db.Column(db.Integer, db.ForeignKey('campeonatos.id'))
    id_dupla = db.Column(db.Integer, db.ForeignKey('duplas.id'))

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Inscricao(**preparar_dados(Inscricao, dados))
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
        return Inscricao.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Inscricao, id)

    @staticmethod
    def atualizar(id, dados):
        inscricao = db.session.get(Inscricao, id)
        if not inscricao:
            return None
        for campo, valor in preparar_dados(Inscricao, dados).items():
            setattr(inscricao, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return inscricao

    @staticmethod
    def deletar(id):
        inscricao = db.session.get(Inscricao, id)
        if not inscricao:
            return False
        db.session.delete(inscricao)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True