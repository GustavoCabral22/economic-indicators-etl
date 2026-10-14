"""Configuração central: quais séries buscar e como conectar no banco."""
import os
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Serie:
    nome: str
    codigo_sgs: int
    descricao: str
    periodicidade: str      # "diaria" ou "mensal"
    valor_minimo: float     # faixa plausível: fora dela, o dado é suspeito
    valor_maximo: float


SERIES: dict[str, Serie] = {
    s.nome: s
    for s in [
        Serie("ipca", 433, "IPCA - variação % mensal", "mensal", -5.0, 10.0),
        Serie("selic_meta", 432, "Meta Selic definida pelo Copom (% a.a.)", "diaria", 0.0, 50.0),
        Serie("dolar_ptax", 1, "Dólar PTAX venda (R$)", "diaria", 0.5, 20.0),
    ]
}

# Primeira data buscada quando a série ainda não existe no banco.
DATA_INICIAL_PADRAO = date(2015, 1, 1)

# Quantos dias para trás rebuscar numa carga incremental. O BCB às vezes
# revisa valores recentes; rebuscar uma janela curta captura essas correções.
DIAS_REPROCESSAMENTO = 45

BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

# A API limita consultas de séries diárias a janelas de até 10 anos.
JANELA_MAXIMA_DIAS = 3650


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/indicadores"
    )
