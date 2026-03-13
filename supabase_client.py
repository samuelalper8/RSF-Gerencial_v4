"""
supabase_client.py — Integração Supabase para ConPrev Dashboard
===============================================================
Responsável por:
- Publicar resultados de análise (stats + ZIP) após cada ciclo admin
- Recuperar análises publicadas para o dashboard dos sócios
- Gerenciar uploads de ZIP no Supabase Storage

Configuração necessária em .streamlit/secrets.toml:
    SUPABASE_URL = "https://xxxx.supabase.co"
    SUPABASE_KEY = "sua_service_role_key"   # NÃO use anon key aqui

Schema SQL: veja schema.sql na raiz do repositório.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)

# ── Importação defensiva ──────────────────────────────────────────────────────
try:
    from supabase import Client, create_client

    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False
    Client = Any  # type: ignore[misc,assignment]


# ── Client singleton ──────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client() -> "Client":
    """
    Retorna client Supabase cacheado pela sessão Streamlit.

    Raises:
        RuntimeError: se supabase-py não estiver instalado ou secrets ausentes.
    """
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
    """Verifica se a integração Supabase está configurada e acessível."""
    if not _SUPABASE_AVAILABLE:
        return False
    try:
        get_client()
        return True
    except Exception:
        return False


# ── Publicação ────────────────────────────────────────────────────────────────

def publicar_analise(
    stats: dict[str, Any],
    zip_bytes: bytes,
    ref_date: str,
    ts: str,
) -> str:
    """
    Publica uma análise completa no Supabase.

    Fluxo:
        1. INSERT em `analises` com stats_json completo
        2. INSERT batch em `municipios_status` (uma linha por município)
        3. Upload do ZIP em Storage bucket `relatorios`

    Args:
        stats:     Dicionário retornado por compute_stats()
        zip_bytes: Bytes do ZIP gerado pela análise
        ref_date:  Data de referência (ex.: "12/03/2026")
        ts:        Timestamp usado no nome do arquivo (ex.: "2026-03-13_15h24")

    Returns:
        analise_id: UUID string da análise recém-publicada

    Raises:
        RuntimeError: em caso de falha na publicação
    """
    client = get_client()

    # 1) Insere análise principal
    analise_payload: dict[str, Any] = {
        "ref_date":          ref_date,
        "total_municipios":  stats.get("total_municipios", 0),
        "stats_json":        json.dumps(stats, ensure_ascii=False, default=str),
        "zip_ts":            ts,
    }
    resp = client.table("analises").insert(analise_payload).execute()
    if not resp.data:
        raise RuntimeError("Falha ao inserir análise no Supabase.")
    analise_id: str = resp.data[0]["id"]

    # 2) Insere status por município em batch
    rows: list[dict[str, Any]] = []
    for m in stats.get("por_municipio", []):
        dias: int | None = m.get("cnd_dias")
        cnd_st: str
        if dias is None:
            cnd_st = "sem_info"
        elif dias < 0:
            cnd_st = "vencida"
        elif dias <= 30:
            cnd_st = "urgente"
        elif dias <= 90:
            cnd_st = "atencao"
        else:
            cnd_st = "ok"

        rows.append({
            "analise_id": analise_id,
            "nome":        m["nome"],
            "n_dev":       int(m.get("n_dev",  0)),
            "v_dev":       float(m.get("v_dev",  0.0)),
            "n_maed":      int(m.get("n_maed", 0)),
            "v_maed":      float(m.get("v_maed", 0.0)),
            "n_omiss":     int(m.get("n_omiss", 0)),
            "n_pf":        int(m.get("n_pf",   0)),
            "cnd_dias":    dias,
            "cnd_status":  cnd_st,
        })

    if rows:
        # Supabase aceita até ~1000 linhas por batch; chunking por segurança
        CHUNK = 500
        for i in range(0, len(rows), CHUNK):
            client.table("municipios_status").insert(rows[i : i + CHUNK]).execute()

    # 3) Upload do ZIP no Storage
    bucket_path = f"{analise_id}/ConPrev_Restricoes_{ts}.zip"
    try:
        client.storage.from_("relatorios").upload(
            path=bucket_path,
            file=zip_bytes,
            file_options={"content-type": "application/zip"},
        )
    except Exception as exc:
        logger.warning("Upload do ZIP falhou (análise publicada sem arquivo): %s", exc)

    return analise_id


# ── Leitura ───────────────────────────────────────────────────────────────────

def listar_analises(limit: int = 20) -> list[dict[str, Any]]:
    """
    Retorna as últimas `limit` análises publicadas (mais recentes primeiro).

    Returns:
        Lista de dicts com campos: id, created_at, ref_date, total_municipios
    """
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
    """
    Retorna o stats_json completo de uma análise específica.

    Args:
        analise_id: UUID da análise

    Returns:
        Dicionário de stats (mesmo formato de compute_stats()) com
        campos extras _id, _ref_date e _created_at.
    """
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
    """
    Retorna todos os municípios de uma análise ordenados por urgência de CND.

    Ordem: vencida → urgente → atencao → ok → sem_info
    """
    client = get_client()
    resp = (
        client.table("municipios_status")
        .select("*")
        .eq("analise_id", analise_id)
        .execute()
    )
    rows: list[dict] = resp.data or []

    # Ordena por urgência (Python-side para evitar ORDER BY complexo no Supabase)
    _order = {"vencida": 0, "urgente": 1, "atencao": 2, "ok": 3, "sem_info": 4}
    rows.sort(key=lambda r: (
        _order.get(r.get("cnd_status", "sem_info"), 5),
        -(r.get("v_dev", 0) + r.get("v_maed", 0)),
    ))
    return rows


def gerar_url_download(analise_id: str, zip_ts: str, expiry_seconds: int = 3600) -> str | None:
    """
    Gera URL assinada (válida por `expiry_seconds`) para download do ZIP.

    Args:
        analise_id:     UUID da análise
        zip_ts:         Timestamp usado no nome do arquivo
        expiry_seconds: Validade da URL em segundos (padrão: 1h)

    Returns:
        URL assinada ou None em caso de falha
    """
    client = get_client()
    bucket_path = f"{analise_id}/ConPrev_Restricoes_{zip_ts}.zip"
    try:
        resp = client.storage.from_("relatorios").create_signed_url(
            bucket_path, expiry_seconds
        )
        return resp.get("signedURL") or resp.get("data", {}).get("signedUrl")
    except Exception as exc:
        logger.warning("Falha ao gerar URL assinada: %s", exc)
        return None
