"""Extração: busca os dados brutos na API SGS do Banco Central."""
import logging
from datetime import date, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import BCB_URL, JANELA_MAXIMA_DIAS, Serie

log = logging.getLogger(__name__)


def criar_sessao() -> requests.Session:
    """Sessão HTTP com retry automático: a API do BCB oscila com frequência."""
    retry = Retry(
        total=5,
        backoff_factor=2,  # espera 2s, 4s, 8s...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    sessao = requests.Session()
    sessao.mount("https://", HTTPAdapter(max_retries=retry))
    return sessao


def dividir_periodo(inicio: date, fim: date, max_dias: int = JANELA_MAXIMA_DIAS):
    """Quebra [inicio, fim] em janelas de no máximo `max_dias` dias."""
    atual = inicio
    while atual <= fim:
        fim_janela = min(atual + timedelta(days=max_dias - 1), fim)
        yield atual, fim_janela
        atual = fim_janela + timedelta(days=1)


def extrair(serie: Serie, inicio: date, fim: date, sessao: requests.Session | None = None) -> list[dict]:
    """Retorna a lista de registros brutos ({"data": "dd/mm/aaaa", "valor": "1.23"})."""
    sessao = sessao or criar_sessao()
    registros: list[dict] = []

    for ini, fim_janela in dividir_periodo(inicio, fim):
        params = {
            "formato": "json",
            "dataInicial": ini.strftime("%d/%m/%Y"),
            "dataFinal": fim_janela.strftime("%d/%m/%Y"),
        }
        resposta = sessao.get(BCB_URL.format(codigo=serie.codigo_sgs), params=params, timeout=30)

        # A API responde 404 quando não há dados no período (ex.: fim de semana).
        if resposta.status_code == 404:
            log.info("%s: sem dados entre %s e %s", serie.nome, ini, fim_janela)
            continue
        resposta.raise_for_status()

        lote = resposta.json()
        log.info("%s: %d registros entre %s e %s", serie.nome, len(lote), ini, fim_janela)
        registros.extend(lote)

    return registros
