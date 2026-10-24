"""
Popula o banco do FTV World com dados de demonstração.

Como usar (com o MySQL ligado e dentro da pasta backend):
    venv\\Scripts\\python.exe seed.py

Pode rodar quantas vezes quiser: o que já existe não é duplicado.
Todos os usuários de exemplo têm a senha 123456 (admin: admin123).
"""
import random
import unicodedata
from datetime import date, datetime, time, timedelta

from werkzeug.security import generate_password_hash

from app import app
from models import (Campeonato, Candidato, Dupla, Inscricao, Notificacao,
                    Partida, Quadra, Solicitacao, Usuario, db)

SENHA_PADRAO = '123456'
HASH = generate_password_hash(SENHA_PADRAO)
rnd = random.Random(2026)          # sempre os mesmos dados
HOJE = date.today()
AGORA = datetime.now().replace(microsecond=0)


def slug(txt):
    s = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode()
    return '.'.join(s.lower().replace('&', ' ').split())


def telefone(cidade):
    ddd = {'Rio de Janeiro': '21', 'Santos': '13', 'Florianópolis': '48', 'Fortaleza': '85'}.get(cidade, '31')
    return f'({ddd}) 9{rnd.randint(1000, 9999)}-{rnd.randint(1000, 9999)}'


def nascimento():
    return date(rnd.randint(1985, 2004), rnd.randint(1, 12), rnd.randint(1, 28))


def cadastro():
    """Data de criação espalhada pelos últimos 5 meses (alimenta os gráficos do admin)."""
    return AGORA - timedelta(days=rnd.randint(1, 150), hours=rnd.randint(0, 23))


# ---------------------------------------------------------------- usuários
# (nome, sexo, nível, cidade, perna, habilidades, bio)
JOGADORES = [
    ('Lucas Almeida', 'masculino', 'avançado', 'Belo Horizonte', 'direita', 'Chapa,Shark', 'Jogo desde 2015. Gosto de ataque agressivo e quadra rápida.'),
    ('Rafael Costa', 'masculino', 'avançado', 'Contagem', 'esquerda', 'Defesa,Ombro', 'Especialista em defesa de fundo. Já ganhei dois torneios regionais.'),
    ('Gustavo Pereira', 'masculino', 'avançado', 'Rio de Janeiro', 'direita', 'Chapa,Peito', 'Carioca da Barra, treino todo dia de manhã.'),
    ('Thiago Martins', 'masculino', 'avançado', 'Rio de Janeiro', 'ambas', 'Shark,Ombro', 'Ex-jogador de vôlei de quadra, migrei para a areia.'),
    ('Bruno Carvalho', 'masculino', 'intermediário', 'Belo Horizonte', 'direita', 'Peito,Defesa', 'Jogo nos fins de semana na Pampulha.'),
    ('Felipe Rocha', 'masculino', 'intermediário', 'Contagem', 'direita', 'Ombro', 'Evoluindo rápido, focado em melhorar o saque.'),
    ('Matheus Ribeiro', 'masculino', 'iniciante', 'Belo Horizonte', 'direita', 'Defesa', 'Comecei há 6 meses e já viciei.'),
    ('Diego Barbosa', 'masculino', 'iniciante', 'Contagem', 'esquerda', 'Peito', 'Quero aprender e fazer amigos na areia.'),
    ('André Nascimento', 'masculino', 'intermediário', 'Santos', 'direita', 'Chapa,Defesa', 'Jogo em Santos, aberto a viajar para torneios.'),
    ('Rodrigo Teixeira', 'masculino', 'intermediário', 'Santos', 'ambas', 'Ombro,Peito', 'Disciplina e treino, sempre.'),
    ('Vinícius Moreira', 'masculino', 'iniciante', 'Florianópolis', 'direita', 'Defesa', 'Aprendendo com os vídeos e treinando aos sábados.'),
    ('Leandro Cardoso', 'masculino', 'intermediário', 'Belo Horizonte', 'direita', 'Chapa,Ombro', 'Procuro dupla para o circuito mineiro.'),
    ('Pedro Henrique Dias', 'masculino', 'iniciante', 'Contagem', 'direita', 'Peito', 'Novo no esporte, procuro alguém paciente para treinar.'),
    ('João Victor Lima', 'masculino', 'avançado', 'Belo Horizonte', 'esquerda', 'Shark,Chapa', 'Canhoto, ataque forte. Busco dupla competitiva.'),
    ('Eduardo Pinto', 'masculino', 'intermediário', 'Fortaleza', 'direita', 'Defesa,Ombro', 'Jogo em Fortaleza, treino na Praia do Futuro.'),
    ('Camila Souza', 'feminino', 'intermediário', 'Belo Horizonte', 'direita', 'Defesa,Peito', 'Jogo há 3 anos e amo campeonato.'),
    ('Juliana Ferreira', 'feminino', 'intermediário', 'Belo Horizonte', 'direita', 'Ombro,Chapa', 'Foco em evoluir o ataque.'),
    ('Beatriz Gomes', 'feminino', 'iniciante', 'Contagem', 'direita', 'Defesa', 'Comecei no futevôlei este ano.'),
    ('Larissa Araújo', 'feminino', 'iniciante', 'Contagem', 'esquerda', 'Peito', 'Aprendendo e me divertindo.'),
    ('Mariana Santos', 'feminino', 'avançado', 'Rio de Janeiro', 'direita', 'Chapa,Shark', 'Competidora, treino 5x por semana.'),
    ('Fernanda Lopes', 'feminino', 'avançado', 'Rio de Janeiro', 'ambas', 'Defesa,Ombro', 'Já joguei circuito carioca.'),
    ('Amanda Castro', 'feminino', 'intermediário', 'Florianópolis', 'direita', 'Peito,Defesa', 'Jogo em Floripa, adoro jogo misto.'),
    ('Letícia Monteiro', 'feminino', 'intermediário', 'Belo Horizonte', 'direita', 'Ombro', 'Procuro dupla feminina para torneios.'),
    ('Gabriela Freitas', 'feminino', 'iniciante', 'Santos', 'direita', 'Defesa', 'Quero treinar e jogar meu primeiro campeonato.'),
    ('Isabela Correia', 'feminino', 'avançado', 'Belo Horizonte', 'esquerda', 'Chapa,Peito', 'Canhota, jogo de ataque. Busco dupla fixa.'),
    ('Carolina Mendes', 'feminino', 'intermediário', 'Contagem', 'direita', 'Defesa,Ombro', 'Disponível à noite e nos fins de semana.'),
    ('Renata Vieira', 'feminino', 'iniciante', 'Belo Horizonte', 'direita', 'Peito', 'Recomeçando depois de uma pausa, bora jogar!'),
    ('Natália Ramos', 'feminino', 'intermediário', 'Fortaleza', 'direita', 'Shark,Defesa', 'Jogo em Fortaleza, procuro dupla para o Aberto.'),
]

# (nome, sexo, cidade, local da aula, valor da aula, bio)
PROFESSORES = [
    ('Marcelo Andrade', 'masculino', 'Belo Horizonte', 'Arena Pampulha Beach, Belo Horizonte', 120, 'Professor há 8 anos. Aulas individuais e em grupo, do iniciante ao avançado.'),
    ('Patrícia Lemos', 'feminino', 'Rio de Janeiro', 'Praia de Copacabana, Posto 5', 150, 'Ex-atleta profissional. Foco em técnica de ataque e defesa.'),
    ('Rogério Tavares', 'masculino', 'Santos', 'Santos Beach Sports, Santos', 100, 'Aulas para iniciantes e preparação para campeonatos.'),
    ('Aline Duarte', 'feminino', 'Contagem', 'Praia Clube Contagem', 90, 'Aulas para mulheres e turmas mistas. Primeira aula experimental.'),
]

# (nome, sexo, cidade)
DONOS = [
    ('Sérgio Batista', 'masculino', 'Belo Horizonte'),
    ('Cláudia Ribeiro', 'feminino', 'Rio de Janeiro'),
    ('Henrique Matos', 'masculino', 'Santos'),
]

# (nome, endereço, cidade, nº de quadras, modo, preço/hora, descrição, dono)
QUADRAS = [
    ('Arena Pampulha Beach', 'Av. Otacílio Negrão de Lima, 1500 - Pampulha', 'Belo Horizonte', 4, 'ambos', 80, 'Quatro quadras de areia fina, iluminação para jogo noturno, vestiário e bar.', 'Sérgio Batista'),
    ('Praia Clube Contagem', 'Rua das Palmeiras, 320 - Centro', 'Contagem', 3, 'campeonato', 0, 'Espaço dedicado a campeonatos, com arquibancada e estacionamento.', 'Sérgio Batista'),
    ('Arena Copacabana FTV', 'Av. Atlântica, Posto 5 - Copacabana', 'Rio de Janeiro', 6, 'ambos', 120, 'Seis quadras de frente para o mar. Aluguel por hora e torneios aos fins de semana.', 'Cláudia Ribeiro'),
    ('Ipanema Sand Club', 'Rua Vieira Souto, 700 - Ipanema', 'Rio de Janeiro', 2, 'aluguel', 100, 'Quadras para aluguel com aulas disponíveis pela manhã.', 'Cláudia Ribeiro'),
    ('Santos Beach Sports', 'Av. Vicente de Carvalho, 55 - Gonzaga', 'Santos', 3, 'ambos', 90, 'Três quadras, loja de acessórios e lanchonete.', 'Henrique Matos'),
]

ADMIN = ('Administrador FTV', 'admin@ftvworld.com', 'admin123')


def get_usuario(nome, email, **campos):
    u = Usuario.query.filter_by(email=email).first()
    if u:
        return u, False
    u = Usuario(nome=nome, email=email, senha=HASH, aceitou_termos=True,
                data_aceite_termos=AGORA, data_criacao=cadastro(), bloqueado=False, adm=False, **campos)
    db.session.add(u)
    db.session.flush()
    return u, True


def email_de(nome):
    return f'{slug(nome)}@demo.ftvworld.com'


def popular():
    novos = {'usuarios': 0, 'quadras': 0, 'campeonatos': 0, 'duplas': 0, 'inscricoes': 0,
             'partidas': 0, 'candidatos': 0, 'solicitacoes': 0}
    U = {}   # nome -> Usuario

    # administrador de demonstração
    if not Usuario.query.filter_by(email=ADMIN[1]).first():
        db.session.add(Usuario(nome=ADMIN[0], email=ADMIN[1], senha=generate_password_hash(ADMIN[2]),
                               tipo='jogador', adm=True, aceitou_termos=True, data_aceite_termos=AGORA,
                               sexo='masculino', cidade='Belo Horizonte', telefone=telefone('Belo Horizonte')))
        novos['usuarios'] += 1

    for nome, sexo, nivel, cidade, perna, habs, bio in JOGADORES:
        u, criado = get_usuario(nome, email_de(nome), tipo='jogador', sexo=sexo, nivel=nivel, cidade=cidade,
                                perna=perna, habilidades=habs, bio=bio, telefone=telefone(cidade),
                                data_nascimento=nascimento())
        U[nome] = u
        novos['usuarios'] += criado

    for nome, sexo, cidade, local, valor, bio in PROFESSORES:
        u, criado = get_usuario(nome, email_de(nome), tipo='professor', sexo=sexo, cidade=cidade, local=local,
                                valor=valor, bio=bio, telefone=telefone(cidade), data_nascimento=nascimento())
        U[nome] = u
        novos['usuarios'] += criado

    for nome, sexo, cidade in DONOS:
        u, criado = get_usuario(nome, email_de(nome), tipo='dono', sexo=sexo, cidade=cidade,
                                telefone=telefone(cidade), data_nascimento=nascimento())
        U[nome] = u
        novos['usuarios'] += criado

    # ---------------------------------------------------------------- quadras
    Q = {}
    for nome, end, cidade, n, modo, preco, desc, dono in QUADRAS:
        q = Quadra.query.filter_by(nome=nome).first()
        if not q:
            q = Quadra(nome=nome, endereco=end, cidade=cidade, numero_quadras=n, modo=modo, preco=preco,
                       descricao=desc, contato=U[dono].telefone, id_responsavel=U[dono].id)
            db.session.add(q)
            db.session.flush()
            novos['quadras'] += 1
        Q[nome] = q

    # ---------------------------------------------------------------- duplas
    # (nome da dupla, jogador 1, jogador 2)
    DUPLAS = [
        ('Areia Quente', 'Lucas Almeida', 'Rafael Costa'),
        ('Os Tubarões', 'Gustavo Pereira', 'Thiago Martins'),
        ('Ondas do Norte', 'Mariana Santos', 'Fernanda Lopes'),
        ('Sol & Rede', 'Camila Souza', 'Juliana Ferreira'),
        ('Dunas FC', 'Bruno Carvalho', 'Felipe Rocha'),
        ('Chapa Quente', 'André Nascimento', 'Rodrigo Teixeira'),
        ('Maré Alta', 'Beatriz Gomes', 'Larissa Araújo'),
        ('Peito e Raça', 'Matheus Ribeiro', 'Diego Barbosa'),
        ('Mix Beach', 'Vinícius Moreira', 'Amanda Castro'),
    ]
    D = {}
    for nome, a, b in DUPLAS:
        d = Dupla.query.filter_by(nome=nome).first()
        if not d:
            ua, ub = U[a], U[b]
            cat = ua.nivel if ua.nivel == ub.nivel else 'livre'   # mesma regra do sistema
            d = Dupla(nome=nome, id_usuario1=ua.id, id_usuario2=ub.id, categoria=cat, ativa=True)
            db.session.add(d)
            db.session.flush()
            novos['duplas'] += 1
        D[nome] = d

    # ------------------------------------------------------------ campeonatos
    dia = lambda n: HOJE + timedelta(days=n)
    # (nome, nível, cidade, dia (negativo = já começou), hora, vagas, prêmio, status, dono, descrição)
    CAMPS = [
        # --- em andamento (já começaram, ainda abertos) ---
        ('Copa Contagem Intermediário', 'intermediário', 'Contagem', dia(-2), time(9, 0), 8, 2000, 'aberto', 'Sérgio Batista',
         'Campeonato em andamento: fase de grupos nos sábados e domingos. Premiação total de R$ 2.000.'),
        ('Circuito Carioca Avançado', 'avançado', 'Rio de Janeiro', dia(-1), time(10, 0), 8, 5000, 'aberto', 'Cláudia Ribeiro',
         'Em andamento! Jogos todos os dias na Arena Copacabana FTV. Premiação de R$ 5.000.'),
        # --- abertos para inscrição ---
        ('Open Pampulha de Futevôlei', 'iniciante', 'Belo Horizonte', dia(10), time(8, 0), 16, 1500, 'aberto', 'Sérgio Batista',
         'Inscrições abertas para duplas iniciantes. Início às 8h, com café da manhã para os atletas.'),
        ('Torneio Livre de Verão', 'livre', 'Santos', dia(17), time(8, 30), 20, 3000, 'aberto', 'Henrique Matos',
         'Categoria livre: qualquer nível pode se inscrever. Premiação de R$ 3.000 e troféus.'),
        ('Desafio da Areia', 'intermediário', 'Belo Horizonte', dia(24), time(9, 0), 8, 1200, 'aberto', 'Sérgio Batista',
         'Torneio intermediário em formato de eliminatória dupla.'),
        ('Copa Ipanema Iniciantes', 'iniciante', 'Rio de Janeiro', dia(31), time(8, 0), 12, 800, 'aberto', 'Cláudia Ribeiro',
         'Evento para quem está começando. Aulas gratuitas de aquecimento antes dos jogos.'),
        ('Aberto de Fortaleza', 'livre', 'Fortaleza', dia(45), time(16, 0), 16, 4000, 'aberto', 'Henrique Matos',
         'Torneio livre ao entardecer na Praia do Futuro.'),
        # --- encerrados (histórico e ranking) ---
        ('Taça Primavera', 'avançado', 'Rio de Janeiro', dia(-30), time(10, 0), 8, 4500, 'encerrado', 'Cláudia Ribeiro',
         'Campeonato encerrado. Campeões: Areia Quente.'),
        ('Open Inverno BH', 'intermediário', 'Belo Horizonte', dia(-60), time(9, 0), 8, 1800, 'encerrado', 'Sérgio Batista',
         'Campeonato encerrado. Campeões: Sol & Rede.'),
    ]
    C = {}
    for nome, nivel, cidade, d, h, vagas, premio, status, dono, desc in CAMPS:
        c = Campeonato.query.filter_by(nome=nome).first()
        if not c:
            c = Campeonato(nome=nome, nivel=nivel, categoria=nivel, cidade=cidade, data=d, horario=h,
                           vagas_total=vagas, vagas_disponiveis=vagas, premio=premio, status=status,
                           id_dono=U[dono].id, descricao=desc)
            db.session.add(c)
            db.session.flush()
            novos['campeonatos'] += 1
        C[nome] = c

    # ------------------------------------------------------------- inscrições
    INSCR = {
        'Copa Contagem Intermediário': ['Sol & Rede', 'Dunas FC', 'Chapa Quente'],
        'Circuito Carioca Avançado': ['Areia Quente', 'Os Tubarões', 'Ondas do Norte'],
        'Open Pampulha de Futevôlei': ['Maré Alta', 'Peito e Raça'],
        'Torneio Livre de Verão': ['Mix Beach', 'Areia Quente', 'Sol & Rede', 'Peito e Raça'],
        'Desafio da Areia': ['Dunas FC', 'Chapa Quente'],
        'Taça Primavera': ['Areia Quente', 'Os Tubarões', 'Ondas do Norte'],
        'Open Inverno BH': ['Sol & Rede', 'Dunas FC', 'Chapa Quente'],
    }
    for camp, duplas in INSCR.items():
        for nd in duplas:
            if not Inscricao.query.filter_by(id_campeonato=C[camp].id, id_dupla=D[nd].id).first():
                db.session.add(Inscricao(id_campeonato=C[camp].id, id_dupla=D[nd].id, status='ativa',
                                         data_inscricao=C[camp].data - timedelta(days=rnd.randint(7, 20))))
                novos['inscricoes'] += 1
    db.session.flush()
    for c in C.values():   # mesma conta do sistema: vagas = limite - inscrições ativas
        ativas = Inscricao.query.filter_by(id_campeonato=c.id, status='ativa').count()
        c.vagas_disponiveis = max(0, c.vagas_total - ativas)

    # --------------------------------------------------------------- partidas
    # (campeonato, quadra, fase, dupla A, sets A, dupla B, sets B, dias após o início, hora)
    PARTIDAS = [
        ('Copa Contagem Intermediário', 'Praia Clube Contagem', 'Fase de grupos', 'Sol & Rede', 18, 'Dunas FC', 15, 0, 9),
        ('Copa Contagem Intermediário', 'Praia Clube Contagem', 'Fase de grupos', 'Chapa Quente', 9, 'Sol & Rede', 18, 1, 10),
        ('Circuito Carioca Avançado', 'Arena Copacabana FTV', 'Fase de grupos', 'Areia Quente', 18, 'Os Tubarões', 9, 0, 10),
        ('Circuito Carioca Avançado', 'Arena Copacabana FTV', 'Fase de grupos', 'Ondas do Norte', 15, 'Os Tubarões', 18, 1, 11),
        ('Taça Primavera', 'Arena Copacabana FTV', 'Fase de grupos', 'Os Tubarões', 18, 'Ondas do Norte', 15, 0, 10),
        ('Taça Primavera', 'Arena Copacabana FTV', 'Semifinal', 'Areia Quente', 18, 'Ondas do Norte', 9, 1, 10),
        ('Taça Primavera', 'Arena Copacabana FTV', 'Final', 'Areia Quente', 18, 'Os Tubarões', 15, 2, 15),
        ('Open Inverno BH', 'Arena Pampulha Beach', 'Fase de grupos', 'Dunas FC', 9, 'Chapa Quente', 18, 0, 9),
        ('Open Inverno BH', 'Arena Pampulha Beach', 'Semifinal', 'Sol & Rede', 18, 'Chapa Quente', 15, 1, 10),
        ('Open Inverno BH', 'Arena Pampulha Beach', 'Final', 'Sol & Rede', 18, 'Dunas FC', 9, 2, 15),
    ]
    for camp, quadra, fase, a, sa, b, sb, off, hora in PARTIDAS:
        c, da, db_ = C[camp], D[a], D[b]
        if Partida.query.filter_by(id_campeonato=c.id, id_dupla1=da.id, id_dupla2=db_.id, fase=fase).first():
            continue
        quando = datetime.combine(c.data + timedelta(days=off), time(hora, 0))
        db.session.add(Partida(id_campeonato=c.id, id_quadra=Q[quadra].id, fase=fase, id_dupla1=da.id,
                               id_dupla2=db_.id, placar_dupla1=sa, placar_dupla2=sb, data_hora=quando,
                               status='finalizada', id_dupla_vencedora=da.id if sa > sb else db_.id))
        novos['partidas'] += 1

    # ------------------------------------------------- "Encontre sua dupla"
    # jogadores sem dupla que se candidataram a encontrar parceiro(a)
    CANDIDATOS = ['Leandro Cardoso', 'Pedro Henrique Dias', 'João Victor Lima', 'Eduardo Pinto',
                  'Letícia Monteiro', 'Gabriela Freitas', 'Isabela Correia', 'Carolina Mendes',
                  'Renata Vieira', 'Natália Ramos']
    MSG = {
        'Leandro Cardoso': 'Procuro dupla para o circuito mineiro. Treino às terças e quintas.',
        'Pedro Henrique Dias': 'Sou iniciante e quero uma dupla paciente para evoluir juntos.',
        'João Victor Lima': 'Canhoto de ataque, busco dupla competitiva para campeonatos.',
        'Eduardo Pinto': 'Procuro dupla em Fortaleza para o Aberto.',
        'Letícia Monteiro': 'Busco dupla feminina para torneios em BH.',
        'Gabriela Freitas': 'Quero jogar meu primeiro campeonato, alguém topa?',
        'Isabela Correia': 'Procuro dupla fixa, nível avançado, treinos 3x por semana.',
        'Carolina Mendes': 'Disponível à noite e nos fins de semana, vamos treinar?',
        'Renata Vieira': 'Voltando a jogar, quero dupla para treinar sem pressão.',
        'Natália Ramos': 'Dupla para o Aberto de Fortaleza, de preferência feminina.',
    }
    for nome in CANDIDATOS:
        if not Candidato.query.filter_by(id_usuario=U[nome].id).first():
            db.session.add(Candidato(id_usuario=U[nome].id, mensagem=MSG[nome],
                                     data_criacao=AGORA - timedelta(days=rnd.randint(0, 20), hours=rnd.randint(0, 23))))
            novos['candidatos'] += 1

    # solicitações de dupla entre candidatos
    SOL = [('Pedro Henrique Dias', 'Leandro Cardoso', 'pendente'), ('Letícia Monteiro', 'Carolina Mendes', 'pendente'),
           ('Isabela Correia', 'Letícia Monteiro', 'pendente'), ('Natália Ramos', 'Eduardo Pinto', 'recusada'),
           ('Renata Vieira', 'Gabriela Freitas', 'pendente')]
    for de, para, st in SOL:
        if not Solicitacao.query.filter_by(id_de=U[de].id, id_para=U[para].id).first():
            db.session.add(Solicitacao(id_de=U[de].id, id_para=U[para].id, status=st,
                                       data_solicitacao=HOJE - timedelta(days=rnd.randint(0, 6))))
            novos['solicitacoes'] += 1

    db.session.commit()
    return novos


if __name__ == '__main__':
    with app.app_context():
        r = popular()
    print('Dados de exemplo criados:')
    for k, v in r.items():
        print(f'  {k}: {v} novo(s)')
    print('\nLogin de teste: qualquer e-mail abaixo, senha 123456')
    print('  jogador: lucas.almeida@demo.ftvworld.com')
    print('  candidato (sem dupla): leandro.cardoso@demo.ftvworld.com')
    print('  professor: marcelo.andrade@demo.ftvworld.com')
    print('  dono de quadra: sergio.batista@demo.ftvworld.com')
    print('  administrador: admin@ftvworld.com / admin123')
