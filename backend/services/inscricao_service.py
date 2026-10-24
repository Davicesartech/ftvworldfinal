# services da inscricao

from models import Campeonato, Dupla, Inscricao, Usuario
from repositories.inscricao_repository import InscricaoRepository
from services.campeonato_service import recalcular_vagas
from services.comum import como_inteiro, eh_admin, exigir_login, notificar


def nivel_compativel(campeonato, dupla):
    # campeonato "livre" aceita qualquer um; senao os dois jogadores precisam ter o nivel dele
    if campeonato.nivel in (None, '', 'livre'):
        return True
    jogadores = [Usuario.buscar_por_id(dupla.id_usuario1), Usuario.buscar_por_id(dupla.id_usuario2)]
    return all(j and j.nivel == campeonato.nivel for j in jogadores)


def genero_compativel(campeonato, dupla):
    # masculino so aceita jogadores masculinos, feminino so femininos, misto aceita os dois
    genero = campeonato.genero or 'misto'
    if genero == 'misto':
        return True
    jogadores = [Usuario.buscar_por_id(dupla.id_usuario1), Usuario.buscar_por_id(dupla.id_usuario2)]
    return all(j and j.sexo == genero for j in jogadores)


class CriarInscricaoService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario)
        campeonato = Campeonato.buscar_por_id(como_inteiro(dados.get('id_campeonato'), 'id_campeonato'))
        dupla = Dupla.buscar_por_id(como_inteiro(dados.get('id_dupla'), 'id_dupla'))
        if not campeonato or not dupla:
            raise ValueError("campeonato ou dupla não encontrados")
        if not (eh_admin(usuario) or usuario.id in (dupla.id_usuario1, dupla.id_usuario2)):
            raise PermissionError("só quem faz parte da dupla pode inscrevê-la")
        if not dupla.ativa:
            raise ValueError("esta dupla não está ativa")
        if campeonato.status != 'aberto':
            raise ValueError("este campeonato está encerrado")
        if InscricaoRepository.contar_ativas(campeonato.id) >= (campeonato.vagas_total or 0):
            raise ValueError("o limite de duplas já foi atingido")
        if InscricaoRepository.buscar_ativa(campeonato.id, dupla.id):
            raise ValueError("esta dupla já está inscrita neste campeonato")
        if not nivel_compativel(campeonato, dupla):
            raise ValueError("a categoria do campeonato não é compatível com o nível dos jogadores")
        if not genero_compativel(campeonato, dupla):
            if campeonato.genero == 'masculino':
                raise ValueError("este campeonato é masculino: os dois jogadores da dupla precisam ser do sexo masculino")
            raise ValueError("este campeonato é feminino: as duas jogadoras da dupla precisam ser do sexo feminino")
        inscricao = Inscricao.salvar({'id_campeonato': campeonato.id, 'id_dupla': dupla.id, 'status': 'ativa'})
        recalcular_vagas(campeonato.id)
        if campeonato.id_dono:
            notificar(campeonato.id_dono, f'A dupla "{dupla.nome}" se inscreveu em "{campeonato.nome}".')
        return inscricao


class ListarInscricaoService:
    @staticmethod
    def executar(usuario=None):
        return Inscricao.listar_todos()


class BuscarInscricaoPorIdService:
    @staticmethod
    def executar(id):
        return Inscricao.buscar_por_id(id)


class AtualizarInscricaoService:
    @staticmethod
    def executar(id, dados, usuario=None):
        inscricao = Inscricao.atualizar(id, dados)
        if inscricao:
            recalcular_vagas(inscricao.id_campeonato)
        return inscricao


class ExcluirInscricaoService:
    @staticmethod
    def executar(id, usuario=None):
        inscricao = Inscricao.buscar_por_id(id)
        id_campeonato = inscricao.id_campeonato if inscricao else None
        sucesso = Inscricao.deletar(id)
        if sucesso:
            recalcular_vagas(id_campeonato)
        return sucesso


class CancelarInscricaoService:
    @staticmethod
    def executar(id, usuario=None):
        inscricao = Inscricao.buscar_por_id(id)
        if not inscricao:
            return None
        dupla = Dupla.buscar_por_id(inscricao.id_dupla)
        campeonato = Campeonato.buscar_por_id(inscricao.id_campeonato)
        pode = eh_admin(usuario) or (usuario and (
            (dupla and usuario.id in (dupla.id_usuario1, dupla.id_usuario2))
            or (campeonato and usuario.id == campeonato.id_dono)))
        if not pode:
            raise PermissionError("só a dupla, o dono do campeonato ou o admin podem cancelar a inscrição")
        if inscricao.status != 'ativa':
            raise ValueError("esta inscrição já foi cancelada")
        inscricao = Inscricao.atualizar(id, {'status': 'cancelada'})
        recalcular_vagas(inscricao.id_campeonato)
        return inscricao