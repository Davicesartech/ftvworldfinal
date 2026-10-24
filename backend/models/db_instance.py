# instancia do SQLAlchemy usada em todas as models
# fica separada num arquivo proprio pra evitar import circular
# aqui tambem ficam as funcoes de apoio que todas as models usam
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import LONGTEXT

db = SQLAlchemy()

# texto grande (fotos em base64 etc.): LONGTEXT no mysql, TEXT nos outros bancos
TextoLongo = db.Text().with_variant(LONGTEXT(), 'mysql')


def agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hoje():
    return agora().date()


def serializar(valor):
    # transforma data, hora e decimal em algo que o jsonify entende
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def preparar_dados(modelo, dados):
    # deixa passar so os campos que existem na tabela (nunca o id) e converte
    # texto em data/hora/numero, que eh como o JSON chega do front
    resultado = {}
    for coluna in modelo.__table__.columns:
        if coluna.name not in dados or coluna.primary_key:
            continue
        valor = dados[coluna.name]
        try:
            tipo = coluna.type.python_type
        except NotImplementedError:
            tipo = str
        try:
            if valor == '' and tipo is not str:
                valor = None
            elif isinstance(valor, str) and tipo is datetime:
                valor = datetime.fromisoformat(valor.replace('Z', '+00:00')).replace(tzinfo=None)
            elif isinstance(valor, str) and tipo is date:
                valor = date.fromisoformat(valor[:10])
            elif isinstance(valor, str) and tipo is time:
                valor = time.fromisoformat(valor)
            elif tipo is int and valor is not None and not isinstance(valor, (int, bool)):
                valor = int(valor)
            elif tipo is Decimal and valor is not None and not isinstance(valor, Decimal):
                valor = Decimal(str(valor))
        except (ValueError, InvalidOperation):
            raise ValueError(f"valor inválido para o campo '{coluna.name}'")
        resultado[coluna.name] = valor
    return resultado
