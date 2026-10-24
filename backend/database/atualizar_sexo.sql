-- roda isso no phpmyadmin (aba SQL, banco ftvworld) UMA vez, SO SE o banco ja existia
-- (o db.create_all do python cria tabelas novas, mas NAO adiciona coluna em tabela que ja existe)
-- se o banco for novo, nao precisa rodar: o python ja cria a coluna sozinho
-- rode UMA vez: se rodar de novo vai dar erro de "coluna duplicada"

ALTER TABLE usuarios ADD COLUMN sexo VARCHAR(20);
