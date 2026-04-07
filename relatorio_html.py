import base64
import time
from datetime import datetime

def _brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def _pct(parte, total):
    if not total: return "0,0%"
    return f"{(parte / total * 100):.1f}".replace('.', ',') + '%'

def gerar_html_executivo(stats: dict, municipios: list, logo_path: str = "logo_conprev.png") -> str:
    """
    Gera o relatório HTML executivo com base nos dados analisados de restrições.
    """
    hoje = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    # Tentativa de carregar logo em base64
    logo_b64 = ""
    try:
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="ConPrev" style="height:60px;width:auto;object-fit:contain;mix-blend-mode:screen;" />'
    except Exception:
        logo_html = '<div style="font-family:Outfit,sans-serif;font-size:26px;font-weight:800;color:#E8872A;letter-spacing:-0.5px;">Con<span style="color:#fff;">Prev</span></div>'

    # --- Tratamento de Dados (KPIs) ---
    tot_mun = len(municipios)
    mun_ok = len([m for m in municipios if m.get('cnd_status') == 'ok'])
    mun_pend = tot_mun - mun_ok
    
    v_dev = sum(m.get('v_dev', 0) for m in municipios)
    v_maed = sum(m.get('v_maed', 0) for m in municipios)
    v_total = v_dev + v_maed

    # --- Construção das Linhas da Tabela ---
    linhas_html = []
    for m in sorted(municipios, key=lambda x: x.get('v_dev', 0) + x.get('v_maed', 0), reverse=True):
        status = m.get('cnd_status', 'sem_info')
        if status == 'ok':
            chip = '<span class="chip chip-prev"><span class="chip-dot"></span>Regular</span>'
        elif status == 'vencida':
            chip = '<span class="chip chip-nao"><span class="chip-dot"></span>Vencida / Irregular</span>'
        else:
            chip = '<span class="chip chip-corr"><span class="chip-dot"></span>Atenção</span>'

        v_m_dev = _brl(m.get('v_dev', 0))
        v_m_maed = _brl(m.get('v_maed', 0))

        linhas_html.append(f"""
            <tr>
              <td class="cod">{m.get('cnpj', '---')}</td>
              <td><strong>{m.get('nome', 'Município')}</strong></td>
              <td>{chip}</td>
              <td style="color:var(--red); font-weight:600;">{v_m_dev}</td>
              <td style="color:var(--amber); font-weight:600;">{v_m_maed}</td>
            </tr>
        """)
    
    tbody = "".join(linhas_html) if linhas_html else '<tr><td colspan="5" style="text-align:center;">Nenhum dado encontrado.</td></tr>'

    # --- Montagem do HTML Final ---
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório Executivo — Situação Fiscal</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --navy:#0D1F3C; --navy2:#1A3259; --gold:#C89B3C; --gold2:#E8B94F;
  --red:#C0392B;  --red-bg:#FDF0EE; --green:#1A6B3A; --green-bg:#EAF5EE;
  --amber:#B45309; --amber-bg:#FEF3E2; --purple:#7B2D8B; --purple-bg:#F5EBF8;
  --gray50:#F8FAFC; --gray100:#F1F5F9; --gray200:#E2E8F0;
  --gray400:#94A3B8; --gray600:#475569; --gray800:#1E293B; --white:#FFFFFF;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'DM Sans',sans-serif;background:#EDF0F5;color:var(--gray800);font-size:13.5px;line-height:1.6;}}
.page{{max-width:960px;margin:32px auto;background:var(--white);box-shadow:0 4px 32px rgba(13,31,60,.12);border-radius:4px;overflow:hidden;}}

/* HEADER */
.header{{background:linear-gradient(135deg,#0B1E33 0%,#112840 40%,#16324F 100%);padding:48px 56px 36px;position:relative;overflow:hidden;}}
.header::after{{content:'';position:absolute;top:-60px;right:-80px;width:320px;height:320px;border-radius:50%;background:rgba(200,155,60,.07);pointer-events:none;}}
.header-top{{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;flex-wrap:wrap;}}
.header-meta .badge{{display:inline-block;background:rgba(200,155,60,.18);border:1px solid rgba(200,155,60,.35);color:var(--gold2);font-size:10.5px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;padding:4px 12px;border-radius:20px;margin-bottom:8px;}}
.header-meta .date{{font-size:12px;color:rgba(255,255,255,.5);font-weight:300;}}
.header-divider{{height:1px;background:rgba(200,155,60,.25);margin:28px 0 24px;}}
.report-title{{font-family:'Outfit',sans-serif;font-size:30px;font-weight:800;color:var(--white);line-height:1.2;}}
.report-subtitle{{font-size:13px;color:rgba(255,255,255,.55);margin-top:8px;font-weight:300;}}

/* BODY */
.body{{padding:48px 56px;}}
.section-label{{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--gold);margin-bottom:10px;}}
.section-title{{font-family:'Outfit',sans-serif;font-size:20px;font-weight:700;color:var(--navy);margin-bottom:16px;border-left:3px solid var(--gold);padding-left:12px;}}

/* KPIs */
.kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:32px;}}
.kpi-card{{background:var(--white);border:1px solid var(--gray200);border-radius:8px;padding:22px 20px;position:relative;overflow:hidden;}}
.kpi-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:4px;}}
.kpi-total::before{{background:var(--navy);}} .kpi-ok::before{{background:var(--green);}}
.kpi-pend::before{{background:var(--red);}} .kpi-dev::before{{background:var(--amber);}}
.kpi-maed::before{{background:var(--purple);}}
.kpi-value{{font-family:'Outfit',sans-serif;font-size:26px;font-weight:800;color:var(--navy);margin-bottom:4px;}}
.kpi-label{{font-size:11px;font-weight:600;color:var(--gray600);text-transform:uppercase;}}

/* TABLES & CHIPS */
.table-wrap{{border:1px solid var(--gray200);border-radius:8px;overflow:hidden;margin-bottom:40px;}}
table{{width:100%;border-collapse:collapse;}}
thead{{background:var(--navy);}}
th{{padding:11px 16px;text-align:left;font-size:10.5px;font-weight:700;color:rgba(255,255,255,.85);text-transform:uppercase;}}
td{{padding:10px 16px;font-size:12.5px;border-bottom:1px solid var(--gray100);}}
tr:nth-child(even) td{{background:#FAFBFC;}}
.chip{{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;}}
.chip-nao{{background:var(--red-bg);color:var(--red);}}
.chip-prev{{background:var(--green-bg);color:var(--green);}}
.chip-corr{{background:var(--amber-bg);color:var(--amber);}}
.chip-dot{{width:6px;height:6px;border-radius:50%;}}
.chip-nao .chip-dot{{background:var(--red);}} .chip-prev .chip-dot{{background:var(--green);}} .chip-corr .chip-dot{{background:var(--amber);}}

/* INSIGHTS */
.insights-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
.insight-card{{border-radius:8px;padding:22px 24px;border:1px solid;}}
.insight-card.red{{background:var(--red-bg);border-color:#FBCBC4;}}
.insight-card.navy{{background:#EEF2F8;border-color:#C5D3E8;}}
.insight-title{{font-weight:700;font-size:13px;margin-bottom:8px;}}
.insight-text{{font-size:12.5px;color:var(--gray600);line-height:1.65;}}

@media print{{body{{background:white;}} .page{{box-shadow:none;margin:0;max-width:100%;}}}}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-top">
      <div>{logo_html}</div>
      <div class="header-meta">
        <div class="badge">Relatório Executivo de Regularidade</div>
        <div class="date">Emissão: {hoje}</div>
      </div>
    </div>
    <div class="header-divider"></div>
    <div class="report-title">Auditoria de Restrições e Passivos</div>
    <div class="report-subtitle">Monitoramento de Situação Fiscal (RFB/PGFN) — Risco de Bloqueio de FPM</div>
  </div>

  <div class="body">
    <div class="section-label">01 — Indicadores Globais</div>
    <div class="section-title">Macrovisão da Carteira</div>
    <div class="kpi-grid">
      <div class="kpi-card kpi-total">
        <div class="kpi-value">{tot_mun}</div><div class="kpi-label">Municípios Analisados</div>
      </div>
      <div class="kpi-card kpi-ok">
        <div class="kpi-value" style="color:var(--green)">{mun_ok}</div><div class="kpi-label">Sem Pendências</div>
      </div>
      <div class="kpi-card kpi-pend">
        <div class="kpi-value" style="color:var(--red)">{mun_pend}</div><div class="kpi-label">Com Restrições</div>
      </div>
      <div class="kpi-card kpi-dev">
        <div class="kpi-value" style="color:var(--amber); font-size:18px; margin-top:6px;">{_brl(v_dev)}</div>
        <div class="kpi-label">Estoque Devedor (RFB)</div>
      </div>
      <div class="kpi-card kpi-maed">
        <div class="kpi-value" style="color:var(--purple); font-size:18px; margin-top:6px;">{_brl(v_maed)}</div>
        <div class="kpi-label">Multas MAED Acumuladas</div>
      </div>
    </div>

    <div class="section-label">02 — Detalhamento Analítico</div>
    <div class="section-title">Materialidade por Ente Público</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>CNPJ</th><th>Entidade</th><th>Status CND</th><th>Saldo Devedor (R$)</th><th>Multas Atraso (MAED)</th></tr>
        </thead>
        <tbody>{tbody}</tbody>
      </table>
    </div>

    <div class="section-label">03 — Recomendações Técnicas</div>
    <div class="section-title">Insights e Gestão de Risco</div>
    <div class="insights-grid">
      <div class="insight-card red">
        <div class="insight-title" style="color:var(--red);">⚠️ Risco de Bloqueio do FPM e Certidões</div>
        <div class="insight-text">
          Identificamos <strong>{mun_pend} entidades</strong> com pendências ativas. 
          A falta de saneamento imediato (via pagamento, parcelamento ou adesão à Transação Tributária PGFN) 
          resultará em bloqueio do Fundo de Participação dos Municípios (FPM) e inviabilidade de recebimento de transferências voluntárias e convênios.
        </div>
      </div>
      <div class="insight-card navy">
        <div class="insight-title" style="color:var(--navy);">🛡️ Estratégia de Mitigação (Consultoria)</div>
        <div class="insight-text">
          O volume de penalidades por atraso na entrega de declarações (MAED) atinge <strong>{_brl(v_maed)}</strong>. 
          Nossa equipe recomenda a impugnação administrativa nos casos de inexistência de fato gerador (ex: cancelamento do ato principal) 
          e a antecipação preventiva de rotinas do eSocial/DCTFWeb para blindar o fluxo de caixa do município contra novas autuações sistêmicas.
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>"""
    return html
