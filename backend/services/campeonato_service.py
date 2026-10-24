# services do campeonato (so dono de quadra cria; so quem criou edita)

from models import Campeonato
from repositories.inscricao_repository import InscricaoRepository
from services.comum import (
    CATEGORIAS, GENEROS_CAMPEONATO, STATUS_CAMPEONATO,
    como_inteiro, como_numero, exigir_login, exigir_dono_ou_admin, registrar_log,
)

CAMPOS_CAMPEONATO = {'nome', 'descricao', 'data', 'horario', 'categoria', 'nivel', 'genero', 'vagas_total',
                     'cidade', 'premio', 'foto', 'status'}


def recalcular_vagas(id_campeonato):
    # vagas disponiveis = limite - duplas com inscricao ativa
    campeonato = Campeonato.buscar_por_id(id_campeonato)
    if campeonato and campeonato.vagas_total is not None:
        vagas = max(0, campeonato.vagas_total - InscricaoRepository.contar_ativas(id_campeonato))
        Campeonato.atualizar(id_campeonato, {'vagas_disponiveis': vagas})


def validar_campeonato(novos, criacao):
    if criacao and not (novos.get('nome') or '').strip():
        raise ValueError("o nome do campeonato é obrigatório")
    if criacao or 'vagas_total' in novos:
        novos['vagas_total'] = como_inteiro(novos.get('vagas_total'), 'limite de duplas')
        if novos['vagas_total'] < 2:
            raise ValueError("o limite deve ser de pelo menos 2 duplas")
    if novos.get('premio') not in (None, '') and como_numero(novos['premio'], 'premiação') < 0:
        raise ValueError("a premiação não pode ser negativa")
    if novos.get('nivel') and novos['nivel'] not in CATEGORIAS:
        raise ValueError("categoria (nível) inválida")
    if novos.get('status') and novos['status'] not in STATUS_CAMPEONATO:
        raise ValueError("status inválido: use aberto ou encerrado")
    if criacao and not novos.get('genero'):
        novos['genero'] = 'misto'
    if novos.get('genero') and novos['genero'] not in GENEROS_CAMPEONATO:
        raise ValueError("tipo inválido: use masculino, feminino ou misto")


class CriarCampeonatoService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario, "entre na sua conta para criar campeonatos")
        if not (usuario.tipo == 'dono' or usuario.adm):
            raise PermissionError("somente donos de quadra podem criar campeonatos")
        novos = {campo: dados[campo] for campo in CAMPOS_CAMPEONATO if campo in dados}
        validar_campeonato(novos, criacao=True)
        novos['status'] = novos.get('status') or 'aberto'
        novos['id_dono'] = usuario.id
        novos['vagas_disponiveis'] = novos['vagas_total']
        campeonato = Campeonato.salvar(novos)
        registrar_log(usuario, f'Criou o campeonato "{campeonato.nome}"')
        return campeonato


class ListarCampeonatoService:
    @staticmethod
    def executar(usuario=None):
        return Campeonato.listar_todos()


class BuscarCampeonatoPorIdService:
    @staticmethod
    def executar(id):
        return Campeonato.buscar_por_id(id)


class AtualizarCampeonatoService:
    @staticmethod
    def executar(id, dados, usuario=None):
        campeonato = Campeonato.buscar_por_id(id)
        if not campeonato:
            return None
        exigir_dono_ou_admin(campeonato.id_dono, usuario, "você só pode editar campeonatos que criou")
        novos = {campo: dados[campo] for campo in CAMPOS_CAMPEONATO if campo in dados}
        validar_campeonato(novos, criacao=False)
        if 'vagas_total' in novos and novos['vagas_total'] < InscricaoRepository.contar_ativas(id):
            raise ValueError("já existem mais duplas inscritas do que esse limite")
        status_antes = campeonato.status
        campeonato = Campeonato.atualizar(id, novos)
        recalcular_vagas(id)
        if campeonato.status != status_antes:
            acao = 'Encerrou' if campeonato.status == 'encerrado' else 'Reabriu'
            registrar_log(usuario, f'{acao} o campeonato "{campeonato.nome}"')
        return campeonato


class ExcluirCampeonatoService:
    @staticmethod
    def executar(id, usuario=None):
        campeonato = Campeonato.buscar_por_id(id)
        if not campeonato:
            return False
        exigir_dono_ou_admin(campeonato.id_dono, usuario, "você só pode excluir campeonatos que criou")
        nome = campeonato.nome
        sucesso = Campeonato.deletar(id)
        if sucesso:
            registrar_log(usuario, f'Excluiu o campeonato "{nome}"')
        return sucesso