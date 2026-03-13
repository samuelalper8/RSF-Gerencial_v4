"""
dashboard_socios.py — Dashboard de Acompanhamento para Sócios ConPrev
=====================================================================
Interface read-only que consome dados publicados pelo admin no Supabase.

Exibe:
  - Seletor de análises publicadas
  - Alertas de CND com semáforo de urgência
  - Painel de estatísticas macro
  - Tabela detalhada por município
  - Botão de download do ZIP (URL assinada Supabase Storage)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

# ── Paleta (espelha app.py) ────────────────────────────────────────────────────
_C = {
    "navy":        "#0B1E33",
    "navy2":       "#0f2540",
    "amber":       "#F29F05",
    "sky":         "#2d8fd4",
    "green":       "#2a9c6b",
    "red":         "#d63b3b",
    "yellow":      "#e8a020",
    "purple":      "#8b5cf6",
    "text":        "#dce8f2",
    "text2":       "#b0c4d8",
    "muted":       "#7a95ad",
}

_CND_META: dict[str, dict[str, str]] = {
    "vencida":  {"label": "VENCIDA",       "color": "#d63b3b", "icon": "🔴"},
    "urgente":  {"label": "Vence em 30d",  "color": "#F29F05", "icon": "🟡"},
    "atencao":  {"label": "Vence em 90d",  "color": "#e8a020", "icon": "🟠"},
    "ok":       {"label": "Válida +90d",   "color": "#2a9c6b", "icon": "🟢"},
    "sem_info": {"label": "Sem info",      "color": "#7a95ad", "icon": "⚪"},
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_dt(iso: str) -> str:
    """Converte ISO 8601 do Supabase para formato brasileiro legível."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return iso


def _card(value: str, label: str, sub: str = "", color: str = "#F29F05") -> None:
    st.markdown(
        f'<div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);'
        f'border-radius:12px;padding:16px 20px;text-align:center">'
        f'<div style="font-size:28px;font-weight:800;color:{color};line-height:1.1;'
        f'font-family:\'Sora\',sans-serif">{value}</div>'
        f'<div style="font-size:10.5px;font-weight:600;color:#7a95ad;'
        f'text-transform:uppercase;letter-spacing:1px;margin-top:4px">{label}</div>'
        f'{"<div style=\'font-size:11px;color:#7a95ad;margin-top:3px\'>" + sub + "</div>" if sub else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _section(title: str, icon: str = "", accent: str = "#F29F05") -> None:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'padding:13px 18px 11px;background:rgba(255,255,255,.03);'
        f'border:1px solid rgba(255,255,255,.07);border-left:3px solid {accent};'
        f'border-radius:10px;margin-bottom:12px">'
        f'<span style="font-size:15px">{icon}</span>'
        f'<span style="font-size:11.5px;font-weight:700;color:#b0c4d8;'
        f'text-transform:uppercase;letter-spacing:1.2px">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _divider(label: str = "") -> None:
    if label:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:20px 0 14px">'
            f'<div style="flex:1;height:1px;background:rgba(255,255,255,.06)"></div>'
            f'<span style="font-size:10.5px;font-weight:600;color:#7a95ad;'
            f'text-transform:uppercase;letter-spacing:1px">{label}</span>'
            f'<div style="flex:1;height:1px;background:rgba(255,255,255,.06)"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="height:1px;background:linear-gradient(90deg,'
            'transparent,rgba(242,159,5,.3),transparent);margin:18px 0"></div>',
            unsafe_allow_html=True,
        )


# ── Sub-componentes ───────────────────────────────────────────────────────────

def _render_cnd_alertas(municipios: list[dict[str, Any]]) -> None:
    """Exibe alertas de CND ordenados por urgência."""
    _section("🔔 Alertas de CND", accent="#d63b3b")

    alertas = [
        m for m in municipios
        if m.get("cnd_status") in ("vencida", "urgente", "atencao")
    ]

    if not alertas:
        st.markdown(
            '<div style="padding:18px;border:1px solid rgba(42,156,107,.25);'
            'border-radius:10px;background:rgba(42,156,107,.06);text-align:center">'
            '<span style="font-size:22px">✅</span>'
            '<p style="color:#2a9c6b;font-weight:700;margin:6px 0 0;font-size:13px">'
            'Nenhuma CND com vencimento próximo ou vencida</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Agrupa por status para contadores rápidos
    venc  = [m for m in alertas if m.get("cnd_status") == "vencida"]
    urg   = [m for m in alertas if m.get("cnd_status") == "urgente"]
    aten  = [m for m in alertas if m.get("cnd_status") == "atencao"]

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        _card(str(len(venc)),  "CNDs Vencidas",      color="#d63b3b")
    with cc2:
        _card(str(len(urg)),   "Vencem em 30 dias",  color="#F29F05")
    with cc3:
        _card(str(len(aten)),  "Vencem em 90 dias",  color="#e8a020")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Lista de alertas
    for m in alertas:
        meta  = _CND_META.get(m.get("cnd_status", "sem_info"), _CND_META["sem_info"])
        dias  = m.get("cnd_dias")
        dias_txt = (
            f"Vencida há {abs(dias)} dia(s)" if dias is not None and dias < 0
            else f"Vence em {dias} dia(s)" if dias is not None
            else "Validade não identificada"
        )
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 16px;margin-bottom:5px;'
            f'background:rgba(255,255,255,.025);border-radius:8px;'
            f'border-left:3px solid {meta["color"]}">'
            f'<div style="display:flex;align-items:center;gap:10px">'
            f'<span style="font-size:14px">{meta["icon"]}</span>'
            f'<span style="font-size:13px;color:#dce8f2;font-weight:600">{m["nome"]}</span>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:16px">'
            f'<span style="font-size:11px;color:{meta["color"]};font-weight:700">'
            f'{dias_txt}</span>'
            f'<span style="font-size:10.5px;padding:2px 8px;border-radius:12px;'
            f'background:rgba(255,255,255,.06);color:{meta["color"]};font-weight:600">'
            f'{meta["label"]}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_stats_macro(stats: dict[str, Any]) -> None:
    """Painel de métricas macro (devedores, MAED, omissões, PF)."""
    _section("📊 Painel de Acompanhamento", accent="#2d8fd4")

    totais = stats.get("totais", {})
    n_total = stats.get("total_municipios", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        _card(str(n_total),                         "Municípios",     color="#dce8f2")
    with c2:
        _card(str(totais.get("muns_dev",   0)),      "Com Devedor",
              sub=_brl(totais.get("v_devedor", 0.0)), color="#d63b3b")
    with c3:
        _card(str(totais.get("muns_maed",  0)),      "Com MAED",
              sub=_brl(totais.get("v_maed",    0.0)), color="#e8a020")
    with c4:
        _card(str(totais.get("muns_omiss", 0)),      "Com Omissões",
              sub=f"{totais.get('n_omiss', 0)} itens", color="#2d8fd4")
    with c5:
        _card(str(totais.get("muns_pf",    0)),      "Processo Fiscal",
              sub=f"{totais.get('n_pf', 0)} itens",   color="#8b5cf6")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Top devedores + breakdown de declarações
    col_top, col_bd = st.columns([1.4, 1])
    top = stats.get("top_devedores", [])
    bd  = stats.get("decl_breakdown", {})

    with col_top:
        st.markdown(
            '<p style="font-size:11px;font-weight:700;color:#7a95ad;'
            'text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">'
            '🏆 Top Devedores (valor consolidado)</p>',
            unsafe_allow_html=True,
        )
        if top:
            max_val = top[0]["valor"] if top else 1
            rank_colors = ["#d63b3b", "#d63b3b", "#F29F05", "#F29F05",
                           "#e8a020", "#e8a020", "#7a95ad", "#7a95ad"]
            for i, r in enumerate(top[:8]):
                pct = r["valor"] / max_val * 100 if max_val else 0
                col_r = rank_colors[i % len(rank_colors)]
                nome_s = r["nome"][:28] + ("…" if len(r["nome"]) > 28 else "")
                st.markdown(
                    f'<div style="margin-bottom:5px">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:11px;margin-bottom:2px">'
                    f'<span style="color:#b0c4d8"><span style="color:{col_r};'
                    f'font-weight:700;margin-right:5px">#{i+1}</span>{nome_s}</span>'
                    f'<span style="color:{col_r};font-weight:700;'
                    f'font-family:\'IBM Plex Mono\',monospace;font-size:10.5px">'
                    f'{_brl(r["valor"])}</span></div>'
                    f'<div style="background:rgba(255,255,255,.06);border-radius:3px;height:4px">'
                    f'<div style="background:{col_r};width:{pct:.0f}%;'
                    f'height:4px;border-radius:3px;opacity:.75"></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<p style="font-size:12px;color:#7a95ad">Nenhum devedor encontrado.</p>',
                unsafe_allow_html=True,
            )

    with col_bd:
        st.markdown(
            '<p style="font-size:11px;font-weight:700;color:#7a95ad;'
            'text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">'
            '📋 Omissões por Declaração</p>',
            unsafe_allow_html=True,
        )
        if bd:
            total_bd = sum(bd.values()) or 1
            _DECL_COLORS = {
                "DCTF":    "#1a6faf", "DCTFWEB": "#2d8fd4",
                "SISOBRA": "#2a9c6b", "GFIP":    "#8b5cf6",
                "ECF":     "#10b981", "PGFN":    "#d63b3b",
            }
            for decl, cnt in list(bd.items())[:8]:
                pct = cnt / total_bd * 100
                col_d = _DECL_COLORS.get(decl, "#7a95ad")
                st.markdown(
                    f'<div style="margin-bottom:5px">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:11px;margin-bottom:2px">'
                    f'<span style="color:#b0c4d8">{decl}</span>'
                    f'<span style="color:{col_d};font-weight:700">{cnt}</span></div>'
                    f'<div style="background:rgba(255,255,255,.06);border-radius:3px;height:4px">'
                    f'<div style="background:{col_d};width:{pct:.0f}%;'
                    f'height:4px;border-radius:3px"></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<p style="font-size:12px;color:#7a95ad">Nenhuma omissão encontrada.</p>',
                unsafe_allow_html=True,
            )


def _render_tabela_municipios(municipios: list[dict[str, Any]]) -> None:
    """Tabela detalhada por município com status visual."""
    _section("🗂 Detalhamento por Município", accent="#F29F05")

    if not municipios:
        st.info("Nenhum município encontrado nesta análise.")
        return

    # Cabeçalho
    hc = st.columns([2.6, .7, 1.2, .7, 1.2, .7, .6, .9])
    for col, lbl in zip(hc, ["Município", "Devedor", "Valor Dev.",
                               "MAED", "Valor MAED", "Omissões", "P.F.", "CND"]):
        col.markdown(
            f'<p style="font-size:10px;font-weight:700;color:#7a95ad;'
            f'text-transform:uppercase;letter-spacing:.8px;margin:0;padding:2px 0">'
            f'{lbl}</p>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,.09);margin:4px 0 6px"></div>',
        unsafe_allow_html=True,
    )

    for i, m in enumerate(municipios):
        cnd_meta = _CND_META.get(m.get("cnd_status", "sem_info"), _CND_META["sem_info"])
        dias     = m.get("cnd_dias")
        dias_txt = (
            f"{abs(dias)}d atrás" if dias is not None and dias < 0
            else f"{dias}d"       if dias is not None
            else "—"
        )
        status_dot = (
            "🔴" if m.get("n_dev", 0) > 0
            else "🟡" if (m.get("n_maed", 0) or m.get("n_omiss", 0)) > 0
            else "🟢"
        )
        rc = st.columns([2.6, .7, 1.2, .7, 1.2, .7, .6, .9])

        rc[0].markdown(
            f'<p style="font-size:12px;color:#dce8f2;margin:0;padding:3px 0">'
            f'{status_dot} {m["nome"]}</p>',
            unsafe_allow_html=True,
        )
        # Devedor
        n_dev = m.get("n_dev", 0)
        rc[1].markdown(
            f'<p style="font-size:12px;font-weight:{"700" if n_dev else "400"};'
            f'color:{"#d63b3b" if n_dev else "#7a95ad"};margin:0;padding:3px 0">'
            f'{n_dev or "—"}</p>', unsafe_allow_html=True)
        # Valor Devedor
        v_dev = m.get("v_dev", 0.0)
        rc[2].markdown(
            f'<p style="font-size:10.5px;font-family:\'IBM Plex Mono\',monospace;'
            f'color:{"#d63b3b" if v_dev > 0 else "#7a95ad"};margin:0;padding:3px 0">'
            f'{"<b>" + _brl(v_dev) + "</b>" if v_dev > 0 else "—"}</p>',
            unsafe_allow_html=True,
        )
        # MAED
        n_maed = m.get("n_maed", 0)
        rc[3].markdown(
            f'<p style="font-size:12px;font-weight:{"700" if n_maed else "400"};'
            f'color:{"#e8a020" if n_maed else "#7a95ad"};margin:0;padding:3px 0">'
            f'{n_maed or "—"}</p>', unsafe_allow_html=True)
        # Valor MAED
        v_maed = m.get("v_maed", 0.0)
        rc[4].markdown(
            f'<p style="font-size:10.5px;font-family:\'IBM Plex Mono\',monospace;'
            f'color:{"#e8a020" if v_maed > 0 else "#7a95ad"};margin:0;padding:3px 0">'
            f'{"<b>" + _brl(v_maed) + "</b>" if v_maed > 0 else "—"}</p>',
            unsafe_allow_html=True,
        )
        # Omissões
        n_omiss = m.get("n_omiss", 0)
        rc[5].markdown(
            f'<p style="font-size:12px;color:{"#2d8fd4" if n_omiss else "#7a95ad"};'
            f'margin:0;padding:3px 0">{n_omiss or "—"}</p>', unsafe_allow_html=True)
        # PF
        n_pf = m.get("n_pf", 0)
        rc[6].markdown(
            f'<p style="font-size:12px;color:{"#8b5cf6" if n_pf else "#7a95ad"};'
            f'margin:0;padding:3px 0">{n_pf or "—"}</p>', unsafe_allow_html=True)
        # CND
        rc[7].markdown(
            f'<p style="font-size:10.5px;color:{cnd_meta["color"]};'
            f'font-weight:600;margin:0;padding:3px 0">'
            f'{cnd_meta["icon"]} {dias_txt}</p>',
            unsafe_allow_html=True,
        )


# ── Componente principal ──────────────────────────────────────────────────────

def render_dashboard_socios() -> None:
    """
    Entry point do dashboard de sócios.
    Chamado pelo app.py quando ss.role == 'socio'.
    """
    # Import lazy para não quebrar se supabase não estiver configurado
    try:
        from supabase_client import (
            buscar_municipios,
            buscar_stats,
            gerar_url_download,
            listar_analises,
            supabase_disponivel,
        )
    except ImportError as exc:
        st.error(f"❌ Módulo supabase_client não encontrado: {exc}")
        return

    ss = st.session_state

    # ── Header sócios ─────────────────────────────────────────────────────────
    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:14px;padding:6px 0 2px">'
            '<div style="width:42px;height:42px;flex-shrink:0;'
            'background:linear-gradient(145deg,#2a9c6b,#1a7a52);border-radius:10px;'
            'display:flex;align-items:center;justify-content:center;font-size:20px;'
            'box-shadow:0 4px 14px rgba(42,156,107,.4)">📈</div>'
            '<div>'
            '<div style="font-size:18px;font-weight:800;color:#dce8f2;line-height:1.2">'
            'ConPrev'
            '<span style="font-weight:400;color:#7a95ad;font-size:14px;margin-left:6px">'
            'Dashboard Sócios</span></div>'
            '<div style="font-size:11px;color:#7a95ad;margin-top:2px">'
            'Acompanhamento em tempo real · Acesso somente leitura</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("<div style='padding-top:10px'>", unsafe_allow_html=True)
        if st.button("↩ Sair", key="socio_logout"):
            ss.authenticated = False
            ss.role = None
            ss.pop("socio_analise_id", None)
            ss.pop("socio_stats", None)
            ss.pop("socio_municipios", None)
            st.rerun()

    _divider()

    # ── Verifica Supabase ──────────────────────────────────────────────────────
    if not supabase_disponivel():
        st.error(
            "⚠️ Supabase não configurado. "
            "Verifique SUPABASE_URL e SUPABASE_KEY em `.streamlit/secrets.toml`."
        )
        return

    # ── Seletor de análises ───────────────────────────────────────────────────
    with st.spinner("Carregando análises publicadas…"):
        analises = listar_analises(limit=20)

    if not analises:
        st.markdown(
            '<div style="padding:32px;text-align:center;border:1px dashed rgba(255,255,255,.1);'
            'border-radius:12px;margin-top:20px">'
            '<span style="font-size:32px">📭</span>'
            '<p style="color:#7a95ad;margin:10px 0 0;font-size:14px">'
            'Nenhuma análise publicada ainda.<br>'
            '<span style="font-size:12px">Aguarde o admin publicar a próxima análise.</span></p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Monta opções do seletor
    opcoes: dict[str, str] = {}  # label → id
    for a in analises:
        dt_fmt = _fmt_dt(a.get("created_at", ""))
        ref    = a.get("ref_date", "—")
        n_mun  = a.get("total_municipios", 0)
        label  = f"📅 {dt_fmt}  ·  Ref. {ref}  ·  {n_mun} municípios"
        opcoes[label] = a["id"]

    _section("📂 Selecione a Análise", "🗓", accent="#2d8fd4")
    escolhida_label = st.selectbox(
        "Análises disponíveis",
        options=list(opcoes.keys()),
        key="socio_analise_select",
        label_visibility="collapsed",
    )
    analise_id: str = opcoes[escolhida_label]

    # Cache na session_state para evitar re-fetch a cada interação
    if ss.get("socio_analise_id") != analise_id:
        with st.spinner("Carregando dados da análise…"):
            ss["socio_analise_id"]    = analise_id
            ss["socio_stats"]         = buscar_stats(analise_id)
            ss["socio_municipios"]    = buscar_municipios(analise_id)

    stats:     dict            = ss.get("socio_stats", {})
    municipios: list[dict]     = ss.get("socio_municipios", [])

    if not stats:
        st.warning("⚠️ Não foi possível carregar os dados desta análise.")
        return

    # Metadados da análise selecionada
    ref_date   = stats.get("_ref_date", "—")
    created_at = _fmt_dt(stats.get("_created_at", ""))
    zip_ts     = stats.get("_zip_ts", "")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;'
        f'padding:10px 16px;background:rgba(45,143,212,.06);'
        f'border:1px solid rgba(45,143,212,.2);border-radius:8px;margin-bottom:18px">'
        f'<span style="font-size:13px">ℹ️</span>'
        f'<span style="font-size:12px;color:#b0c4d8">'
        f'Publicada em <b style="color:#dce8f2">{created_at}</b>'
        f' &nbsp;·&nbsp; Referência: <b style="color:#dce8f2">{ref_date}</b>'
        f' &nbsp;·&nbsp; {stats.get("total_municipios", 0)} municípios analisados'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # ── Download do ZIP ───────────────────────────────────────────────────────
    if zip_ts:
        _section("⬇️ Relatórios em PDF", accent="#2a9c6b")
        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            if st.button("🔗 Gerar link de download (válido 1h)", key="btn_dl",
                         use_container_width=True):
                with st.spinner("Gerando URL assinada…"):
                    url = gerar_url_download(analise_id, zip_ts)
                if url:
                    ss["socio_dl_url"] = url
                else:
                    st.error("❌ Não foi possível gerar o link. Tente novamente.")

        if ss.get("socio_dl_url"):
            with col_info:
                st.markdown(
                    f'<div style="padding:10px 16px;background:rgba(42,156,107,.08);'
                    f'border:1px solid rgba(42,156,107,.25);border-radius:8px">'
                    f'<p style="font-size:12px;color:#4dd8a0;margin:0 0 6px;font-weight:700">'
                    f'✅ Link gerado com sucesso</p>'
                    f'<a href="{ss["socio_dl_url"]}" target="_blank" '
                    f'style="font-size:11.5px;color:#2d8fd4;word-break:break-all">'
                    f'⬇️ Clique aqui para baixar o ZIP completo</a>'
                    f'<p style="font-size:10.5px;color:#7a95ad;margin:5px 0 0">'
                    f'⏱ Expira em 1 hora</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        _divider()

    # ── Alertas CND ───────────────────────────────────────────────────────────
    _render_cnd_alertas(municipios)

    _divider()

    # ── Painel de estatísticas ────────────────────────────────────────────────
    _render_stats_macro(stats)

    _divider("Detalhamento por Município")

    # ── Tabela de municípios ──────────────────────────────────────────────────
    _render_tabela_municipios(municipios)

    # Rodapé
    st.markdown(
        '<div style="text-align:center;padding:24px 0 8px">'
        '<p style="font-size:11px;color:#7a95ad">'
        '🔒 Dados restritos &middot; Conprev Assessoria Municipal &middot; '
        'Acesso somente leitura</p>'
        '</div>',
        unsafe_allow_html=True,
    )
