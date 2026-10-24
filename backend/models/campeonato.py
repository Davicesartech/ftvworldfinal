from models.db_instance import db, serializar, preparar_dados, TextoLongo
from sqlalchemy.exc import IntegrityError


class Campeonato(db.Model):
    __tablename__ = 'campeonatos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    data = db.Column(db.Date)
    horario = db.Column(db.Time)
    categoria = db.Column(db.String(50))
    nivel = db.Column(db.String(50))  # iniciante, intermediario, avancado ou livre
    genero = db.Column(db.String(20), default='misto')  # masculino, feminino ou misto (misto aceita os dois)
    vagas_total = db.Column(db.Integer)
    vagas_disponiveis = db.Column(db.Integer)  # recalculado pelo service a cada inscricao
    status = db.Column(db.String(50), default='aberto')  # aberto ou encerrado
    cidade = db.Column(db.String(100))  # usado pra sugerir campeonatos proximos ao usuario
    premio = db.Column(db.Numeric(10, 2), default=0)
    foto = db.Column(TextoLongo)
    id_dono = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # dono de quadra que criou o campeonato

    def to_dict(self):
        return {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns}

    @staticmethod
    def salvar(dados):
        novo = Campeonato(**preparar_dados(Campeonato, dados))
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
        return Campeonato.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Campeonato, id)

    @staticmethod
    def atualizar(id, dados):
        campeonato = db.session.get(Campeonato, id)
        if not campeonato:
            return None
        for campo, valor in preparar_dados(Campeonato, dados).items():
            setattr(campeonato, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return campeonato

    @staticmethod
    def deletar(id):
        campeonato = db.session.get(Campeonato, id)
        if not campeonato:
            return False
        db.session.delete(campeonato)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True