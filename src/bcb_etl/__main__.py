"""Linha de comando.

Exemplos:
    python -m bcb_etl                       # todas as séries, incremental
    python -m bcb_etl --serie ipca          # só o IPCA
    python -m bcb_etl --serie dolar_ptax --desde 2020-01-01   # reprocessa um período
"""
import argparse
import logging
import sys
from datetime import date

import psycopg

from . import load, pipeline
from .config import SERIES, database_url

log = logging.getLogger("bcb_etl")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bcb_etl", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serie", choices=sorted(SERIES), help="padrão: todas")
    parser.add_argument("--desde", type=date.fromisoformat, help="AAAA-MM-DD")
    parser.add_argument("--ate", type=date.fromisoformat, help="AAAA-MM-DD (padrão: hoje)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    series = [args.serie] if args.serie else list(SERIES)
    falhas = 0
    with psycopg.connect(database_url()) as conn:
        load.criar_schema(conn)
        for nome in series:
            try:
                pipeline.executar(nome, conn, args.desde, args.ate)
            except Exception:
                log.exception("Falha ao processar %s", nome)
                falhas += 1

    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
