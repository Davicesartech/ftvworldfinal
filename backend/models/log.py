from models.db_instance import db, serializar, preparar_dados, agora
from sqlalchemy.exc import IntegrityError


class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_hora = db.Column(db.DateTime, default=agora)
    quem = db.Column(db.String(150))
    acao = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Log(**preparar_dados(Log, dados))
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
        return Log.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Log, id)

    @staticmethod
    def atualizar(id, dados):
        log = db.session.get(Log, id)
        if not log:
            return None
        for campo, valor in preparar_dados(Log, dados).items():
            setattr(log, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return log

    @staticmethod
    def deletar(id):
        log = db.session.get(Log, id)
        if not log:
            return False
        db.session.delete(log)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True