CREATE SCHEMA IF NOT EXISTS indicadores;

-- Formato "longo": uma linha por série e data. Adicionar uma série nova
-- não exige mudar a tabela, só o arquivo de configuração.
CREATE TABLE IF NOT EXISTS indicadores.serie_temporal (
    serie          TEXT        NOT NULL,
    data           DATE        NOT NULL,
    valor          NUMERIC(18, 6) NOT NULL,
    carregado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (serie, data)
);

CREATE TABLE IF NOT EXISTS indicadores.execucao (
    id              BIGSERIAL PRIMARY KEY,
    serie           TEXT        NOT NULL,
    periodo_inicio  DATE        NOT NULL,
    periodo_fim     DATE        NOT NULL,
    linhas          INTEGER     NOT NULL,
    status          TEXT        NOT NULL CHECK (status IN ('sucesso', 'erro')),
    erro            TEXT,
    executado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);
