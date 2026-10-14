"""Carga: grava no PostgreSQL de forma incremental e idempotente."""
from datetime import date
from pathlib import Path

import pandas as pd
import psycopg

SCHEMA_SQL = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"

UPSERT_SQL = """
    INSERT INTO indicadores.serie_temporal (serie, data, valor)
    VALUES (%s, %s, %s)
    ON CONFLICT (serie, data) DO UPDATE
        SET valor = EXCLUDED.valor,
            atualizado_em = now()
        WHERE indicadores.serie_temporal.valor IS DISTINCT FROM EXCLUDED.valor
"""


def criar_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_SQL.read_text())
    conn.commit()


def ultima_data(conn: psycopg.Connection, serie: str) -> date | None:
    """Última data já carregada da série (base da carga incremental)."""
    linha = conn.execute(
        "SELECT MAX(data) FROM indicadores.serie_temporal WHERE serie = %s", (serie,)
    ).fetchone()
    return linha[0] if linha else None


def carregar(conn: psycopg.Connection, df: pd.DataFrame) -> int:
    """Faz upsert das linhas. Rodar duas vezes com o mesmo df não duplica nada."""
    if df.empty:
        return 0
    linhas = list(df[["serie", "data", "valor"]].itertuples(index=False, name=None))
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, linhas)
    conn.commit()
    return len(linhas)


def registrar_execucao(conn: psycopg.Connection, serie: str, inicio: date, fim: date,
                       linhas: int, status: str, erro: str | None = None) -> None:
    """Trilha de auditoria: toda execução fica registrada, com sucesso ou falha."""
    conn.execute(
        """INSERT INTO indicadores.execucao (serie, periodo_inicio, periodo_fim, linhas, status, erro)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (serie, inicio, fim, linhas, status, erro),
    )
    conn.commit()
