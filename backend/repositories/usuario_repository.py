# consultas especiais do usuario
# o CRUD simples (salvar, listar_todos, buscar_por_id, atualizar, deletar) fica direto na model Usuario

from sqlalchemy import or_

from models import Usuario, Notificacao, Candidato, Solicitacao


class UsuarioRepository:

    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def buscar_outro_com_email(email, id_ignorado):
        # alguem que nao seja o proprio usuario ja usa esse e-mail?
        return Usuario.query.filter(Usuario.email == email, Usuario.id != id_ignorado).first()

    @staticmethod
    def remover_vinculos(id):
        # notificacoes, candidatura e solicitacoes pertencem so a essa pessoa: saem junto com a conta
        Notificacao.query.filter_by(id_usuario=id).delete(synchronize_session=False)
        Candidato.query.filter_by(id_usuario=id).delete(synchronize_session=False)
        Solicitacao.query.filter(or_(Solicitacao.id_de == id, Solicitacao.id_para == id)).delete(synchronize_session=False)