# consultas especiais da inscricao
# o CRUD simples fica direto na model Inscricao

from models import Inscricao


class InscricaoRepository:

    @staticmethod
    def contar_ativas(id_campeonato):
        return Inscricao.query.filter_by(id_campeonato=id_campeonato, status='ativa').count()

    @staticmethod
    def listar_ativas_do_campeonato(id_campeonato):
        return Inscricao.query.filter_by(id_campeonato=id_campeonato, status='ativa').all()

    @staticmethod
    def listar_ativas_da_dupla(id_dupla):
        return Inscricao.query.filter_by(id_dupla=id_dupla, status='ativa').all()

    @staticmethod
    def buscar_ativa(id_campeonato, id_dupla):
        return Inscricao.query.filter_by(id_campeonato=id_campeonato, id_dupla=id_dupla, status='ativa').first()