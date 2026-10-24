from models.db_instance import db, serializar, preparar_dados, hoje
from sqlalchemy.exc import IntegrityError


class Solicitacao(db.Model):
    __tablename__ = 'solicitacoes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_de = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # quem enviou
    id_para = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # quem recebeu (so ele aceita ou recusa)
    status = db.Column(db.String(50), default='pendente')  # pendente, aceita, recusada ou cancelada
    data_solicitacao = db.Column(db.Date, default=hoje)

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Solicitacao(**preparar_dados(Solicitacao, dados))
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
        return Solicitacao.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Solicitacao, id)

    @staticmethod
    def atualizar(id, dados):
        solicitacao = db.session.get(Solicitacao, id)
        if not solicitacao:
            return None
        for campo, valor in preparar_dados(Solicitacao, dados).items():
            setattr(solicitacao, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return solicitacao

    @staticmethod
    def deletar(id):
        solicitacao = db.session.get(Solicitacao, id)
        if not solicitacao:
            return False
        db.session.delete(solicitacao)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True