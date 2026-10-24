# repository das consultas mais complexas do projeto
# aqui a gente chama as procedures que estao criadas la no banco (mysql)
# controller e service nao encostam em SQL, só essa classe aqui

from datetime import date, datetime, time
from decimal import Decimal
from models import db


def formatar_valor(valor):
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        # contagens e somas voltam como Decimal: se for numero inteiro, devolve int
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    return valor


def formatar_linha(linha):
    return {chave: formatar_valor(valor) for chave, valor in linha.items()}


class RelatorioRepository:

    @staticmethod
    def chamar_procedure(nome_procedure, parametros=None):
        parametros = parametros or []
        conexao = db.engine.raw_connection()
        try:
            cursor = conexao.cursor()
            cursor.callproc(nome_procedure, parametros)

            colunas = [col[0] for col in cursor.description] if cursor.description else []
            linhas = cursor.fetchall()

            resultado = [formatar_linha(dict(zip(colunas, linha))) for linha in linhas]

            cursor.close()
            conexao.commit()
            return resultado
        finally:
            conexao.close()

    @staticmethod
    def campeonatos_disponiveis(categoria=None, nivel=None):
        return RelatorioRepository.chamar_procedure('sp_campeonatos_disponiveis', [categoria, nivel])

    @staticmethod
    def campeonatos(nivel=None):
        return RelatorioRepository.chamar_procedure('sp_campeonatos', [nivel])

    @staticmethod
    def classificacao_campeonato(id_campeonato):
        return RelatorioRepository.chamar_procedure('sp_classificacao_campeonato', [id_campeonato])

    @staticmethod
    def ranking_duplas():
        return RelatorioRepository.chamar_procedure('sp_ranking_duplas', [])

    @staticmethod
    def inscritos_campeonato(id_campeonato):
        return RelatorioRepository.chamar_procedure('sp_inscritos_campeonato', [id_campeonato])

    @staticmethod
    def historico_partidas_usuario(id_usuario):
        return RelatorioRepository.chamar_procedure('sp_historico_partidas_usuario', [id_usuario])

    @staticmethod
    def quadras_mais_utilizadas():
        return RelatorioRepository.chamar_procedure('sp_quadras_mais_utilizadas', [])

    @staticmethod
    def resumo_admin():
        return RelatorioRepository.chamar_procedure('sp_resumo_admin', [])
