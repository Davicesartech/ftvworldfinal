from models.db_instance import db, serializar, preparar_dados, TextoLongo
from sqlalchemy.exc import IntegrityError


class Quadra(db.Model):
    __tablename__ = 'quadras'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    numero_quadras = db.Column(db.Integer)
    contato = db.Column(db.String(50))
    modo = db.Column(db.String(20), default='ambos')  # campeonato, aluguel ou ambos
    preco = db.Column(db.Numeric(10, 2), default=0)  # aluguel por hora
    descricao = db.Column(db.Text)
    foto = db.Column(TextoLongo)
    id_responsavel = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Quadra(**preparar_dados(Quadra, dados))
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
        return Quadra.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Quadra, id)

    @staticmethod
    def atualizar(id, dados):
        quadra = db.session.get(Quadra, id)
        if not quadra:
            return None
        for campo, valor in preparar_dados(Quadra, dados).items():
            setattr(quadra, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return quadra

    @staticmethod
    def deletar(id):
        quadra = db.session.get(Quadra, id)
        if not quadra:
            return False
        db.session.delete(quadra)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True