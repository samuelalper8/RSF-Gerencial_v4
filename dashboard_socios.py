"""
dashboard_socios.py — Dashboard de Acompanhamento para Sócios ConPrev v2
"""
from __future__ import annotations
import io, time
from datetime import datetime
from typing import Any
import streamlit as st

_CND_META = {
    "vencida":  {"label": "VENCIDA",      "color": "#d63b3b", "icon": "🔴"},
    "urgente":  {"label": "Vence em 30d", "color": "#F29F05", "icon": "🟡"},
    "atencao":  {"label": "Vence em 90d", "color": "#e8a020", "icon": "🟠"},
    "ok":       {"label": "Válida +90d",  "color": "#2a9c6b", "icon": "🟢"},
    "sem_info": {"label": "Sem info",     "color": "#7a95ad", "icon": "⚪"},
}

def _brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return "—"

def _fmt_dt(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z","+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return iso

def _card(value, label, sub="", color="#F29F05"):
    st.markdown(
        f'<div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);'
        f'border-radius:12px;padding:16px 20px;text-align:center">'
        f'<div style="font-size:28px;font-weight:800;color:{color};line-height:1.1;'
        f'font-family:Sora,sans-serif">{value}</div>'
        f'<div style="font-size:10.5px;font-weight:600;color:#7a95ad;'
        f'text-transform:uppercase;letter-spacing:1px;margin-top:4px">{label}</div>'
        f'{"<div style=font-size:11px;color:#7a95ad;margin-top:3px>" + sub + "</div>" if sub else ""}'
        f'</div>', unsafe_allow_html=True)

def _section(title, icon="", accent="#F29F05"):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;padding:13px 18px 11px;'
        f'background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);'
        f'border-left:3px solid {accent};border-radius:10px;margin-bottom:12px">'
        f'<span style="font-size:15px">{icon}</span>'
        f'<span style="font-size:11.5px;font-weight:700;color:#b0c4d8;'
        f'text-transform:uppercase;letter-spacing:1.2px">{title}</span></div>',
        unsafe_allow_html=True)

def _divider(label=""):
    if label:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:20px 0 14px">'
            f'<div style="flex:1;height:1px;background:rgba(255,255,255,.06)"></div>'
            f'<span style="font-size:10.5px;font-weight:600;color:#7a95ad;'
            f'text-transform:uppercase;letter-spacing:1px">{label}</span>'
            f'<div style="flex:1;height:1px;background:rgba(255,255,255,.06)"></div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="height:1px;background:linear-gradient(90deg,'
            'transparent,rgba(242,159,5,.3),transparent);margin:18px 0"></div>',
            unsafe_allow_html=True)

# ── Tabela de DEVEDORES ───────────────────────────────────────────────────────
def _render_devedores(itens):
    if not itens:
        st.markdown('<p style="font-size:12px;color:#7a95ad;padding:6px 0">Nenhum devedor.</p>', unsafe_allow_html=True); return
    grupos = {}
    for it in itens:
        key = f"{it.get('orgao') or 'Município'} ||| {it.get('cnpj') or '—'}"
        grupos.setdefault(key, []).append(it)
    for gk, gitens in grupos.items():
        orgao, cnpj = gk.split(" ||| ", 1)
        st.markdown(
            f'<div style="padding:8px 12px;background:rgba(214,59,59,.07);'
            f'border-left:3px solid #d63b3b;border-radius:6px;margin:10px 0 4px">'
            f'<b style="font-size:12px;color:#dce8f2">{orgao}</b>'
            f'<span style="font-size:11px;color:#7a95ad;margin-left:10px;'
            f'font-family:IBM Plex Mono,monospace">CNPJ: {cnpj}</span></div>',
            unsafe_allow_html=True)
        cols = st.columns([1.4,1.4,.8,.9,.9,.85,1.1])
        for c, l in zip(cols, ["Cód./Rubrica","Competência","Vencimento","Original","Devedor","Multa+Juros","Consolidado"]):
            c.markdown(f'<p style="font-size:9px;font-weight:700;color:#7a95ad;text-transform:uppercase;letter-spacing:.6px;margin:2px 0">{l}</p>', unsafe_allow_html=True)
        for it in gitens:
            rc = st.columns([1.4,1.4,.8,.9,.9,.85,1.1])
            cod = f"{it.get('cod') or ''} – {it.get('desc_rubrica') or ''}".strip(" –")
            multa = (it.get("v_multa") or 0.0) + (it.get("v_juros") or 0.0)
            residual = it.get("residual", False)
            rc[0].markdown(f'<p style="font-size:10.5px;color:#b0c4d8;margin:1px 0;font-family:IBM Plex Mono,monospace">{cod[:30]}</p>', unsafe_allow_html=True)
            rc[1].markdown(f'<p style="font-size:10.5px;color:#b0c4d8;margin:1px 0">{it.get("comp") or "—"}</p>', unsafe_allow_html=True)
            rc[2].markdown(f'<p style="font-size:10.5px;color:#7a95ad;margin:1px 0">{it.get("venc") or "—"}</p>', unsafe_allow_html=True)
            rc[3].markdown(f'<p style="font-size:10.5px;color:#7a95ad;margin:1px 0">{_brl(it.get("v_original"))}</p>', unsafe_allow_html=True)
            rc[4].markdown(f'<p style="font-size:10.5px;font-weight:700;color:#d63b3b;margin:1px 0">{_brl(it.get("v_devedor"))}</p>', unsafe_allow_html=True)
            rc[5].markdown(f'<p style="font-size:10.5px;color:#e8a020;margin:1px 0">{"—" if not multa else _brl(multa)}</p>', unsafe_allow_html=True)
            cc = "#e8a020" if residual else "#d63b3b"
            rc[6].markdown(f'<p style="font-size:10.5px;font-weight:700;color:{cc};margin:1px 0">{_brl(it.get("v_consolidado"))}{"  ⚠️" if residual else ""}</p>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px;background:rgba(255,255,255,.04);margin:4px 0"></div>', unsafe_allow_html=True)

# ── Tabela de MAED ────────────────────────────────────────────────────────────
def _render_maed(itens):
    if not itens:
        st.markdown('<p style="font-size:12px;color:#7a95ad;padding:6px 0">Nenhum MAED.</p>', unsafe_allow_html=True); return
    grupos = {}
    for it in itens:
        key = f"{it.get('orgao') or 'Município'} ||| {it.get('cnpj') or '—'}"
        grupos.setdefault(key, []).append(it)
    for gk, gitens in grupos.items():
        orgao, cnpj = gk.split(" ||| ", 1)
        st.markdown(
            f'<div style="padding:8px 12px;background:rgba(232,160,32,.07);'
            f'border-left:3px solid #e8a020;border-radius:6px;margin:10px 0 4px">'
            f'<b style="font-size:12px;color:#dce8f2">{orgao}</b>'
            f'<span style="font-size:11px;color:#7a95ad;margin-left:10px;'
            f'font-family:IBM Plex Mono,monospace">CNPJ: {cnpj}</span></div>',
            unsafe_allow_html=True)
        cols = st.columns([1.6,1.4,1.0,1.0,1.0])
        for c, l in zip(cols, ["Cód./Rubrica","Competência","Vencimento","Saldo Devedor","Situação"]):
            c.markdown(f'<p style="font-size:9px;font-weight:700;color:#7a95ad;text-transform:uppercase;letter-spacing:.6px;margin:2px 0">{l}</p>', unsafe_allow_html=True)
        for it in gitens:
            rc = st.columns([1.6,1.4,1.0,1.0,1.0])
            cod = f"{it.get('cod') or ''} – {it.get('desc_rubrica') or ''}".strip(" –")
            rc[0].markdown(f'<p style="font-size:10.5px;color:#b0c4d8;margin:1px 0;font-family:IBM Plex Mono,monospace">{cod[:32]}</p>', unsafe_allow_html=True)
            rc[1].markdown(f'<p style="font-size:10.5px;color:#b0c4d8;margin:1px 0">{it.get("comp") or "—"}</p>', unsafe_allow_html=True)
            rc[2].markdown(f'<p style="font-size:10.5px;color:#7a95ad;margin:1px 0">{it.get("venc") or "—"}</p>', unsafe_allow_html=True)
            rc[3].markdown(f'<p style="font-size:10.5px;font-weight:700;color:#e8a020;margin:1px 0">{_brl(it.get("v_devedor"))}</p>', unsafe_allow_html=True)
            rc[4].markdown(f'<p style="font-size:10.5px;color:#7a95ad;margin:1px 0">{it.get("situacao") or "—"}</p>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px;background:rgba(255,255,255,.04);margin:4px 0"></div>', unsafe_allow_html=True)

# ── Tabela de OMISSÕES ────────────────────────────────────────────────────────
def _render_omissoes(itens):
    if not itens:
        st.markdown('<p style="font-size:12px;color:#7a95ad;padding:6px 0">Nenhuma omissão.</p>', unsafe_allow_html=True); return
    grupos = {}
    for it in itens:
        key = f"{it.get('orgao') or 'Município'} ||| {it.get('cnpj') or '—'}"
        grupos.setdefault(key, []).append(it)
    for gk, gitens in grupos.items():
        orgao, cnpj = gk.split(" ||| ", 1)
        st.markdown(
            f'<div style="padding:8px 12px;background:rgba(45,143,212,.07);'
            f'border-left:3px solid #2d8fd4;border-radius:6px;margin:10px 0 4px">'
            f'<b style="font-size:12px;color:#dce8f2">{orgao}</b>'
            f'<span style="font-size:11px;color:#7a95ad;margin-left:10px;'
            f'font-family:IBM Plex Mono,monospace">CNPJ: {cnpj}</span></div>',
            unsafe_allow_html=True)
        for it in gitens:
            decl = it.get("tipo_declaracao") or "NÃO ID."
            per  = it.get("periodo") or "(período não identificado)"
            st.markdown(
                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                f'padding:4px 0 4px 8px;border-bottom:1px solid rgba(255,255,255,.03)">'
                f'<span style="font-size:10px;font-weight:700;padding:2px 7px;'
                f'border-radius:10px;background:rgba(45,143,212,.15);color:#2d8fd4;'
                f'white-space:nowrap;flex-shrink:0">{decl}</span>'
                f'<span style="font-size:11px;color:#b0c4d8">{per}</span>'
                f'</div>', unsafe_allow_html=True)

# ── Tabela de PROCESSOS FISCAIS ───────────────────────────────────────────────
def _render_pf(itens):
    if not itens:
        st.markdown('<p style="font-size:12px;color:#7a95ad;padding:6px 0">Nenhum processo fiscal.</p>', unsafe_allow_html=True); return
    for it in itens:
        st.markdown(
            f'<div style="display:flex;gap:12px;align-items:center;'
            f'padding:6px 8px;background:rgba(139,92,246,.06);'
            f'border-left:3px solid #8b5cf6;border-radius:6px;margin:4px 0">'
            f'<span style="font-size:11px;font-weight:700;color:#8b5cf6;'
            f'font-family:IBM Plex Mono,monospace">{it.get("processo") or "—"}</span>'
            f'<span style="font-size:11px;color:#7a95ad">{it.get("situacao") or ""}</span>'
            f'<span style="font-size:11px;color:#b0c4d8">'
            f'{it.get("orgao") or ""}'
            f'{"  |  CNPJ: " + it.get("cnpj") if it.get("cnpj") else ""}'
            f'</span></div>', unsafe_allow_html=True)

# ── Detalhamento de município ─────────────────────────────────────────────────
def _render_detalhe_municipio(analise_id, municipio, m_stats):
    ss = st.session_state
    cache_key = f"itens_{analise_id}_{municipio}"

    if cache_key not in ss:
        try:
            from supabase_client import buscar_itens_municipio
            with st.spinner(f"Carregando detalhes de {municipio}..."):
                ss[cache_key] = buscar_itens_municipio(analise_id, municipio)
        except Exception as e:
            st.error(f"Erro ao carregar itens: {e}")
            return

    itens_por_tipo = ss[cache_key]
    devs  = itens_por_tipo.get("DEVEDOR", [])
    maeds = itens_por_tipo.get("MAED", [])
    omiss = itens_por_tipo.get("OMISSÃO", [])
    pfs   = itens_por_tipo.get("PROCESSO FISCAL", [])

    has_any = any([devs, maeds, omiss, pfs])
    if not has_any:
        st.info("Nenhuma restrição encontrada para este município nesta análise.")
        return

    tabs = []
    tab_labels = []
    if devs:  tab_labels.append(f"🔴 Devedor ({len(devs)})")
    if maeds: tab_labels.append(f"🟡 MAED ({len(maeds)})")
    if omiss: tab_labels.append(f"🔵 Omissões ({len(omiss)})")
    if pfs:   tab_labels.append(f"🟣 Proc. Fiscal ({len(pfs)})")

    if not tab_labels:
        return

    tabs = st.tabs(tab_labels)
    ti = 0
    if devs:
        with tabs[ti]: _render_devedores(devs)
        ti += 1
    if maeds:
        with tabs[ti]: _render_maed(maeds)
        ti += 1
    if omiss:
        with tabs[ti]: _render_omissoes(omiss)
        ti += 1
    if pfs:
        with tabs[ti]: _render_pf(pfs)

# ── Alertas de CND ────────────────────────────────────────────────────────────
def _render_cnd_alertas(municipios):
    _section("🔔 Alertas de CND", accent="#d63b3b")
    alertas = [m for m in municipios if m.get("cnd_status") in ("vencida","urgente","atencao")]
    if not alertas:
        st.markdown(
            '<div style="padding:18px;border:1px solid rgba(42,156,107,.25);'
            'border-radius:10px;background:rgba(42,156,107,.06);text-align:center">'
            '<span style="font-size:22px">✅</span>'
            '<p style="color:#2a9c6b;font-weight:700;margin:6px 0 0;font-size:13px">'
            'Nenhuma CND com vencimento próximo ou vencida</p></div>',
            unsafe_allow_html=True); return

    cc1,cc2,cc3 = st.columns(3)
    venc = [m for m in alertas if m.get("cnd_status")=="vencida"]
    urg  = [m for m in alertas if m.get("cnd_status")=="urgente"]
    aten = [m for m in alertas if m.get("cnd_status")=="atencao"]
    with cc1: _card(str(len(venc)), "CNDs Vencidas",    color="#d63b3b")
    with cc2: _card(str(len(urg)),  "Vencem em 30d",    color="#F29F05")
    with cc3: _card(str(len(aten)), "Vencem em 90d",    color="#e8a020")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    for m in alertas:
        meta = _CND_META.get(m.get("cnd_status","sem_info"), _CND_META["sem_info"])
        dias = m.get("cnd_dias")
        dias_txt = (f"Vencida há {abs(dias)}d" if dias is not None and dias < 0
                    else f"Vence em {dias}d" if dias is not None else "—")
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 16px;margin-bottom:4px;background:rgba(255,255,255,.025);'
            f'border-radius:8px;border-left:3px solid {meta["color"]}">'
            f'<span style="font-size:13px;color:#dce8f2;font-weight:600">'
            f'{meta["icon"]} {m["nome"]}</span>'
            f'<span style="font-size:11px;color:{meta["color"]};font-weight:700">'
            f'{dias_txt} &nbsp;&nbsp; {meta["label"]}</span></div>',
            unsafe_allow_html=True)

# ── Painel macro ──────────────────────────────────────────────────────────────
def _render_stats_macro(stats):
    _section("📊 Painel de Acompanhamento", accent="#2d8fd4")
    totais = stats.get("totais",{})
    n_total = stats.get("total_municipios",0)
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: _card(str(n_total),                          "Municípios",    color="#dce8f2")
    with c2: _card(str(totais.get("muns_dev",0)),          "Com Devedor",   sub=_brl(totais.get("v_devedor",0.0)), color="#d63b3b")
    with c3: _card(str(totais.get("muns_maed",0)),         "Com MAED",      sub=_brl(totais.get("v_maed",0.0)),    color="#e8a020")
    with c4: _card(str(totais.get("muns_omiss",0)),        "Com Omissões",  sub=f"{totais.get('n_omiss',0)} itens", color="#2d8fd4")
    with c5: _card(str(totais.get("muns_pf",0)),           "Proc. Fiscal",  sub=f"{totais.get('n_pf',0)} itens",   color="#8b5cf6")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col_top, col_bd = st.columns([1.4,1])
    top = stats.get("top_devedores",[])
    bd  = stats.get("decl_breakdown",{})
    _RANK_COLORS = ["#d63b3b","#d63b3b","#F29F05","#F29F05","#e8a020","#e8a020","#7a95ad","#7a95ad"]
    _DECL_COLORS = {"DCTF":"#1a6faf","DCTFWEB":"#2d8fd4","SISOBRA":"#2a9c6b","GFIP":"#8b5cf6","ECF":"#10b981","PGFN":"#d63b3b"}

    with col_top:
        st.markdown('<p style="font-size:11px;font-weight:700;color:#7a95ad;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">🏆 Top Devedores</p>', unsafe_allow_html=True)
        if top:
            max_val = top[0]["valor"] if top else 1
            for i,r in enumerate(top[:8]):
                pct = r["valor"]/max_val*100 if max_val else 0
                col_r = _RANK_COLORS[i%len(_RANK_COLORS)]
                nome_s = r["nome"][:28]+("…" if len(r["nome"])>28 else "")
                st.markdown(
                    f'<div style="margin-bottom:5px">'
                    f'<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px">'
                    f'<span style="color:#b0c4d8"><span style="color:{col_r};font-weight:700;margin-right:5px">#{i+1}</span>{nome_s}</span>'
                    f'<span style="color:{col_r};font-weight:700;font-family:IBM Plex Mono,monospace;font-size:10.5px">{_brl(r["valor"])}</span></div>'
                    f'<div style="background:rgba(255,255,255,.06);border-radius:3px;height:4px">'
                    f'<div style="background:{col_r};width:{pct:.0f}%;height:4px;border-radius:3px;opacity:.75"></div>'
                    f'</div></div>', unsafe_allow_html=True)
    with col_bd:
        st.markdown('<p style="font-size:11px;font-weight:700;color:#7a95ad;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">📋 Omissões por Declaração</p>', unsafe_allow_html=True)
        if bd:
            total_bd = sum(bd.values()) or 1
            for decl,cnt in list(bd.items())[:8]:
                pct = cnt/total_bd*100
                col_d = _DECL_COLORS.get(decl,"#7a95ad")
                st.markdown(
                    f'<div style="margin-bottom:5px">'
                    f'<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px">'
                    f'<span style="color:#b0c4d8">{decl}</span>'
                    f'<span style="color:{col_d};font-weight:700">{cnt}</span></div>'
                    f'<div style="background:rgba(255,255,255,.06);border-radius:3px;height:4px">'
                    f'<div style="background:{col_d};width:{pct:.0f}%;height:4px;border-radius:3px"></div>'
                    f'</div></div>', unsafe_allow_html=True)

# ── Tabela de municípios com expanders ───────────────────────────────────────
def _render_tabela_municipios(municipios, analise_id, stats):
    _section("🗂 Detalhamento por Município", accent="#F29F05")
    if not municipios:
        st.info("Nenhum município encontrado."); return

    # Cabeçalho
    hc = st.columns([2.4,.7,1.1,.7,1.1,.65,.55,.85])
    for c,l in zip(hc, ["Município","Dev.","Valor Dev.","MAED","Valor MAED","Omiss.","P.F.","CND"]):
        c.markdown(f'<p style="font-size:9.5px;font-weight:700;color:#7a95ad;text-transform:uppercase;letter-spacing:.7px;margin:0;padding:2px 0">{l}</p>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:rgba(255,255,255,.09);margin:4px 0 6px"></div>', unsafe_allow_html=True)

    # Obtém mapa nome→stats para passar ao detalhe
    pm_map = {m["nome"]: m for m in (stats.get("por_municipio") or [])}

    for m in municipios:
        cnd_meta = _CND_META.get(m.get("cnd_status","sem_info"), _CND_META["sem_info"])
        dias = m.get("cnd_dias")
        dias_txt = (f"{abs(dias)}d atrás" if dias is not None and dias < 0
                    else f"{dias}d" if dias is not None else "—")
        status_dot = ("🔴" if m.get("n_dev",0)>0
                      else "🟡" if (m.get("n_maed",0) or m.get("n_omiss",0))>0
                      else "🟢")
        has_issues = any(m.get(k,0) for k in ("n_dev","n_maed","n_omiss","n_pf"))

        # Linha resumo em expander
        with st.expander(
            f"{status_dot}  {m['nome']}"
            + (f"   |  Dev: {_brl(m.get('v_dev',0))}" if m.get('n_dev',0) else "")
            + (f"  |  MAED: {_brl(m.get('v_maed',0))}" if m.get('n_maed',0) else "")
            + (f"  |  Omiss: {m.get('n_omiss',0)}" if m.get('n_omiss',0) else "")
            + (f"  |  CND: {cnd_meta['label']}" if m.get('cnd_status') in ('vencida','urgente') else ""),
            expanded=False
        ):
            # Mini-métricas
            mc1,mc2,mc3,mc4,mc5 = st.columns(5)
            with mc1: _card(str(m.get("n_dev",0)),   "Devedores",    sub=_brl(m.get("v_dev",0.0)),  color="#d63b3b")
            with mc2: _card(str(m.get("n_maed",0)),  "MAED",         sub=_brl(m.get("v_maed",0.0)), color="#e8a020")
            with mc3: _card(str(m.get("n_omiss",0)), "Omissões",     color="#2d8fd4")
            with mc4: _card(str(m.get("n_pf",0)),    "Proc. Fiscal", color="#8b5cf6")
            with mc5: _card(dias_txt, "CND",          color=cnd_meta["color"])

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            if has_issues:
                _render_detalhe_municipio(analise_id, m["nome"], pm_map.get(m["nome"],{}))
            else:
                st.success("✅ Município sem restrições nesta análise.")

# ── PDF do dashboard ──────────────────────────────────────────────────────────
def _gerar_pdf_dashboard(stats, municipios, itens_todos, ref_date, created_at):
    """
    Gera PDF com layout ConPrev contendo:
     - Capa com resumo executivo
     - Painel macro (top devedores, omissões por declaração, status CND)
     - Uma seção por município com detalhamento completo
    """
    try:
        import fitz
    except ImportError:
        return None, "PyMuPDF não instalado."

    W, H = 841.89, 595.28
    ML, MR = 38.0, 38.0
    HDR_H  = 66.0
    YBOT   = H - 30.0
    CW     = W - ML - MR
    NAVY   = (0.043, 0.118, 0.200)
    NAVY2  = (0.059, 0.157, 0.255)
    AMBER  = (0.949, 0.624, 0.020)
    AMBER_LT=(1.0, 0.780, 0.200)
    SKY    = (0.176, 0.561, 0.831)
    GREEN  = (0.165, 0.612, 0.420)
    RED    = (0.839, 0.231, 0.231)
    YELLOW = (0.910, 0.627, 0.125)
    PURPLE = (0.545, 0.361, 0.965)
    WHITE  = (1.0, 1.0, 1.0)
    DARK   = (0.10, 0.16, 0.24)
    MID    = (0.42, 0.50, 0.60)
    GRAY   = (0.965, 0.972, 0.983)

    FN_R = "Helvetica"
    FN_B = "Helvetica-Bold"

    def tw(t, fn, fs):
        try:    return fitz.get_text_length(t, fontname=fn, fontsize=fs)
        except: return len(t)*fs*0.56

    def fill(pg, x0,y0,x1,y1, col, r=None):
        pg.draw_rect(fitz.Rect(x0,y0,x1,y1), color=None, fill=col, width=0, radius=r)

    def txt(pg, x,y, s, fn, fs, col=DARK):
        pg.insert_text(fitz.Point(x,y), s, fontname=fn, fontsize=fs, fill=col)
        return tw(s,fn,fs)

    def hline(pg, x0,y,x1, col=(0.875,0.9,0.93), w=0.5):
        pg.draw_line(fitz.Point(x0,y), fitz.Point(x1,y), color=col, width=w)

    def draw_hdr(pg, titulo, pnum):
        fill(pg, 0,0,W,HDR_H, NAVY)
        fill(pg, 0,HDR_H-2.5,W,HDR_H, AMBER)
        txt(pg, ML, 35, titulo, FN_B, 13, WHITE)
        info = f"Gerado em {time.strftime('%d/%m/%Y às %H:%M')}   ·   Referência: {ref_date}   ·   ConPrev Assessoria Municipal"
        txt(pg, ML, 52, info, FN_R, 7.5, AMBER_LT)
        pg_t = f"pág. {pnum}"
        txt(pg, W-MR-tw(pg_t,FN_R,8)-2, 52, pg_t, FN_R, 8, (0.5,0.62,0.73))
        return HDR_H + 10.0

    doc = fitz.open()
    pnum = 0

    def new_page(titulo):
        nonlocal pnum
        pnum += 1
        pg = doc.new_page(width=W, height=H)
        y = draw_hdr(pg, titulo, pnum)
        return pg, y

    totais = stats.get("totais",{})
    top    = stats.get("top_devedores",[])
    bd     = stats.get("decl_breakdown",{})
    cnd    = stats.get("cnd_status",{})

    # ── CAPA ──────────────────────────────────────────────────────────────────
    pg, y = new_page("RELATÓRIO GERENCIAL CONSOLIDADO · Dashboard Sócios")
    fill(pg, ML,y, W-MR, y+2, AMBER)
    y += 10
    txt(pg, ML, y+14, "RESUMO EXECUTIVO", FN_B, 11, SKY)
    y += 24

    # 5 métricas em boxes
    bw = CW/5 - 4
    boxes = [
        (str(stats.get("total_municipios",0)), "Municípios", (0.6,0.7,0.8)),
        (str(totais.get("muns_dev",0)),         "Com Devedor", RED),
        (str(totais.get("muns_maed",0)),        "Com MAED",   YELLOW),
        (str(totais.get("muns_omiss",0)),       "Com Omissões", SKY),
        (str(totais.get("muns_pf",0)),          "Proc. Fiscal", PURPLE),
    ]
    for i,(val,lbl,col) in enumerate(boxes):
        bx = ML + i*(bw+5)
        fill(pg, bx, y, bx+bw, y+52, GRAY, r=6)
        fill(pg, bx, y, bx+bw, y+5, col, r=3)
        vw = tw(val,FN_B,20)
        txt(pg, bx+(bw-vw)/2, y+30, val, FN_B, 20, col)
        lw = tw(lbl,FN_R,8)
        txt(pg, bx+(bw-lw)/2, y+46, lbl, FN_R, 8, MID)
    y += 66

    # Valores totais
    vals = [
        (f"Total Devedor: {_brl(totais.get('v_devedor',0.0))}", RED),
        (f"Total MAED: {_brl(totais.get('v_maed',0.0))}",       YELLOW),
        (f"Omissões: {totais.get('n_omiss',0)} itens",          SKY),
        (f"Processos: {totais.get('n_pf',0)} itens",            PURPLE),
    ]
    for vt,col in vals:
        txt(pg, ML, y, vt, FN_B, 10, col)
        y += 16
    y += 6

    # Top devedores
    hline(pg, ML, y, W-MR)
    y += 10
    txt(pg, ML, y, "TOP DEVEDORES", FN_B, 9, SKY)
    y += 14
    max_v = top[0]["valor"] if top else 1
    for i,r in enumerate(top[:8]):
        pct = r["valor"]/max_v if max_v else 0
        bar_w = (CW*0.45)*pct
        fill(pg, ML, y-8, ML+bar_w, y-1, (*RED,0.35) if i<2 else (*YELLOW,0.35))
        rank_s = f"#{i+1}  {r['nome'][:30]}"
        txt(pg, ML+2, y, rank_s, FN_R, 9, DARK)
        val_s = _brl(r["valor"])
        txt(pg, ML+CW*0.45+4, y, val_s, FN_B, 9, RED if i<2 else YELLOW)
        y += 13
    y += 6

    # CND status
    hline(pg, ML, y, W-MR); y += 10
    txt(pg, ML, y, "STATUS DAS CNDs", FN_B, 9, SKY); y += 14
    cnd_items = [
        (cnd.get("vencidas",0), "Vencidas",       RED),
        (cnd.get("urgente",0),  "Vencem em 30d",  AMBER),
        (cnd.get("atencao",0),  "Vencem em 90d",  YELLOW),
        (cnd.get("ok",0),       "Válidas (+90d)", GREEN),
    ]
    total_cnd = sum(c[0] for c in cnd_items) or 1
    for n,lbl,col in cnd_items:
        pct = n/total_cnd
        bw2 = CW*0.3*pct
        fill(pg, ML, y-8, ML+bw2, y-1, col)
        txt(pg, ML+CW*0.3+6, y, f"{lbl}: {n}", FN_R, 9, DARK)
        y += 13

    # ── PÁGINAS POR MUNICÍPIO ─────────────────────────────────────────────────
    pm_map = {m["nome"]: m for m in municipios}

    for mun_nome, itens_por_tipo in itens_todos.items():
        m_stat = pm_map.get(mun_nome, {})
        devs   = itens_por_tipo.get("DEVEDOR", [])
        maeds  = itens_por_tipo.get("MAED", [])
        omiss  = itens_por_tipo.get("OMISSÃO", [])
        pfs    = itens_por_tipo.get("PROCESSO FISCAL", [])
        if not any([devs, maeds, omiss, pfs]):
            continue

        pg, y = new_page(f"MUNICÍPIO: {mun_nome.upper()}")

        # Barra de status do município
        cnd_dias = m_stat.get("cnd_dias")
        if cnd_dias is None:           cnd_col = (0.47,0.58,0.67); cnd_txt = "CND: Sem info"
        elif cnd_dias < 0:             cnd_col = RED;               cnd_txt = f"CND: VENCIDA há {abs(cnd_dias)}d"
        elif cnd_dias <= 30:           cnd_col = AMBER;             cnd_txt = f"CND: Vence em {cnd_dias}d"
        elif cnd_dias <= 90:           cnd_col = YELLOW;            cnd_txt = f"CND: Vence em {cnd_dias}d"
        else:                          cnd_col = GREEN;             cnd_txt = f"CND: Válida ({cnd_dias}d)"
        fill(pg, ML, y, W-MR, y+18, (*cnd_col, 0.12))
        txt(pg, ML+6, y+13, cnd_txt, FN_B, 9.5, cnd_col)
        v_txt = f"Devedor: {_brl(m_stat.get('v_dev',0))}   MAED: {_brl(m_stat.get('v_maed',0))}   Omissões: {m_stat.get('n_omiss',0)}   Processos: {m_stat.get('n_pf',0)}"
        txt(pg, ML+CW*0.4, y+13, v_txt, FN_R, 8.5, MID)
        y += 26

        def need_page(pg, y, h, titulo):
            if y+h > YBOT:
                pg, y = new_page(titulo)
            return pg, y

        titulo_mun = f"MUNICÍPIO: {mun_nome.upper()}"

        # DEVEDORES
        if devs:
            pg, y = need_page(pg, y, 30, titulo_mun)
            fill(pg, ML, y-2, W-MR, y+14, (*RED, 0.10))
            txt(pg, ML+4, y+10, f"DEVEDORES ({len(devs)} item(ns))", FN_B, 9.5, RED)
            y += 20
            # Cabeçalho da tabela
            cols_dev = [(ML,       90, "Cód./Rubrica"),
                        (ML+95,    75, "Competência"),
                        (ML+175,   62, "Vencimento"),
                        (ML+242,   75, "Original"),
                        (ML+322,   75, "Devedor"),
                        (ML+402,   75, "Multa+Juros"),
                        (ML+482,   90, "Consolidado")]
            fill(pg, ML, y-8, W-MR, y+4, (0.93,0.95,0.97))
            for x,w,lbl in cols_dev:
                txt(pg, x+2, y, lbl, FN_B, 7.5, MID)
            y += 11
            grupos: dict = {}
            for it in devs:
                k = f"{it.get('orgao') or 'Município'} ||| {it.get('cnpj') or '—'}"
                grupos.setdefault(k,[]).append(it)
            for gk, gitens in grupos.items():
                orgao, cnpj = gk.split(" ||| ",1)
                pg, y = need_page(pg, y, 16, titulo_mun)
                fill(pg, ML, y-9, W-MR, y+2, (*RED,0.06))
                txt(pg, ML+4, y, f"{orgao}  (CNPJ: {cnpj})", FN_B, 8.5, RED)
                y += 12
                for it in gitens:
                    pg, y = need_page(pg, y, 12, titulo_mun)
                    cod = f"{it.get('cod') or ''} – {it.get('desc_rubrica') or ''}".strip(" –")[:22]
                    multa = (it.get("v_multa") or 0)+(it.get("v_juros") or 0)
                    res   = it.get("residual",False)
                    row_vals = [
                        (ML+2,    cod,                       FN_R, 8, DARK),
                        (ML+97,   it.get("comp") or "—",    FN_R, 8, DARK),
                        (ML+177,  it.get("venc") or "—",    FN_R, 8, MID),
                        (ML+244,  _brl(it.get("v_original")),FN_R, 8, MID),
                        (ML+324,  _brl(it.get("v_devedor")), FN_B, 8, RED),
                        (ML+404,  _brl(multa) if multa else "—", FN_R, 8, YELLOW),
                        (ML+484,  _brl(it.get("v_consolidado"))+((" ⚠") if res else ""), FN_B, 8, YELLOW if res else RED),
                    ]
                    for x,v,fn,fs,col in row_vals:
                        txt(pg, x, y, str(v), fn, fs, col)
                    hline(pg, ML, y+3, W-MR, (0.92,0.94,0.97), 0.3)
                    y += 12
            y += 4

        # MAED
        if maeds:
            pg, y = need_page(pg, y, 30, titulo_mun)
            fill(pg, ML, y-2, W-MR, y+14, (*YELLOW, 0.10))
            txt(pg, ML+4, y+10, f"MAED ({len(maeds)} item(ns))", FN_B, 9.5, YELLOW)
            y += 20
            cols_m = [(ML,100,"Cód./Rubrica"),(ML+105,75,"Competência"),(ML+185,70,"Vencimento"),
                      (ML+260,90,"Saldo Devedor"),(ML+355,160,"Situação")]
            fill(pg, ML, y-8, W-MR, y+4, (0.93,0.95,0.97))
            for x,w,lbl in cols_m:
                txt(pg, x+2, y, lbl, FN_B, 7.5, MID)
            y += 11
            grupos = {}
            for it in maeds:
                k = f"{it.get('orgao') or 'Município'} ||| {it.get('cnpj') or '—'}"
                grupos.setdefault(k,[]).append(it)
            for gk,gitens in grupos.items():
                orgao, cnpj = gk.split(" ||| ",1)
                pg, y = need_page(pg, y, 16, titulo_mun)
                fill(pg, ML, y-9, W-MR, y+2, (*YELLOW,0.06))
                txt(pg, ML+4, y, f"{orgao}  (CNPJ: {cnpj})", FN_B, 8.5, YELLOW)
                y += 12
                for it in gitens:
                    pg, y = need_page(pg, y, 12, titulo_mun)
                    cod = f"{it.get('cod') or ''} – {it.get('desc_rubrica') or ''}".strip(" –")[:28]
                    row_vals = [
                        (ML+2,   cod,                       FN_R, 8, DARK),
                        (ML+107, it.get("comp") or "—",    FN_R, 8, DARK),
                        (ML+187, it.get("venc") or "—",    FN_R, 8, MID),
                        (ML+262, _brl(it.get("v_devedor")), FN_B, 8, YELLOW),
                        (ML+357, it.get("situacao") or "—",FN_R, 8, MID),
                    ]
                    for x,v,fn,fs,col in row_vals:
                        txt(pg, x, y, str(v), fn, fs, col)
                    hline(pg, ML, y+3, W-MR, (0.92,0.94,0.97), 0.3)
                    y += 12
            y += 4

        # OMISSÕES
        if omiss:
            pg, y = need_page(pg, y, 30, titulo_mun)
            fill(pg, ML, y-2, W-MR, y+14, (*SKY, 0.10))
            txt(pg, ML+4, y+10, f"OMISSÕES ({len(omiss)} item(ns))", FN_B, 9.5, SKY)
            y += 20
            grupos = {}
            for it in omiss:
                k = f"{it.get('orgao') or 'Município'} ||| {it.get('cnpj') or '—'}"
                grupos.setdefault(k,[]).append(it)
            for gk,gitens in grupos.items():
                orgao, cnpj = gk.split(" ||| ",1)
                pg, y = need_page(pg, y, 16, titulo_mun)
                fill(pg, ML, y-9, W-MR, y+2, (*SKY,0.06))
                txt(pg, ML+4, y, f"{orgao}  (CNPJ: {cnpj})", FN_B, 8.5, SKY)
                y += 12
                for it in gitens:
                    pg, y = need_page(pg, y, 12, titulo_mun)
                    decl = (it.get("tipo_declaracao") or "NÃO ID.")[:12]
                    per  = (it.get("periodo") or "(período não identificado)")[:60]
                    dw = tw(decl,FN_B,8)+8
                    fill(pg, ML+2, y-8, ML+2+dw, y+3, (*SKY,0.15), r=2)
                    txt(pg, ML+4, y, decl, FN_B, 8, SKY)
                    txt(pg, ML+2+dw+6, y, per, FN_R, 8, DARK)
                    hline(pg, ML, y+3, W-MR, (0.92,0.94,0.97), 0.3)
                    y += 12
            y += 4

        # PROCESSOS FISCAIS
        if pfs:
            pg, y = need_page(pg, y, 30, titulo_mun)
            fill(pg, ML, y-2, W-MR, y+14, (*PURPLE, 0.10))
            txt(pg, ML+4, y+10, f"PROCESSOS FISCAIS ({len(pfs)} item(ns))", FN_B, 9.5, PURPLE)
            y += 20
            for it in pfs:
                pg, y = need_page(pg, y, 12, titulo_mun)
                proc = (it.get("processo") or "—")[:30]
                situ = (it.get("situacao") or "")[:40]
                orgao= (it.get("orgao") or "")[:30]
                txt(pg, ML+2, y, proc, FN_B, 8.5, PURPLE)
                txt(pg, ML+220, y, situ, FN_R, 8, MID)
                txt(pg, ML+450, y, orgao, FN_R, 8, DARK)
                hline(pg, ML, y+3, W-MR, (0.92,0.94,0.97), 0.3)
                y += 12
            y += 4

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue(), None

# ── Componente principal ──────────────────────────────────────────────────────
def render_dashboard_socios():
    try:
        from supabase_client import (
            buscar_municipios, buscar_stats, buscar_itens_municipio,
            gerar_url_download, listar_analises, supabase_disponivel,
        )
    except ImportError as exc:
        st.error(f"❌ Módulo supabase_client não encontrado: {exc}"); return

    ss = st.session_state

    # ── Header ────────────────────────────────────────────────────────────────
    left, right = st.columns([5,1])
    with left:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:14px;padding:6px 0 2px">'
            '<div style="width:42px;height:42px;flex-shrink:0;'
            'background:linear-gradient(145deg,#2a9c6b,#1a7a52);border-radius:10px;'
            'display:flex;align-items:center;justify-content:center;font-size:20px;'
            'box-shadow:0 4px 14px rgba(42,156,107,.4)">📈</div>'
            '<div><div style="font-size:18px;font-weight:800;color:#dce8f2;line-height:1.2">'
            'ConPrev <span style="font-weight:400;color:#7a95ad;font-size:14px;margin-left:6px">'
            'Dashboard Sócios</span></div>'
            '<div style="font-size:11px;color:#7a95ad;margin-top:2px">'
            'Acompanhamento em tempo real · Acesso somente leitura</div></div></div>',
            unsafe_allow_html=True)
    with right:
        if st.button("↩ Sair", key="socio_logout"):
            for k in ["authenticated","role","socio_analise_id","socio_stats",
                      "socio_municipios","socio_dl_url"]:
                ss.pop(k, None)
            ss["authenticated"] = False; ss["role"] = None; st.rerun()

    _divider()

    if not supabase_disponivel():
        st.error("⚠️ Supabase não configurado. Verifique SUPABASE_URL e SUPABASE_KEY."); return

    # ── Seletor de análises ───────────────────────────────────────────────────
    with st.spinner("Carregando análises..."):
        analises = listar_analises(limit=20)
    if not analises:
        st.info("📭 Nenhuma análise publicada ainda."); return

    opcoes = {}
    for a in analises:
        dt_fmt = _fmt_dt(a.get("created_at",""))
        label  = f"📅 {dt_fmt}  ·  Ref. {a.get('ref_date','—')}  ·  {a.get('total_municipios',0)} municípios"
        opcoes[label] = a["id"]

    _section("📂 Selecione a Análise", "🗓", accent="#2d8fd4")
    escolhida = st.selectbox("Análises", list(opcoes.keys()), key="socio_analise_select", label_visibility="collapsed")
    analise_id = opcoes[escolhida]

    if ss.get("socio_analise_id") != analise_id:
        with st.spinner("Carregando dados..."):
            ss["socio_analise_id"]  = analise_id
            ss["socio_stats"]       = buscar_stats(analise_id)
            ss["socio_municipios"]  = buscar_municipios(analise_id)
            ss.pop("socio_dl_url", None)

    stats      = ss.get("socio_stats", {})
    municipios = ss.get("socio_municipios", [])
    if not stats:
        st.warning("⚠️ Não foi possível carregar os dados."); return

    ref_date   = stats.get("_ref_date","—")
    created_at = _fmt_dt(stats.get("_created_at",""))
    zip_ts     = stats.get("_zip_ts","")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;'
        f'background:rgba(45,143,212,.06);border:1px solid rgba(45,143,212,.2);'
        f'border-radius:8px;margin-bottom:18px">'
        f'<span style="font-size:12px;color:#b0c4d8">ℹ️ Publicada em '
        f'<b style="color:#dce8f2">{created_at}</b> &nbsp;·&nbsp; '
        f'Referência: <b style="color:#dce8f2">{ref_date}</b> &nbsp;·&nbsp; '
        f'{stats.get("total_municipios",0)} municípios</span></div>',
        unsafe_allow_html=True)

    # ── Downloads ─────────────────────────────────────────────────────────────
    _section("⬇️ Downloads", accent="#2a9c6b")
    dl_col, pdf_col = st.columns(2)

    with dl_col:
        if zip_ts:
            if st.button("🔗 Gerar link do ZIP (válido 1h)", key="btn_dl", use_container_width=True):
                with st.spinner("Gerando URL assinada..."):
                    url = gerar_url_download(analise_id, zip_ts)
                ss["socio_dl_url"] = url if url else None
            if ss.get("socio_dl_url"):
                st.markdown(
                    f'<div style="padding:8px 12px;background:rgba(42,156,107,.08);'
                    f'border:1px solid rgba(42,156,107,.25);border-radius:8px;margin-top:6px">'
                    f'<a href="{ss["socio_dl_url"]}" target="_blank" '
                    f'style="font-size:12px;color:#2d8fd4">⬇️ Baixar ZIP completo</a>'
                    f'<p style="font-size:10px;color:#7a95ad;margin:4px 0 0">Expira em 1h</p>'
                    f'</div>', unsafe_allow_html=True)

    with pdf_col:
        if st.button("📄 Gerar PDF do Dashboard", key="btn_pdf", use_container_width=True,
                     help="Gera PDF com layout ConPrev contendo todos os detalhamentos"):
            # Coleta itens de todos os municípios com restrições
            muns_com_issues = [
                m["nome"] for m in municipios
                if any(m.get(k,0) for k in ("n_dev","n_maed","n_omiss","n_pf"))
            ]
            itens_todos = {}
            prog = st.progress(0, text="Coletando dados...")
            for i, mun in enumerate(muns_com_issues):
                cache_key = f"itens_{analise_id}_{mun}"
                if cache_key not in ss:
                    ss[cache_key] = buscar_itens_municipio(analise_id, mun)
                itens_todos[mun] = ss[cache_key]
                prog.progress((i+1)/max(len(muns_com_issues),1), text=f"Processando {mun}...")
            prog.empty()
            with st.spinner("Gerando PDF..."):
                pdf_bytes, err = _gerar_pdf_dashboard(
                    stats, municipios, itens_todos, ref_date, created_at)
            if err:
                st.error(f"❌ Erro ao gerar PDF: {err}")
            elif pdf_bytes:
                ss["socio_pdf_bytes"] = pdf_bytes
                ts_now = time.strftime("%Y-%m-%d_%Hh%M")
                ss["socio_pdf_ts"] = ts_now

        if ss.get("socio_pdf_bytes"):
            st.download_button(
                label="⬇️ Baixar PDF do Dashboard",
                data=ss["socio_pdf_bytes"],
                file_name=f"ConPrev_Dashboard_{ss.get('socio_pdf_ts','')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_pdf_dl")

    _divider()

    # ── Conteúdo ──────────────────────────────────────────────────────────────
    _render_cnd_alertas(municipios)
    _divider()
    _render_stats_macro(stats)
    _divider("Detalhamento por Município")
    _render_tabela_municipios(municipios, analise_id, stats)

    st.markdown(
        '<div style="text-align:center;padding:24px 0 8px">'
        '<p style="font-size:11px;color:#7a95ad">'
        '🔒 Dados restritos &middot; Conprev Assessoria Municipal</p></div>',
        unsafe_allow_html=True)
