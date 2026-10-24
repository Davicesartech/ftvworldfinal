-- roda isso no phpmyadmin (aba SQL, banco ftvworld) SE o banco ja existia
-- antes da gente adicionar as ForeignKey de verdade
--
-- ATENCAO: se voce ja tem dados de teste com IDs que nao existem de verdade
-- (por exemplo, uma partida com id_dupla1 = 999, mas a dupla 999 nao existe),
-- o ALTER TABLE abaixo vai FALHAR com uma mensagem tipo "Cannot add foreign key
-- constraint". Nesse caso, rode primeiro os SELECTs de diagnostico (a segunda
-- parte deste arquivo) pra achar e corrigir esses dados problematicos.


-- ============================================================
-- PARTE 1: adicionar as ForeignKey de verdade
-- ============================================================

ALTER TABLE quadras
    ADD CONSTRAINT fk_quadra_responsavel
    FOREIGN KEY (id_responsavel) REFERENCES usuarios(id);

ALTER TABLE inscricoes
    ADD CONSTRAINT fk_inscricao_campeonato
    FOREIGN KEY (id_campeonato) REFERENCES campeonatos(id);

ALTER TABLE inscricoes
    ADD CONSTRAINT fk_inscricao_dupla
    FOREIGN KEY (id_dupla) REFERENCES duplas(id);

ALTER TABLE duplas
    ADD CONSTRAINT fk_dupla_usuario1
    FOREIGN KEY (id_usuario1) REFERENCES usuarios(id);

ALTER TABLE duplas
    ADD CONSTRAINT fk_dupla_usuario2
    FOREIGN KEY (id_usuario2) REFERENCES usuarios(id);

ALTER TABLE partidas
    ADD CONSTRAINT fk_partida_campeonato
    FOREIGN KEY (id_campeonato) REFERENCES campeonatos(id);

ALTER TABLE partidas
    ADD CONSTRAINT fk_partida_dupla1
    FOREIGN KEY (id_dupla1) REFERENCES duplas(id);

ALTER TABLE partidas
    ADD CONSTRAINT fk_partida_dupla2
    FOREIGN KEY (id_dupla2) REFERENCES duplas(id);

ALTER TABLE partidas
    ADD CONSTRAINT fk_partida_quadra
    FOREIGN KEY (id_quadra) REFERENCES quadras(id);

ALTER TABLE notificacoes
    ADD CONSTRAINT fk_notificacao_usuario
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id);


-- ============================================================
-- PARTE 2 (SO RODAR SE A PARTE 1 DER ERRO):
-- diagnostico pra achar dados "orfaos" (que apontam pra um ID que nao existe)
-- ============================================================

-- quadras com id_responsavel que nao existe em usuarios
-- SELECT * FROM quadras WHERE id_responsavel IS NOT NULL
--   AND id_responsavel NOT IN (SELECT id FROM usuarios);

-- inscricoes com id_campeonato ou id_dupla que nao existem
-- SELECT * FROM inscricoes WHERE id_campeonato IS NOT NULL
--   AND id_campeonato NOT IN (SELECT id FROM campeonatos);
-- SELECT * FROM inscricoes WHERE id_dupla IS NOT NULL
--   AND id_dupla NOT IN (SELECT id FROM duplas);

-- duplas com id_usuario1 ou id_usuario2 que nao existem
-- SELECT * FROM duplas WHERE id_usuario1 IS NOT NULL
--   AND id_usuario1 NOT IN (SELECT id FROM usuarios);
-- SELECT * FROM duplas WHERE id_usuario2 IS NOT NULL
--   AND id_usuario2 NOT IN (SELECT id FROM usuarios);

-- partidas com id_campeonato, id_dupla1, id_dupla2 ou id_quadra que nao existem
-- SELECT * FROM partidas WHERE id_campeonato IS NOT NULL
--   AND id_campeonato NOT IN (SELECT id FROM campeonatos);
-- SELECT * FROM partidas WHERE id_dupla1 IS NOT NULL
--   AND id_dupla1 NOT IN (SELECT id FROM duplas);
-- SELECT * FROM partidas WHERE id_dupla2 IS NOT NULL
--   AND id_dupla2 NOT IN (SELECT id FROM duplas);
-- SELECT * FROM partidas WHERE id_quadra IS NOT NULL
--   AND id_quadra NOT IN (SELECT id FROM quadras);

-- notificacoes com id_usuario que nao existe
-- SELECT * FROM notificacoes WHERE id_usuario IS NOT NULL
--   AND id_usuario NOT IN (SELECT id FROM usuarios);

-- se algum SELECT acima devolver linhas, o jeito mais simples de corrigir
-- (pra dados de teste, sem valor real) e colocar NULL nesse campo, exemplo:
-- UPDATE partidas SET id_dupla1 = NULL WHERE id = <id_da_linha_problematica>;
