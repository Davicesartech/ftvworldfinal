# services do candidato ("encontre sua dupla": jogadores que estao procurando parceiro)

from models import Candidato
from models.db_instance import agora
from repositories.candidato_repository import CandidatoRepository
from services.comum import exigir_login


class CriarCandidatoService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario)
        if usuario.tipo == 'dono':
            raise ValueError("donos de quadra não participam de duplas")
        mensagem = (dados.get('mensagem') or '').strip()
        if len(mensagem) > 255:
            raise ValueError("o recado pode ter no máximo 255 caracteres")
        existente = CandidatoRepository.buscar_por_usuario(usuario.id)
        if existente:  # publicar de novo so atualiza o recado
            return Candidato.atualizar(existente.id, {'mensagem': mensagem, 'data_criacao': agora()})
        return Candidato.salvar({'id_usuario': usuario.id, 'mensagem': mensagem})


class ListarCandidatoService:
    @staticmethod
    def executar(usuario=None):
        return Candidato.listar_todos()


class BuscarCandidatoPorIdService:
    @staticmethod
    def executar(id):
        return Candidato.buscar_por_id(id)


class AtualizarCandidatoService:
    @staticmethod
    def executar(id, dados, usuario=None):
        return Candidato.atualizar(id, dados)


class ExcluirCandidatoService:
    @staticmethod
    def executar(id, usuario=None):
        return Candidato.deletar(id)


class ExcluirMinhaCandidaturaService:
    @staticmethod
    def executar(usuario=None):
        exigir_login(usuario)
        candidato = CandidatoRepository.buscar_por_usuario(usuario.id)
        return Candidato.deletar(candidato.id) if candidato else False