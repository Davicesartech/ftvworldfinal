-- roda isso no phpmyadmin (aba SQL) UMA vez, antes de ligar o servidor pela primeira vez
-- as tabelas o python cria sozinho (db.create_all) quando o app.py roda
-- depois rode o arquivo procedures.sql, dentro do banco ftvworld

CREATE DATABASE IF NOT EXISTS ftvworld CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
