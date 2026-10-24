# services da quadra (cada quadra pertence a um dono)

from models import Quadra
from services.comum import (
    MODOS_QUADRA, como_numero, eh_admin, exigir_login, exigir_dono_ou_admin, registrar_log,
)

CAMPOS_QUADRA = {'nome', 'endereco', 'cidade', 'numero_quadras', 'contato', 'modo', 'preco',
                 'descricao', 'foto'}


def validar_quadra(novos, atual=None):
    # "atual" eh a quadra que ja existe (na edicao): campos que nao vieram valem o que ja estava salvo
    modo = novos.get('modo') or (atual.modo if atual else 'ambos')
    preco = novos['preco'] if 'preco' in novos else (atual.preco if atual else 0)
    if atual is None and not (novos.get('nome') or '').strip():
        raise ValueError("o nome da quadra é obrigatório")
    if modo not in MODOS_QUADRA:
        raise ValueError("uso inválido: escolha campeonato, aluguel ou ambos")
    if modo == 'campeonato':
        novos['preco'] = 0  # quadra so de campeonato nao tem aluguel
    elif como_numero(preco or 0, 'preço') <= 0:
        raise ValueError("informe o preço do aluguel por hora")
    elif 'preco' in novos:
        novos['preco'] = como_numero(preco, 'preço')


class CriarQuadraService:
    @staticmethod
    def executar(dados, usuario=None):
        exigir_login(usuario, "entre na sua conta para cadastrar quadras")
        if not (usuario.tipo == 'dono' or usuario.adm):
            raise PermissionError("somente donos de quadra podem cadastrar quadras")
        novos = {campo: dados[campo] for campo in CAMPOS_QUADRA if campo in dados}
        novos.setdefault('modo', 'ambos')
        validar_quadra(novos)
        # o admin pode cadastrar em nome de um dono; senao a quadra fica com quem criou
        novos['id_responsavel'] = dados.get('id_responsavel') if eh_admin(usuario) and dados.get('id_responsavel') else usuario.id
        quadra = Quadra.salvar(novos)
        registrar_log(usuario, f'Cadastrou a quadra "{quadra.nome}"')
        return quadra


class ListarQuadraService:
    @staticmethod
    def executar(usuario=None):
        return Quadra.listar_todos()


class BuscarQuadraPorIdService:
    @staticmethod
    def executar(id):
        return Quadra.buscar_por_id(id)


class AtualizarQuadraService:
    @staticmethod
    def executar(id, dados, usuario=None):
        quadra = Quadra.buscar_por_id(id)
        if not quadra:
            return None
        exigir_dono_ou_admin(quadra.id_responsavel, usuario, "você só pode editar as suas quadras")
        novos = {campo: dados[campo] for campo in CAMPOS_QUADRA if campo in dados}
        validar_quadra(novos, atual=quadra)
        return Quadra.atualizar(id, novos)


class ExcluirQuadraService:
    @staticmethod
    def executar(id, usuario=None):
        quadra = Quadra.buscar_por_id(id)
        if not quadra:
            return False
        exigir_dono_ou_admin(quadra.id_responsavel, usuario, "você só pode excluir as suas quadras")
        return Quadra.deletar(id)