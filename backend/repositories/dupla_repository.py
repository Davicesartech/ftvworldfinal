# consultas especiais da dupla
# o CRUD simples fica direto na model Dupla

from sqlalchemy import or_

from models import Dupla


class DuplaRepository:

    @staticmethod
    def buscar_ativa_do_usuario(id_usuario):
        return Dupla.query.filter(
            Dupla.ativa.is_(True),
            or_(Dupla.id_usuario1 == id_usuario, Dupla.id_usuario2 == id_usuario)
        ).first()