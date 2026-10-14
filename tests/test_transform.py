from datetime import date

import pytest

from bcb_etl.config import SERIES
from bcb_etl.transform import ErroQualidadeDados, transformar

IPCA = SERIES["ipca"]


def test_converte_tipos_e_ordena():
    df = transformar(IPCA, [
        {"data": "01/02/2025", "valor": "1.31"},
        {"data": "01/01/2025", "valor": "0.16"},
    ])
    assert list(df.columns) == ["serie", "data", "valor"]
    assert df["data"].tolist() == [date(2025, 1, 1), date(2025, 2, 1)]
    assert df["valor"].tolist() == [0.16, 1.31]
    assert (df["serie"] == "ipca").all()


def test_lista_vazia_retorna_dataframe_vazio():
    assert transformar(IPCA, []).empty


@pytest.mark.parametrize("registros, mensagem", [
    ([{"data": "01/01/2025", "valor": "abc"}], "inválido"),
    ([{"data": "2025-01-01", "valor": "0.5"}], "inválido"),
    ([{"data": "01/01/2025", "valor": "0.5"}, {"data": "01/01/2025", "valor": "0.6"}], "duplicada"),
    ([{"data": "01/01/2025", "valor": "55"}], "fora da faixa"),
    ([{"dt": "01/01/2025", "valor": "0.5"}], "colunas ausentes"),
])
def test_rejeita_dado_ruim(registros, mensagem):
    with pytest.raises(ErroQualidadeDados, match=mensagem):
        transformar(IPCA, registros)
