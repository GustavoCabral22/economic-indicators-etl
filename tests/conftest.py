import os

import psycopg
import pytest

from bcb_etl import load


@pytest.fixture
def conn():
    """Conexão num banco real. Os testes de carga são pulados se não houver banco."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL não definida: pulando teste de integração")
    with psycopg.connect(url) as c:
        load.criar_schema(c)
        c.execute("TRUNCATE indicadores.serie_temporal, indicadores.execucao")
        c.commit()
        yield c
