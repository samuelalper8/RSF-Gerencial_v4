"""
supabase_client.py — Integração Supabase para ConPrev Dashboard
===============================================================
v2: adiciona publicação de itens detalhados (itens_restricoes)
    e busca de itens por município.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False
    Client = Any  # type: ignore[misc,assignment]

_CHUNK = 300   # linhas por batch no Supabase


# ── Client singleton ──────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client() -> "Client":
    """Retorna client Supabase cacheado. Raises RuntimeError se mal configurado."""
    if not _SUPABASE_AVAILABLE:
        raise RuntimeError(
            "supabase-py não instalado. "
            "Adicione `supabase>=2.0.0` ao requirements.txt."
        )
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            f"Secret Supabase ausente: {exc}. "
            "Configure SUPABASE_URL e SUPABASE_KEY em .streamlit/secrets.toml."
        ) from exc
    return create_client(url, key)


def supabase_disponivel() -> bool:
    if not _SUPABASE_AVAILABLE:
        return False
    try:
        get_client()
        return True
    except Exception:
        return False


# ── Helpers de conversão ──────────────────────────────────────────────────────

def _f(v: Any) -> float | None:
    """Converte string BRL ou número para float, retorna None se inválido."""
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(".", "").replace(",", "."))
    except (ValueError, TypeError):
        return None


def _s(v: Any) -> str | None:
    s = str(v).strip() if v is not None else ""
    return s if s else None


def _itens_para_rows(
    analise_id: str,
    ocorrencias_por_mun: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Converte ocorrencias_por_mun → rows para tabela `itens_restricoes`.
    """
    rows: list[dict[str, Any]] = []
    for municipio, itens in ocorrencias_por_mun.items():
        for it in itens:
            tipo = str(it.get("tipo", "")).upper().strip()
            if tipo not in ("DEVEDOR", "MAED", "OMISSÃO", "PROCESSO FISCAL"):
                continue

            row: dict[str, Any] = {
                "analise_id":   analise_id,
                "municipio":    municipio,
                "orgao":        _s(it.get("orgao") or it.get("org")),
                "cnpj":         _s(it.get("cnpj")),
                "tipo":         tipo,
                "cnpj_colisao": bool(it.get("cnpj_colisao", False)),
                "raw_text":     _s(it.get("raw")),
            }

            if tipo in ("DEVEDOR", "MAED"):
                row.update({
                    "cod":           _s(it.get("cod")),
                    "desc_rubrica":  _s(it.get("desc") or it.get("nome")),
                    "comp":          _s(it.get("comp")),
                    "venc":          _s(it.get("venc")),
                    "v_original":    _f(it.get("orig")),
                    "v_devedor":     _f(it.get("dev")),
                    "v_multa":       _f(it.get("multa")),
                    "v_juros":       _f(it.get("juros")),
                    "v_consolidado": _f(it.get("cons")),
                    "situacao":      _s(it.get("situacao")),
                    "residual":      bool(it.get("residual", False)),
                })
            elif tipo == "OMISSÃO":
                row.update({
                    "periodo":         _s(it.get("periodo")),
                    "tipo_declaracao": _s(it.get("tipo_declaracao")),
                })
            elif tipo == "PROCESSO FISCAL":
                row.update({
                    "processo": _s(it.get("processo")),
                    "situacao": _s(it.get("situacao")),
                })

            rows.append(row)
    return rows


# ── Publicação ────────────────────────────────────────────────────────────────

def publicar_analise(
    stats: dict[str, Any],
    zip_bytes: bytes,
    ref_date: str,
    ts: str,
    ocorrencias_por_mun: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    """
    Publica análise completa no Supabase.

    Fluxo:
        1. INSERT em `analises`
        2. INSERT batch em `municipios_status`
        3. INSERT batch em `itens_restricoes` (detalhe por item)
        4. Upload do ZIP em Storage bucket `relatorios`
    """
    client = get_client()

    # 1) Análise principal
    resp = client.table("analises").insert({
        "ref_date":         ref_date,
        "total_municipios": stats.get("total_municipios", 0),
        "stats_json":       json.dumps(stats, ensure_ascii=False, default=str),
        "zip_ts":           ts,
    }).execute()
    if not resp.data:
        raise RuntimeError("Falha ao inserir análise no Supabase.")
    analise_id: str = resp.data[0]["id"]

    # 2) Status por município
    status_rows: list[dict[str, Any]] = []
    for m in stats.get("por_municipio", []):
        dias: int | None = m.get("cnd_dias")
        if dias is None:    cnd_st = "sem_info"
        elif dias < 0:      cnd_st = "vencida"
        elif dias <= 30:    cnd_st = "urgente"
        elif dias <= 90:    cnd_st = "atencao"
        else:               cnd_st = "ok"
        status_rows.append({
            "analise_id": analise_id,
            "nome":       m["nome"],
            "n_dev":      int(m.get("n_dev",  0)),
            "v_dev":      float(m.get("v_dev",  0.0)),
            "n_maed":     int(m.get("n_maed", 0)),
            "v_maed":     float(m.get("v_maed", 0.0)),
            "n_omiss":    int(m.get("n_omiss", 0)),
            "n_pf":       int(m.get("n_pf",   0)),
            "cnd_dias":   dias,
            "cnd_status": cnd_st,
        })
    for i in range(0, len(status_rows), _CHUNK):
        client.table("municipios_status").insert(status_rows[i:i+_CHUNK]).execute()

    # 3) Itens detalhados
    if ocorrencias_por_mun:
        item_rows = _itens_para_rows(analise_id, ocorrencias_por_mun)
        for i in range(0, len(item_rows), _CHUNK):
            client.table("itens_restricoes").insert(item_rows[i:i+_CHUNK]).execute()
        logger.info("Publicados %d itens detalhados.", len(item_rows))

    # 4) Upload ZIP
    try:
        client.storage.from_("relatorios").upload(
            path=f"{analise_id}/ConPrev_Restricoes_{ts}.zip",
            file=zip_bytes,
            file_options={"content-type": "application/zip"},
        )
    except Exception as exc:
        logger.warning("Upload ZIP falhou: %s", exc)

    return analise_id


# ── Leitura ───────────────────────────────────────────────────────────────────

def listar_analises(limit: int = 20) -> list[dict[str, Any]]:
    client = get_client()
    resp = (
        client.table("analises")
        .select("id, created_at, ref_date, total_municipios, zip_ts")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def buscar_stats(analise_id: str) -> dict[str, Any]:
    client = get_client()
    resp = (
        client.table("analises")
        .select("*")
        .eq("id", analise_id)
        .single()
        .execute()
    )
    row: dict = resp.data or {}
    if not row:
        return {}
    stats: dict = json.loads(row.get("stats_json") or "{}")
    stats["_id"]         = row["id"]
    stats["_ref_date"]   = row.get("ref_date", "")
    stats["_created_at"] = row.get("created_at", "")
    stats["_zip_ts"]     = row.get("zip_ts", "")
    return stats


def buscar_municipios(analise_id: str) -> list[dict[str, Any]]:
    client = get_client()
    resp = (
        client.table("municipios_status")
        .select("*")
        .eq("analise_id", analise_id)
        .execute()
    )
    rows: list[dict] = resp.data or []
    _order = {"vencida": 0, "urgente": 1, "atencao": 2, "ok": 3, "sem_info": 4}
    rows.sort(key=lambda r: (
        _order.get(r.get("cnd_status", "sem_info"), 5),
        -(r.get("v_dev", 0) + r.get("v_maed", 0)),
    ))
    return rows


def buscar_itens_municipio(
    analise_id: str,
    municipio: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Retorna todos os itens de um município agrupados por tipo.

    Returns:
        {"DEVEDOR": [...], "MAED": [...], "OMISSÃO": [...], "PROCESSO FISCAL": [...]}
    """
    client = get_client()
    resp = (
        client.table("itens_restricoes")
        .select("*")
        .eq("analise_id", analise_id)
        .eq("municipio", municipio)
        .execute()
    )
    result: dict[str, list] = {
        "DEVEDOR": [], "MAED": [], "OMISSÃO": [], "PROCESSO FISCAL": []
    }
    for r in resp.data or []:
        tipo = r.get("tipo", "")
        if tipo in result:
            result[tipo].append(r)
    return result


def gerar_url_download(
    analise_id: str,
    zip_ts: str,
    expiry_seconds: int = 3600,
) -> str | None:
    client = get_client()
    try:
        resp = client.storage.from_("relatorios").create_signed_url(
            f"{analise_id}/ConPrev_Restricoes_{zip_ts}.zip", expiry_seconds
        )
        return resp.get("signedURL") or resp.get("data", {}).get("signedUrl")
    except Exception as exc:
        logger.warning("Falha ao gerar URL assinada: %s", exc)
        return None
