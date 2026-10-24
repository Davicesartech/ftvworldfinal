# consultas especiais do candidato ("encontre sua dupla")
# o CRUD simples (salvar, listar_todos, buscar_por_id, atualizar, deletar) fica direto na model Candidato

from models import Candidato


class CandidatoRepository:

    @staticmethod
    def buscar_por_usuario(id_usuario):
        return Candidato.query.filter_by(id_usuario=id_usuario).first()