# apoio compartilhado pelos services: constantes, regex e funcoes de permissao/validacao
#
# padrao dos erros (a controller traduz pra resposta HTTP):
#   ValueError      -> dado invalido ou regra de negocio quebrada (400; no excluir, 409)
#   PermissionError -> a pessoa nao pode fazer isso (403)
#   retorno None    -> nao encontrou o registro (404)
#
# todo "executar" recebe tambem o usuario logado (ou None) pra checar permissao

import re

from models import Log, Notificacao

REGEX_EMAIL = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')
REGEX_LINK = re.compile(r'^https?://\S+$', re.IGNORECASE)
REGEX_CHAVE = re.compile(r'^[a-z0-9_-]{1,50}$')

TIPOS_USUARIO = ('jogador', 'professor', 'dono')
NIVEIS = ('iniciante', 'intermediário', 'avançado')
CATEGORIAS = NIVEIS + ('livre',)
PERNAS = ('direita', 'esquerda', 'ambas')
SEXOS = ('feminino', 'masculino')
GENEROS_CAMPEONATO = ('masculino', 'feminino', 'misto')
PLACAR_MAXIMO = 18  # a partida vai ate 18 pontos
MODOS_QUADRA = ('campeonato', 'aluguel', 'ambos')
STATUS_CAMPEONATO = ('aberto', 'encerrado')


def eh_admin(usuario):
    return bool(usuario and usuario.adm)


def exigir_login(usuario, mensagem="faça login para continuar"):
    if not usuario:
        raise PermissionError(mensagem)


def exigir_dono_ou_admin(id_dono, usuario, mensagem):
    if not (eh_admin(usuario) or (usuario and usuario.id == id_dono)):
        raise PermissionError(mensagem)


def como_inteiro(valor, campo="id"):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} inválido")


def como_numero(valor, campo):
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} inválido")


def primeiro_nome(usuario):
    return (usuario.nome or 'Jogador').split()[0]


def registrar_log(usuario, acao):
    # trilha de auditoria que o painel admin mostra
    try:
        Log.salvar({'quem': usuario.nome if usuario else 'Sistema', 'acao': acao[:255]})
    except ValueError:
        pass  # log nunca pode derrubar a acao principal


def notificar(id_usuario, mensagem):
    try:
        Notificacao.salvar({'id_usuario': id_usuario, 'mensagem': mensagem[:255]})
    except ValueError:
        pass  # notificacao tambem nao pode derrubar a acao principal