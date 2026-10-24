# resposta de erro padrao das controllers: {"erro": "..."} + codigo HTTP

from flask import jsonify


def resposta_erro(mensagem, codigo):
    return jsonify({"erro": mensagem}), codigo
