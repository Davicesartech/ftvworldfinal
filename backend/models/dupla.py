from models.db_instance import db, serializar, preparar_dados
from sqlalchemy.exc import IntegrityError


class Dupla(db.Model):
    __tablename__ = 'duplas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100))
    id_usuario1 = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    id_usuario2 = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    categoria = db.Column(db.String(50))
    ativa = db.Column(db.Boolean, default=True)  # dupla desfeita fica inativa (historico preservado)

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Dupla(**preparar_dados(Dupla, dados))
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
        return Dupla.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Dupla, id)

    @staticmethod
    def atualizar(id, dados):
        dupla = db.session.get(Dupla, id)
        if not dupla:
            return None
        for campo, valor in preparar_dados(Dupla, dados).items():
            setattr(dupla, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return dupla

    @staticmethod
    def deletar(id):
        dupla = db.session.get(Dupla, id)
        if not dupla:
            return False
        db.session.delete(dupla)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True