from models.db_instance import db, serializar, preparar_dados, agora
from sqlalchemy.exc import IntegrityError


class Candidato(db.Model):
    __tablename__ = 'candidatos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True)  # uma candidatura por jogador
    mensagem = db.Column(db.String(255))
    data_criacao = db.Column(db.DateTime, default=agora)

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Candidato(**preparar_dados(Candidato, dados))
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
        return Candidato.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Candidato, id)

    @staticmethod
    def atualizar(id, dados):
        candidato = db.session.get(Candidato, id)
        if not candidato:
            return None
        for campo, valor in preparar_dados(Candidato, dados).items():
            setattr(candidato, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return candidato

    @staticmethod
    def deletar(id):
        candidato = db.session.get(Candidato, id)
        if not candidato:
            return False
        db.session.delete(candidato)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True