-- roda isso no phpmyadmin (aba SQL, banco ftvworld) SO SE o banco ja existia com o backend ANTIGO
-- (se for banco novo, nao precisa rodar isso - o python ja cria tudo certo sozinho)
-- as tabelas novas (solicitacoes, candidatos, logs, config) o python cria sozinho
-- rode UMA vez: se rodar de novo vai dar erro de "coluna duplicada"

ALTER TABLE usuarios
    ADD COLUMN data_nascimento DATE,
    ADD COLUMN tipo VARCHAR(20) DEFAULT 'jogador',
    ADD COLUMN perna VARCHAR(20),
    ADD COLUMN habilidades VARCHAR(255),
    ADD COLUMN local VARCHAR(150),
    ADD COLUMN valor DECIMAL(10,2),
    ADD COLUMN bio TEXT,
    ADD COLUMN foto LONGTEXT,
    ADD COLUMN video LONGTEXT,
    ADD COLUMN video_url VARCHAR(255),
    ADD COLUMN adm BOOLEAN DEFAULT FALSE,
    ADD COLUMN bloqueado BOOLEAN DEFAULT FALSE,
    ADD COLUMN data_criacao DATETIME;

ALTER TABLE campeonatos
    ADD COLUMN premio DECIMAL(10,2) DEFAULT 0,
    ADD COLUMN foto LONGTEXT,
    ADD COLUMN id_dono INT,
    ADD CONSTRAINT fk_campeonato_dono FOREIGN KEY (id_dono) REFERENCES usuarios(id);

ALTER TABLE quadras
    ADD COLUMN modo VARCHAR(20) DEFAULT 'ambos',
    ADD COLUMN preco DECIMAL(10,2) DEFAULT 0,
    ADD COLUMN descricao TEXT,
    ADD COLUMN foto LONGTEXT;

ALTER TABLE duplas
    ADD COLUMN nome VARCHAR(100),
    ADD COLUMN ativa BOOLEAN DEFAULT TRUE;

ALTER TABLE partidas
    ADD COLUMN id_dupla_vencedora INT,
    ADD CONSTRAINT fk_partida_vencedora FOREIGN KEY (id_dupla_vencedora) REFERENCES duplas(id);

-- descobre quem ganhou as partidas que ja existiam
UPDATE partidas
   SET id_dupla_vencedora = CASE
         WHEN placar_dupla1 > placar_dupla2 THEN id_dupla1
         WHEN placar_dupla2 > placar_dupla1 THEN id_dupla2
       END
 WHERE id_dupla_vencedora IS NULL;

-- o sistema novo usa os status 'ativa' e 'cancelada' nas inscricoes.
-- veja quais status voce tinha: SELECT DISTINCT status FROM inscricoes;
-- se eram todas validas, pode padronizar assim:
-- UPDATE inscricoes SET status = 'ativa' WHERE status IS NULL OR status <> 'cancelada';

-- AVISO SOBRE SENHAS: as senhas antigas estavam sem hash. nao precisa converter:
-- o login aceita a senha antiga uma vez e ja troca por hash automaticamente.
