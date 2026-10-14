"""Transformação: tipagem e validação de qualidade dos dados."""
import pandas as pd

from .config import Serie


class ErroQualidadeDados(Exception):
    """Levantado quando o dado não passa nas validações. Melhor parar do que carregar lixo."""


def transformar(serie: Serie, registros: list[dict]) -> pd.DataFrame:
    """Converte os registros brutos num DataFrame tipado e validado.

    Colunas de saída: serie (str), data (date), valor (float).
    """
    if not registros:
        return pd.DataFrame(columns=["serie", "data", "valor"])

    df = pd.DataFrame(registros)

    faltando = {"data", "valor"} - set(df.columns)
    if faltando:
        raise ErroQualidadeDados(f"{serie.nome}: colunas ausentes na resposta: {faltando}")

    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce").dt.date
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df.insert(0, "serie", serie.nome)

    validar(serie, df)
    return df.sort_values("data").reset_index(drop=True)


def validar(serie: Serie, df: pd.DataFrame) -> None:
    problemas = []

    nulos = df[df["data"].isna() | df["valor"].isna()]
    if not nulos.empty:
        problemas.append(f"{len(nulos)} linha(s) com data ou valor inválido")

    duplicadas = df[df.duplicated("data", keep=False)]
    if not duplicadas.empty:
        problemas.append(f"{duplicadas['data'].nunique()} data(s) duplicada(s)")

    fora_da_faixa = df[(df["valor"] < serie.valor_minimo) | (df["valor"] > serie.valor_maximo)]
    if not fora_da_faixa.empty:
        problemas.append(
            f"{len(fora_da_faixa)} valor(es) fora da faixa "
            f"[{serie.valor_minimo}, {serie.valor_maximo}]"
        )

    if problemas:
        raise ErroQualidadeDados(f"{serie.nome}: " + "; ".join(problemas))
