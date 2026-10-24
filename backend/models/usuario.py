from models.db_instance import db, serializar, preparar_dados, agora, TextoLongo
from sqlalchemy.exc import IntegrityError


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)  # guarda so o hash, nunca a senha pura
    telefone = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    nivel = db.Column(db.String(50))
    cidade = db.Column(db.String(100))
    tipo = db.Column(db.String(20), default='jogador')  # jogador, professor ou dono (de quadra)
    perna = db.Column(db.String(20))  # perna dominante: direita, esquerda ou ambas
    sexo = db.Column(db.String(20))  # feminino ou masculino (aparece no perfil)
    habilidades = db.Column(db.String(255))  # separadas por virgula
    local = db.Column(db.String(150))  # onde o professor da aula
    valor = db.Column(db.Numeric(10, 2))  # valor da aula (professor)
    bio = db.Column(db.Text)
    foto = db.Column(TextoLongo)
    video = db.Column(TextoLongo)
    video_url = db.Column(db.String(255))
    adm = db.Column(db.Boolean, default=False)
    bloqueado = db.Column(db.Boolean, default=False)

    # registro do aceite da LGPD - precisa guardar isso como prova do consentimento
    aceitou_termos = db.Column(db.Boolean, default=False)
    data_aceite_termos = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=agora)

    CAMPOS_PUBLICOS = ('id', 'nome', 'telefone', 'nivel', 'cidade', 'tipo', 'sexo', 'perna', 'habilidades',
                       'local', 'valor', 'bio', 'foto', 'video', 'video_url')

    def to_dict(self):
        # a senha (hash) nunca sai da API
        d = {c.name: serializar(getattr(self, c.name)) for c in self.__table__.columns if c.name != 'senha'}
        d['habilidades'] = [h for h in (self.habilidades or '').split(',') if h]
        return d

    def to_public_dict(self):
        # versao que qualquer usuario logado pode ver (sem e-mail, nascimento, flags de admin etc.)
        d = self.to_dict()
        return {campo: d[campo] for campo in Usuario.CAMPOS_PUBLICOS}

    @staticmethod
    def salvar(dados):
        novo = Usuario(**preparar_dados(Usuario, dados))
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
        return Usuario.query.all()

    @staticmethod
    def buscar_por_id(id):
        return db.session.get(Usuario, id)

    @staticmethod
    def atualizar(id, dados):
        usuario = db.session.get(Usuario, id)
        if not usuario:
            return None
        for campo, valor in preparar_dados(Usuario, dados).items():
            setattr(usuario, campo, valor)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("dados inválidos: confira os ids informados e os campos que não podem repetir")
        return usuario

    @staticmethod
    def deletar(id):
        usuario = db.session.get(Usuario, id)
        if not usuario:
            return False
        db.session.delete(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            # o banco recusou porque tem outro registro vinculado a este
            # (por causa da ForeignKey) - desfaz a tentativa e avisa com uma mensagem clara
            db.session.rollback()
            raise ValueError("não é possível excluir: existem outros registros vinculados a este")
        return True