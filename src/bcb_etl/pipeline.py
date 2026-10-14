"""Orquestra extract -> transform -> load para uma série."""
import logging
from datetime import date, timedelta

import psycopg

from . import extract, load, transform
from .config import DATA_INICIAL_PADRAO, DIAS_REPROCESSAMENTO, SERIES

log = logging.getLogger(__name__)


def definir_inicio(ultima: date | None, desde: date | None) -> date:
    """Regra da carga incremental.

    - `desde` informado: respeita (útil para reprocessar um período).
    - série já existe no banco: começa um pouco antes da última data,
      para capturar revisões do BCB.
    - série nova: começa na data padrão.
    """
    if desde:
        return desde
    if ultima:
        return ultima - timedelta(days=DIAS_REPROCESSAMENTO)
    return DATA_INICIAL_PADRAO


def executar(nome_serie: str, conn: psycopg.Connection, desde: date | None = None,
             ate: date | None = None) -> int:
    serie = SERIES[nome_serie]
    fim = ate or date.today()
    inicio = definir_inicio(load.ultima_data(conn, serie.nome), desde)

    log.info("%s: buscando de %s a %s", serie.nome, inicio, fim)
    try:
        registros = extract.extrair(serie, inicio, fim)
        df = transform.transformar(serie, registros)
        linhas = load.carregar(conn, df)
    except Exception as erro:
        conn.rollback()
        load.registrar_execucao(conn, serie.nome, inicio, fim, 0, "erro", str(erro))
        raise

    load.registrar_execucao(conn, serie.nome, inicio, fim, linhas, "sucesso")
    log.info("%s: %d linhas carregadas", serie.nome, linhas)
    return linhas
