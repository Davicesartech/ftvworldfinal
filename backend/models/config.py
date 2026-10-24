import json

from models.db_instance import db, TextoLongo


class Config(db.Model):
    # configuracoes do site (ex.: imagens do banner). a chave eh o proprio id
    # e o valor eh guardado como texto JSON, entao pode ser texto, numero, objeto...
    __tablename__ = 'config'

    chave = db.Column(db.String(50), primary_key=True)
    valor = db.Column(TextoLongo)

    def valor_python(self):
        try:
            return json.loads(self.valor) if self.valor else None
        except ValueError:
            return self.valor

    def to_dict(self):
        return {"chave": self.chave, "valor": self.valor_python()}

    @staticmethod
    def listar_todos():
        return Config.query.all()

    @staticmethod
    def buscar_por_chave(chave):
        return db.session.get(Config, chave)

    @staticmethod
    def salvar(chave, valor):
        # cria a chave se nao existir, senao atualiza
        config = db.session.get(Config, chave)
        if not config:
            config = Config(chave=chave)
            db.session.add(config)
        config.valor = json.dumps(valor, ensure_ascii=False)
        db.session.commit()
        return config

    @staticmethod
    def deletar(chave):
        config = db.session.get(Config, chave)
        if not config:
            return False
        db.session.delete(config)
        db.session.commit()
        return True