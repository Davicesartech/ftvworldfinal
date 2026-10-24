import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from werkzeug.security import generate_password_hash

from models import db, Usuario
from models.db_instance import agora
from controllers.rotas import registrar_todas_as_rotas

app = Flask(__name__)
CORS(app)

# banco: por padrao o mysql local do phpmyadmin (igual ao modelo).
# se precisar de outro, defina a variavel de ambiente DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/ftvworld')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.ensure_ascii = False  # acentos saem normais no JSON

db.init_app(app)


def garantir_admin():
    # cria o administrador na primeira execucao, SE as variaveis ADMIN_EMAIL e ADMIN_SENHA existirem
    # (a senha nunca fica escrita no codigo)
    email = (os.environ.get('ADMIN_EMAIL') or '').strip().lower()
    senha = os.environ.get('ADMIN_SENHA') or ''
    if not email or len(senha) < 6 or Usuario.query.filter_by(email=email).first():
        return
    Usuario.salvar({'nome': 'Administrador', 'email': email, 'senha': generate_password_hash(senha),
                    'tipo': 'jogador', 'adm': True, 'aceitou_termos': True, 'data_aceite_termos': agora()})
    print(f'Administrador criado: {email}')


with app.app_context():
    db.create_all()
    garantir_admin()

registrar_todas_as_rotas(app)


@app.errorhandler(404)
def rota_nao_encontrada(erro):
    return jsonify({"erro": "rota não encontrada"}), 404


@app.errorhandler(405)
def metodo_nao_permitido(erro):
    return jsonify({"erro": "método não permitido nesta rota"}), 405


@app.errorhandler(Exception)
def erro_inesperado(erro):
    # 404/405 e afins seguem com os handlers acima; o resto (banco fora do ar, pacote grande demais...)
    # vira JSON, que eh o formato que o front sabe mostrar
    if isinstance(erro, HTTPException):
        return erro
    db.session.rollback()
    app.logger.exception('erro inesperado')
    detalhe = f' ({type(erro).__name__}: {erro})' if app.debug else ''
    return jsonify({"erro": "erro interno no servidor. Veja o terminal do Flask." + detalhe}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)