from datetime import date
from itertools import pairwise

from bcb_etl.config import SERIES
from bcb_etl.extract import dividir_periodo, extrair


class RespostaFalsa:
    def __init__(self, status_code, dados=None):
        self.status_code = status_code
        self._dados = dados or []

    def json(self):
        return self._dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class SessaoFalsa:
    """Substitui a API real: os testes não dependem de internet."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def get(self, url, params, timeout):
        self.chamadas.append(params)
        return self.respostas.pop(0)


def test_dividir_periodo_respeita_janela_maxima():
    janelas = list(dividir_periodo(date(2000, 1, 1), date(2024, 12, 31), max_dias=3650))
    assert len(janelas) == 3
    assert janelas[0][0] == date(2000, 1, 1)
    assert janelas[-1][1] == date(2024, 12, 31)
    # janelas contíguas, sem buraco nem sobreposição
    for (_, fim), (ini, _) in pairwise(janelas):
        assert (ini - fim).days == 1


def test_extrair_junta_todas_as_janelas():
    sessao = SessaoFalsa([
        RespostaFalsa(200, [{"data": "02/01/2015", "valor": "2.69"}]),
        RespostaFalsa(200, [{"data": "02/01/2025", "valor": "6.20"}]),
    ])
    registros = extrair(SERIES["dolar_ptax"], date(2015, 1, 1), date(2025, 1, 31), sessao)
    assert len(sessao.chamadas) == 2
    assert [r["valor"] for r in registros] == ["2.69", "6.20"]


def test_extrair_trata_404_como_periodo_sem_dados():
    sessao = SessaoFalsa([RespostaFalsa(404)])
    assert extrair(SERIES["dolar_ptax"], date(2025, 1, 4), date(2025, 1, 5), sessao) == []
