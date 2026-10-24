from models.db_instance import db, serializar, preparar_dados, hoje
from sqlalchemy.exc import IntegrityError


class Notificacao(db.Model):
    __tablename__ = 'notificacoes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mensagem = db.Column(db.String(255), nullable=False)
    lida = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.Date, default=hoje)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Notificacao(**preparar_dados(Notificacao, dados))
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
        return Notificacao.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Notificacao, id)

    @staticmethod
    def atualizar(id, dados):
        notificacao = db.session.get(Notificacao, id)
        if not notificacao:
            return None
        for campo, valor in preparar_dados(Notificacao, dados).items():
            setattr(notificacao, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return notificacao

    @staticmethod
    def deletar(id):
        notificacao = db.session.get(Notificacao, id)
        if not notificacao:
            return False
        db.session.delete(notificacao)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True