-- roda isso no phpmyadmin (aba SQL, banco ftvworld) UMA vez, SO SE o banco ja existia
-- (o db.create_all do python cria tabelas novas, mas NAO adiciona coluna em tabela que ja existe)
-- se o banco for novo, nao precisa rodar: o python ja cria a coluna sozinho
-- rode UMA vez: se rodar de novo vai dar erro de "coluna duplicada" no ALTER

-- tipo do campeonato: masculino, feminino ou misto (os que ja existem viram misto)
ALTER TABLE campeonatos ADD COLUMN genero VARCHAR(20) DEFAULT 'misto';
UPDATE campeonatos SET genero = 'misto' WHERE genero IS NULL;

-- nome das duplas ja existentes: primeiro nome do jogador 1 & primeiro nome do jogador 2
UPDATE duplas d
JOIN usuarios u1 ON u1.id = d.id_usuario1
JOIN usuarios u2 ON u2.id = d.id_usuario2
SET d.nome = CONCAT(SUBSTRING_INDEX(TRIM(u1.nome), ' ', 1), ' & ', SUBSTRING_INDEX(TRIM(u2.nome), ' ', 1));
