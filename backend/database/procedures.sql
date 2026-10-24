-- procedures das funcionalidades avançadas do ftvworld
-- roda tudo isso no phpmyadmin, dentro do banco ftvworld, aba SQL
-- (pode rodar de novo quando quiser: cada procedure é apagada e recriada)

DELIMITER $$

-- campeonatos abertos que ainda tem vaga (com a quantidade de vagas livres)
DROP PROCEDURE IF EXISTS sp_campeonatos_disponiveis $$
CREATE PROCEDURE sp_campeonatos_disponiveis(
    IN p_categoria VARCHAR(50),
    IN p_nivel VARCHAR(50)
)
BEGIN
    SELECT c.*, c.vagas_total - COUNT(i.id) AS vagas
    FROM campeonatos c
    LEFT JOIN inscricoes i ON i.id_campeonato = c.id AND i.status = 'ativa'
    WHERE c.status = 'aberto'
      AND (p_categoria IS NULL OR p_categoria = '' OR c.categoria = p_categoria)
      AND (p_nivel IS NULL OR p_nivel = '' OR c.nivel = p_nivel)
    GROUP BY c.id
    HAVING vagas > 0
    ORDER BY c.data ASC;
END $$


-- TODOS os campeonatos (abertos e encerrados) com as vagas livres de cada um
DROP PROCEDURE IF EXISTS sp_campeonatos $$
CREATE PROCEDURE sp_campeonatos(
    IN p_nivel VARCHAR(50)
)
BEGIN
    SELECT c.*, GREATEST(0, c.vagas_total - COUNT(i.id)) AS vagas
    FROM campeonatos c
    LEFT JOIN inscricoes i ON i.id_campeonato = c.id AND i.status = 'ativa'
    WHERE (p_nivel IS NULL OR p_nivel = '' OR c.nivel = p_nivel)
    GROUP BY c.id
    ORDER BY (c.status = 'aberto') DESC, c.data ASC;
END $$


-- classificacao de UM campeonato: vitorias, saldo de sets e aproveitamento
-- (inclui duplas inscritas que ainda nao jogaram)
DROP PROCEDURE IF EXISTS sp_classificacao_campeonato $$
CREATE PROCEDURE sp_classificacao_campeonato(
    IN p_id_campeonato INT
)
BEGIN
    SELECT
        d.id AS id_dupla,
        d.nome,
        COUNT(p.id) AS jogos,
        COUNT(CASE WHEN p.id_dupla_vencedora = d.id THEN 1 END) AS vitorias,
        COUNT(p.id) - COUNT(CASE WHEN p.id_dupla_vencedora = d.id THEN 1 END) AS derrotas,
        COALESCE(SUM(CASE
            WHEN p.id_dupla1 = d.id THEN p.placar_dupla1 - p.placar_dupla2
            WHEN p.id_dupla2 = d.id THEN p.placar_dupla2 - p.placar_dupla1
            ELSE 0 END), 0) AS saldo_sets,
        IF(COUNT(p.id) = 0, 0,
           ROUND(100 * COUNT(CASE WHEN p.id_dupla_vencedora = d.id THEN 1 END) / COUNT(p.id))) AS aproveitamento
    FROM duplas d
    LEFT JOIN partidas p
        ON p.id_campeonato = p_id_campeonato
       AND p.status = 'finalizada'
       AND (p.id_dupla1 = d.id OR p.id_dupla2 = d.id)
    WHERE d.id IN (SELECT id_dupla FROM inscricoes
                   WHERE id_campeonato = p_id_campeonato AND status = 'ativa')
       OR d.id IN (SELECT id_dupla1 FROM partidas WHERE id_campeonato = p_id_campeonato)
       OR d.id IN (SELECT id_dupla2 FROM partidas WHERE id_campeonato = p_id_campeonato)
    GROUP BY d.id, d.nome
    ORDER BY vitorias DESC, d.nome ASC;
END $$


-- ranking geral das duplas (so quem ja jogou)
DROP PROCEDURE IF EXISTS sp_ranking_duplas $$
CREATE PROCEDURE sp_ranking_duplas()
BEGIN
    SELECT
        d.id AS id_dupla,
        d.nome,
        d.categoria,
        u1.nome AS jogador1,
        u2.nome AS jogador2,
        COUNT(CASE
            WHEN (p.id_dupla1 = d.id AND p.placar_dupla1 > p.placar_dupla2)
              OR (p.id_dupla2 = d.id AND p.placar_dupla2 > p.placar_dupla1)
            THEN 1 END) AS vitorias,
        COUNT(p.id) AS partidas_jogadas,
        ROUND(100 * COUNT(CASE
            WHEN (p.id_dupla1 = d.id AND p.placar_dupla1 > p.placar_dupla2)
              OR (p.id_dupla2 = d.id AND p.placar_dupla2 > p.placar_dupla1)
            THEN 1 END) / COUNT(p.id)) AS aproveitamento
    FROM duplas d
    LEFT JOIN usuarios u1 ON u1.id = d.id_usuario1
    LEFT JOIN usuarios u2 ON u2.id = d.id_usuario2
    LEFT JOIN partidas p
        ON (p.id_dupla1 = d.id OR p.id_dupla2 = d.id)
       AND p.status = 'finalizada'
    GROUP BY d.id, d.nome, d.categoria, u1.nome, u2.nome
    HAVING partidas_jogadas > 0
    ORDER BY vitorias DESC, aproveitamento DESC;
END $$


-- duplas com inscricao ativa em um campeonato
DROP PROCEDURE IF EXISTS sp_inscritos_campeonato $$
CREATE PROCEDURE sp_inscritos_campeonato(
    IN p_id_campeonato INT
)
BEGIN
    SELECT
        i.id AS id_inscricao,
        i.status AS status_inscricao,
        i.data_inscricao,
        d.id AS id_dupla,
        d.nome,
        d.categoria,
        u1.nome AS jogador1,
        u2.nome AS jogador2
    FROM inscricoes i
    JOIN duplas d ON d.id = i.id_dupla
    LEFT JOIN usuarios u1 ON u1.id = d.id_usuario1
    LEFT JOIN usuarios u2 ON u2.id = d.id_usuario2
    WHERE i.id_campeonato = p_id_campeonato
      AND i.status = 'ativa'
    ORDER BY i.data_inscricao ASC, i.id ASC;
END $$


-- historico de partidas de um jogador (V = vitoria, D = derrota)
DROP PROCEDURE IF EXISTS sp_historico_partidas_usuario $$
CREATE PROCEDURE sp_historico_partidas_usuario(
    IN p_id_usuario INT
)
BEGIN
    SELECT
        p.id AS id_partida,
        p.fase,
        p.data_hora,
        p.status,
        c.nome AS campeonato,
        d_adv.id AS id_dupla_adversaria,
        d_adv.nome AS adversaria,
        CASE WHEN p.id_dupla1 = d_jogador.id THEN p.placar_dupla1 ELSE p.placar_dupla2 END AS placar_jogador,
        CASE WHEN p.id_dupla1 = d_jogador.id THEN p.placar_dupla2 ELSE p.placar_dupla1 END AS placar_adversario,
        IF(p.id_dupla_vencedora = d_jogador.id, 'V', 'D') AS resultado
    FROM partidas p
    JOIN duplas d_jogador
        ON (d_jogador.id_usuario1 = p_id_usuario OR d_jogador.id_usuario2 = p_id_usuario)
       AND (p.id_dupla1 = d_jogador.id OR p.id_dupla2 = d_jogador.id)
    LEFT JOIN duplas d_adv
        ON d_adv.id = CASE WHEN p.id_dupla1 = d_jogador.id THEN p.id_dupla2 ELSE p.id_dupla1 END
    LEFT JOIN campeonatos c ON c.id = p.id_campeonato
    ORDER BY p.data_hora DESC;
END $$


-- quadras ordenadas pela quantidade de partidas jogadas nelas
DROP PROCEDURE IF EXISTS sp_quadras_mais_utilizadas $$
CREATE PROCEDURE sp_quadras_mais_utilizadas()
BEGIN
    SELECT
        q.id AS id_quadra,
        q.nome,
        q.cidade,
        COUNT(p.id) AS total_partidas
    FROM quadras q
    LEFT JOIN partidas p ON p.id_quadra = q.id
    GROUP BY q.id, q.nome, q.cidade
    ORDER BY total_partidas DESC;
END $$


-- numeros do painel do administrador (uma linha so)
DROP PROCEDURE IF EXISTS sp_resumo_admin $$
CREATE PROCEDURE sp_resumo_admin()
BEGIN
    SELECT
        (SELECT COUNT(*) FROM usuarios) AS total_usuarios,
        (SELECT COUNT(*) FROM usuarios WHERE tipo = 'jogador' AND (adm IS NULL OR adm = 0)) AS jogadores,
        (SELECT COUNT(*) FROM usuarios WHERE tipo = 'professor') AS professores,
        (SELECT COUNT(*) FROM usuarios WHERE tipo = 'dono') AS donos_de_quadra,
        (SELECT COUNT(*) FROM usuarios WHERE bloqueado = 1) AS usuarios_bloqueados,
        (SELECT COUNT(*) FROM campeonatos WHERE status = 'aberto') AS campeonatos_abertos,
        (SELECT COUNT(*) FROM quadras) AS total_quadras,
        (SELECT COUNT(*) FROM duplas WHERE ativa = 1) AS duplas_ativas,
        (SELECT COUNT(*) FROM inscricoes WHERE status = 'ativa') AS inscricoes_ativas,
        (SELECT COUNT(*) FROM partidas) AS partidas_registradas,
        (SELECT COUNT(*) FROM solicitacoes WHERE status = 'pendente') AS solicitacoes_pendentes,
        (SELECT COALESCE(SUM(premio), 0) FROM campeonatos WHERE status = 'aberto') AS premiacao_aberta;
END $$

DELIMITER ;
