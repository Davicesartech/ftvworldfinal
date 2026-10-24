# login por token JWT (assinado) - substitui o dicionario de tokens em memoria
# o token carrega o id do usuario e a validade, e so o servidor consegue assina-lo
# quando o usuario faz login ganha um token; nas proximas requisicoes ele manda
# esse token no cabecalho "Authorization: Bearer <token>", sem precisar mandar a senha de novo
#
# a chave de assinatura vem da variavel de ambiente FTVWORLD_SECRET.
# se ela nao existir, uma chave aleatoria eh criada uma vez e guardada em backend/.ftvworld_secret
# (assim os logins continuam valendo quando o servidor reinicia)
#
# obs: o logout guarda o token numa lista em memoria (tokens_revogados).
# em producao isso ficaria no banco ou no Redis.

import os
import secrets
import time

import jwt


def _carregar_segredo():
    # 1) variavel de ambiente (o ideal em producao)
    # 2) senao, uma chave sorteada UMA vez e guardada em backend/.ftvworld_secret.
    #    sem isso, o modo debug do Flask (que reinicia o servidor a cada arquivo salvo) sorteava
    #    uma chave nova toda vez e derrubava o login de todo mundo
    do_ambiente = os.environ.get('FTVWORLD_SECRET')
    if do_ambiente:
        return do_ambiente
    arquivo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.ftvworld_secret')
    try:
        with open(arquivo, encoding='utf-8') as f:
            guardado = f.read().strip()
        if guardado:
            return guardado
    except OSError:
        pass  # ainda nao existe (primeira execucao): cria logo abaixo
    novo = secrets.token_hex(32)
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(novo)
    except OSError:
        pass  # pasta sem permissao de escrita: vale so enquanto o servidor estiver ligado (comportamento antigo)
    return novo


SEGREDO = _carregar_segredo()
VALIDADE_SEGUNDOS = 8 * 60 * 60  # 8 horas

tokens_revogados = set()  # ids (jti) dos tokens que fizeram logout


def _limpar(token):
    # aceita "Bearer abc123" ou so "abc123"
    if not token:
        return None
    token = token.strip()
    if token.lower().startswith('bearer '):
        token = token[7:].strip()
    return token or None


def gerar_token(id_usuario):
    agora = int(time.time())
    dados = {
        'sub': str(id_usuario),
        'iat': agora,
        'exp': agora + VALIDADE_SEGUNDOS,
        'jti': secrets.token_hex(8),
    }
    return jwt.encode(dados, SEGREDO, algorithm='HS256')


def usuario_do_token(token):
    token = _limpar(token)
    if not token:
        return None
    try:
        dados = jwt.decode(token, SEGREDO, algorithms=['HS256'])
    except jwt.PyJWTError:
        return None
    if dados.get('jti') in tokens_revogados:
        return None
    try:
        return int(dados['sub'])
    except (KeyError, ValueError):
        return None


def remover_token(token):
    token = _limpar(token)
    if not token:
        return
    try:
        dados = jwt.decode(token, SEGREDO, algorithms=['HS256'])
    except jwt.PyJWTError:
        return
    tokens_revogados.add(dados.get('jti'))
