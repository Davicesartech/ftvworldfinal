# services da partida (so quem criou o campeonato registra o placar)

from models import Campeonato, Partida, Quadra
from repositories.inscricao_repository import InscricaoRepository
from services.comum import PLACAR_MAXIMO, como_inteiro, exigir_login, exigir_dono_ou_admin, registrar_log


def validar_partida(camp, d1, d2, p1, p2):
    if d1 == d2:
        raise ValueError("as duas duplas precisam ser diferentes")
    ativas = {i.id_dupla for i in InscricaoRepository.listar_ativas_do_campeonato(camp.id)}
    if d1 not in ativas or d2 not in ativas:
        raise ValueError("as duas duplas precisam estar inscritas no campeonato")
    # placar vai ate 18: quem faz 18 vence e a outra dupla fica com no maximo 17
    if not (0 <= p1 <= PLACAR_MAXIMO and 0 <= p2 <= PLACAR_MAXIMO) or max(p1, p2) != PLACAR_MAXIMO or p1 == p2:
        raise ValueError(f"placar inválido: o jogo vai até {PLACAR_MAXIMO} (uma dupla faz {PLACAR_MAXIMO} e a outra, no máximo {PLACAR_MAXIMO - 1})")
    return d1 if p1 > p2 else d2  # dupla vencedora


class CriarPartidaService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario)
        camp = Campeonato.buscar_por_id(como_inteiro(dados.get('id_campeonato'), 'id_campeonato'))
        if not camp:
            raise ValueError("campeonato não encontrado")
        exigir_dono_ou_admin(camp.id_dono, usuario, "só quem criou o campeonato pode registrar partidas")
        d1 = como_inteiro(dados.get('id_dupla1'), 'id_dupla1')
        d2 = como_inteiro(dados.get('id_dupla2'), 'id_dupla2')
        p1 = como_inteiro(dados.get('placar_dupla1'), 'placar_dupla1')
        p2 = como_inteiro(dados.get('placar_dupla2'), 'placar_dupla2')
        vencedora = validar_partida(camp, d1, d2, p1, p2)
        if dados.get('id_quadra') and not Quadra.buscar_por_id(como_inteiro(dados['id_quadra'], 'id_quadra')):
            raise ValueError("quadra não encontrada")
        novos = {campo: dados[campo] for campo in ('fase', 'data_hora', 'id_quadra') if campo in dados}
        novos.update(id_campeonato=camp.id, id_dupla1=d1, id_dupla2=d2, placar_dupla1=p1,
                     placar_dupla2=p2, id_dupla_vencedora=vencedora, status='finalizada')
        partida = Partida.salvar(novos)
        registrar_log(usuario, f'Registrou uma partida em "{camp.nome}"')
        return partida


class ListarPartidaService:
    @staticmethod
    def executar(usuario=None):
        return Partida.listar_todos()


class BuscarPartidaPorIdService:
    @staticmethod
    def executar(id):
        return Partida.buscar_por_id(id)


class AtualizarPartidaService:
    @staticmethod
    def executar(id, dados, usuario=None):
        partida = Partida.buscar_por_id(id)
        if not partida:
            return None
        camp = Campeonato.buscar_por_id(partida.id_campeonato)
        exigir_dono_ou_admin(camp.id_dono if camp else None, usuario, "só quem criou o campeonato pode editar partidas")
        # mistura o que ja estava salvo com o que veio, e confere tudo de novo
        d1 = como_inteiro(dados.get('id_dupla1', partida.id_dupla1), 'id_dupla1')
        d2 = como_inteiro(dados.get('id_dupla2', partida.id_dupla2), 'id_dupla2')
        p1 = como_inteiro(dados.get('placar_dupla1', partida.placar_dupla1), 'placar_dupla1')
        p2 = como_inteiro(dados.get('placar_dupla2', partida.placar_dupla2), 'placar_dupla2')
        vencedora = validar_partida(camp, d1, d2, p1, p2)
        novos = {campo: dados[campo] for campo in ('fase', 'data_hora', 'id_quadra') if campo in dados}
        novos.update(id_dupla1=d1, id_dupla2=d2, placar_dupla1=p1, placar_dupla2=p2, id_dupla_vencedora=vencedora)
        return Partida.atualizar(id, novos)


class ExcluirPartidaService:
    @staticmethod
    def executar(id, usuario=None):
        partida = Partida.buscar_por_id(id)
        if not partida:
            return False
        camp = Campeonato.buscar_por_id(partida.id_campeonato)
        exigir_dono_ou_admin(camp.id_dono if camp else None, usuario, "só quem criou o campeonato pode excluir partidas")
        return Partida.deletar(id)