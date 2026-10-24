# services da dupla

from models import Dupla, Inscricao, Usuario
from repositories.dupla_repository import DuplaRepository
from repositories.inscricao_repository import InscricaoRepository
from repositories.solicitacao_repository import SolicitacaoRepository
from services.campeonato_service import recalcular_vagas
from services.comum import como_inteiro, eh_admin, exigir_login, primeiro_nome, registrar_log


def formar_dupla(nome, id1, id2):
    # regras pra nascer uma dupla (usada ao criar direto e ao aceitar uma solicitacao)
    if id1 == id2:
        raise ValueError("um jogador não pode formar dupla consigo mesmo")
    j1, j2 = Usuario.buscar_por_id(id1), Usuario.buscar_por_id(id2)
    if not j1 or not j2:
        raise ValueError("jogador não encontrado")
    if 'dono' in (j1.tipo, j2.tipo):
        raise ValueError("donos de quadra não participam de duplas")
    if DuplaRepository.buscar_ativa_do_usuario(id1) or DuplaRepository.buscar_ativa_do_usuario(id2):
        raise ValueError("um dos jogadores já está em uma dupla ativa")
    # o nome da dupla e sempre: primeiro nome do jogador 1 + primeiro nome do jogador 2
    nome = f"{primeiro_nome(j1)} & {primeiro_nome(j2)}"
    categoria = j1.nivel if j1.nivel and j1.nivel == j2.nivel else 'livre'
    dupla = Dupla.salvar({'nome': nome, 'id_usuario1': id1, 'id_usuario2': id2,
                          'categoria': categoria, 'ativa': True})
    # quem acabou de formar dupla nao precisa mais das solicitacoes pendentes
    SolicitacaoRepository.cancelar_pendentes_dos_usuarios([id1, id2])
    return dupla


class CriarDuplaService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario)
        id1 = como_inteiro(dados.get('id_usuario1'), 'id_usuario1')
        id2 = como_inteiro(dados.get('id_usuario2'), 'id_usuario2')
        if not (eh_admin(usuario) or usuario.id in (id1, id2)):
            raise PermissionError("você só pode formar uma dupla da qual você faz parte")
        dupla = formar_dupla(dados.get('nome'), id1, id2)
        registrar_log(usuario, f'Formou a dupla "{dupla.nome}"')
        return dupla


class ListarDuplaService:
    @staticmethod
    def executar(usuario=None):
        return Dupla.listar_todos()


class BuscarDuplaPorIdService:
    @staticmethod
    def executar(id):
        return Dupla.buscar_por_id(id)


class AtualizarDuplaService:
    @staticmethod
    def executar(id, dados, usuario=None):
        return Dupla.atualizar(id, dados)


class ExcluirDuplaService:
    @staticmethod
    def executar(id, usuario=None):
        return Dupla.deletar(id)


class DesfazerDuplaService:
    # nao apaga a dupla: cancela as inscricoes ativas e deixa ela inativa (o historico fica)
    @staticmethod
    def executar(id, usuario=None):
        dupla = Dupla.buscar_por_id(id)
        if not dupla:
            return None
        if not (eh_admin(usuario) or (usuario and usuario.id in (dupla.id_usuario1, dupla.id_usuario2))):
            raise PermissionError("só quem faz parte da dupla pode desfazê-la")
        campeonatos = set()
        for inscricao in InscricaoRepository.listar_ativas_da_dupla(id):
            Inscricao.atualizar(inscricao.id, {'status': 'cancelada'})
            campeonatos.add(inscricao.id_campeonato)
        Dupla.atualizar(id, {'ativa': False})
        for id_campeonato in campeonatos:
            recalcular_vagas(id_campeonato)
        registrar_log(usuario, f'Desfez a dupla "{dupla.nome}"')
        return dupla