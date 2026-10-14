from datetime import date, timedelta

import pytest

from bcb_etl import pipeline
from bcb_etl.config import DATA_INICIAL_PADRAO, DIAS_REPROCESSAMENTO
from bcb_etl.transform import ErroQualidadeDados


def test_inicio_serie_nova_usa_data_padrao():
    assert pipeline.definir_inicio(None, None) == DATA_INICIAL_PADRAO


def test_inicio_incremental_volta_janela_de_reprocessamento():
    ultima = date(2025, 6, 30)
    assert pipeline.definir_inicio(ultima, None) == ultima - timedelta(days=DIAS_REPROCESSAMENTO)


def test_inicio_explicito_tem_prioridade():
    assert pipeline.definir_inicio(date(2025, 6, 30), date(2020, 1, 1)) == date(2020, 1, 1)


def test_execucao_completa_e_idempotente(conn, monkeypatch):
    dados = [{"data": "01/01/2025", "valor": "0.16"}, {"data": "01/02/2025", "valor": "1.31"}]
    monkeypatch.setattr(pipeline.extract, "extrair", lambda *a, **k: dados)

    pipeline.executar("ipca", conn, desde=date(2025, 1, 1), ate=date(2025, 2, 28))
    pipeline.executar("ipca", conn, desde=date(2025, 1, 1), ate=date(2025, 2, 28))

    total = conn.execute("SELECT COUNT(*) FROM indicadores.serie_temporal").fetchone()[0]
    execucoes = conn.execute(
        "SELECT COUNT(*) FROM indicadores.execucao WHERE status = 'sucesso'"
    ).fetchone()[0]
    assert total == 2          # rodou 2 vezes, mas não duplicou
    assert execucoes == 2      # e as 2 execuções ficaram registradas


def test_falha_fica_registrada_na_auditoria(conn, monkeypatch):
    monkeypatch.setattr(pipeline.extract, "extrair",
                        lambda *a, **k: [{"data": "01/01/2025", "valor": "999"}])

    with pytest.raises(ErroQualidadeDados):
        pipeline.executar("ipca", conn, desde=date(2025, 1, 1), ate=date(2025, 1, 31))

    status, erro = conn.execute("SELECT status, erro FROM indicadores.execucao").fetchone()
    assert status == "erro"
    assert "fora da faixa" in erro
    assert conn.execute("SELECT COUNT(*) FROM indicadores.serie_temporal").fetchone()[0] == 0
