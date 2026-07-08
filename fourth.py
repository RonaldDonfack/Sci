import streamlit as st
import pandas as pd
import numpy as np
import re
from pyvis.network import Network
import tempfile
import os

st.set_page_config(
    page_title="Investment Cycle · Equity Calculator",
    page_icon="🏗️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #0D1117; color: #E6EDF3; }
.block-container { padding-top: 2rem; max-width: 1500px; }
.metric-card {
    background: linear-gradient(135deg,#161B22 0%,#1C2128 100%);
    border: 1px solid #30363D; border-radius: 12px;
    padding: 1.2rem 1.4rem; margin-bottom: 0.8rem; transition: border-color .2s;
}
.metric-card:hover { border-color: #58A6FF; }
.metric-card .label { font-size:.72rem;font-weight:600;color:#8B949E;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.3rem; }
.metric-card .value { font-family:'Space Grotesk',sans-serif;font-size:1.6rem;font-weight:700;color:#58A6FF; }
.metric-card .sub { font-size:.78rem;color:#6E7681;margin-top:.2rem; }
.section-header {
    font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;color:#C9D1D9;
    border-left:3px solid #58A6FF;padding-left:.75rem;margin:1.5rem 0 1rem 0;
}
.stTextArea textarea { background:#161B22!important;border:1px solid #30363D!important;color:#C9D1D9!important;border-radius:8px!important;font-size:.85rem!important; }
.stNumberInput input,.stTextInput input { background:#161B22!important;border:1px solid #30363D!important;color:#C9D1D9!important;border-radius:8px!important; }
.stButton > button { background:linear-gradient(135deg,#1F6FEB,#388BFD);color:white;border:none;border-radius:8px;font-weight:600;padding:.5rem 1.5rem; }
.stButton > button:hover { background:linear-gradient(135deg,#388BFD,#58A6FF);transform:translateY(-1px); }
.stDataFrame { border-radius:10px;overflow:hidden; }
thead tr th { background:#161B22!important;color:#8B949E!important;font-size:.78rem!important;letter-spacing:.06em!important;text-transform:uppercase!important; }
tbody tr td { color:#C9D1D9!important;font-size:.88rem!important; }
tbody tr:nth-child(even) td { background:#161B22!important; }
.person-card {
    background:#161B22;border:1px solid #30363D;border-radius:10px;
    padding:1rem 1.2rem;margin-bottom:.6rem;transition:border-color .2s;
}
.person-card:hover { border-color:#3FB950; }
.person-card .name { font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;color:#E6EDF3; }
.person-card .wealth { font-family:'Space Grotesk',sans-serif;font-size:1.3rem;font-weight:700;color:#3FB950; }
.person-card .bar-bg { background:#21262D;border-radius:4px;height:6px;margin:.5rem 0; }
.person-card .bar-fg { background:linear-gradient(90deg,#238636,#3FB950);border-radius:4px;height:6px; }
.badge { display:inline-block;background:#0F2918;border:1px solid #238636;border-radius:999px;padding:.1rem .55rem;font-size:.72rem;color:#3FB950;margin:.15rem; }
.badge-blue { background:#0D1F3C;border-color:#1F6FEB;color:#58A6FF; }
.info-box { background:#0D1F3C;border:1px solid #1F6FEB;border-radius:8px;padding:.75rem 1rem;font-size:.83rem;color:#8B949E;margin:1rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_RELATIONS = """LEM IMMO -> LEM2 IMMO : 10%
LEM IMMO -> LEM SYNERGIE : 10%
LEM IMMO -> LEM ALLIANCE : 6.25%
LEM IMMO -> LEM INVEST : 10%
M2N IMMO -> LEM2 IMMO : 10%
M2N IMMO -> LEM SYNERGIE : 10%
M2N IMMO -> LEM ALLIANCE : 12.50%
M2N IMMO -> LEM INVEST : 10%
LEM2 IMMO -> LEM SYNERGIE : 20%
LEM2 IMMO -> LEM VIRY : 11.11%
LEM2 IMMO -> LEM INVEST : 10%
LEM SYNERGIE -> LEM INVEST : 10%
LEM VIRY -> LEM ALLIANCE : 31.25%
LEM VIRY -> LEM INVEST : 10%
LEM ALLIANCE -> LEM SYNERGIE : 10%
LEM ALLIANCE -> LEM INVEST : 10%"""

DEFAULT_ASSETS = """LEM IMMO : 220000
M2N IMMO : 160000
LEM2 IMMO : 230000
LEM SYNERGIE : 250000
LEM VIRY : 170000
LEM ALLIANCE : 160000
LEM INVEST : 100000"""

DEFAULT_PARTNERS = """LEM IMMO:
Martial : 2
Nina : 1
Armand : 1
Marlène : 1
Linda : 1
Ivan : 1
Ludovic : 1
Prisca : 1
Nelly : 1

M2N IMMO:
Martial : 1
Nina : 1
Patrick O : 1
Florent : 1

LEM2 IMMO:
Martial : 1
Nina : 1
Armand : 1
Rolaine : 1
Josiane : 1
Lionel : 1
Thierry : 1
Cédric : 1
LEM IMMO : 1
M2N IMMO : 1

LEM SYNERGIE:
Martial : 1
Nina : 1
Cyrius : 1
Davina : 1
Yvonne : 1
LEM IMMO : 1
LEM ALLIANCE : 1
M2N IMMO : 1
LEM2 IMMO : 2

LEM VIRY:
Martial : 1
Nina : 1
Armand : 1
Cyrius : 1
Soraya : 1
Stéphane : 1
Ivan : 1
Jerry : 1
LEM2 IMMO : 1

LEM ALLIANCE:
Martial : 2
Nina : 2
Kelvine : 2
Ludovic : 1
Ivan : 1
LEM IMMO : 1
M2N IMMO : 2
LEM VIRY : 5

LEM INVEST:
Martial : 1.5
Nina : 1.5
Armand : 0.5
Ivan : 0.5
LEM IMMO : 1
M2N IMMO : 1
LEM2 IMMO : 1
LEM VIRY : 1
LEM SYNERGIE : 1
LEM ALLIANCE : 1"""

DEFAULT_CASHFLOW = """LEM IMMO:
  revenue  : 3000
  partners : 2000
  charges  : 1000

M2N IMMO:
  revenue  : 3000
  partners : 2000
  charges  : 1000

LEM2 IMMO:
  revenue  : 4500
  partners : 3000
  charges  : 1500

LEM SYNERGIE:
  revenue  : 4500
  partners : 3000
  charges  : 1500

LEM VIRY:
  revenue  : 3000
  partners : 2000
  charges  : 1000

LEM ALLIANCE:
  revenue  : 3500
  partners : 2500
  charges  : 1000

LEM INVEST:
  revenue  : 2000
  partners : 1100
  charges  : 900"""

# ── Initial investment per SCI (€ per share-unit) ────────────────────────────
SCI_UNIT_COST = {
    "M2N IMMO":    45000,
    "LEM IMMO":    23000,
    "LEM2 IMMO":   26000,
    "LEM ALLIANCE":10000,
    "LEM INVEST":   7500,
    "LEM SYNERGIE":28000,
    "LEM VIRY":    25000,
}

# ── Parsers ───────────────────────────────────────────────────────────────────
def parse_relations(text):
    edges = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        m = re.match(r"^(.+?)\s*->\s*(.+?)\s*:\s*([\d.,]+)\s*%?$", line)
        if m:
            edges.append((m.group(1).strip().upper(), m.group(2).strip().upper(),
                          float(m.group(3).replace(",", ".")) / 100.0))
    return edges

def parse_assets(text):
    assets = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        m = re.match(r"^(.+?)\s*:\s*([\d.,\s]+)$", line)
        if m:
            name = m.group(1).strip().upper()
            assets[name] = float(m.group(2).replace(" ", "").replace(",", "."))
    return assets

def parse_partners(text):
    result = {}
    current_sci = None
    for line in text.strip().splitlines():
        line = line.strip()
        if not line: continue
        if line.endswith(":") and line.count(":") == 1:
            current_sci = line[:-1].strip().upper()
            result[current_sci] = {}
        elif current_sci and ":" in line:
            parts = line.rsplit(":", 1)
            name = parts[0].strip()
            try:
                weight = float(parts[1].strip().replace(",", "."))
            except ValueError:
                weight = 1.0
            result[current_sci][name.upper()] = weight
    return result

def parse_cashflow(text):
    result = {}
    current = None
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped: continue
        if stripped.endswith(":") and stripped.count(":") == 1:
            current = stripped[:-1].strip().upper()
            result[current] = {"revenue": 0, "to_partners": 0, "to_charges": 0}
        elif current and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip().lower().replace(" ", "")
            try:
                v = float(val.strip().replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            if "revenue" in key:   result[current]["revenue"] = v
            elif "partner" in key: result[current]["to_partners"] = v
            elif "charge" in key:  result[current]["to_charges"] = v
    return result

# ── Core calculation ──────────────────────────────────────────────────────────
def compute_all(edges, direct_assets, partners_raw):
    nodes = sorted({n for e in edges for n in (e[0], e[1])} | set(direct_assets.keys()))
    idx   = {n: i for i, n in enumerate(nodes)}
    n     = len(nodes)
    W     = np.zeros((n, n))
    for src, dst, pct in edges:
        W[idx[src], idx[dst]] += pct
    A_vec = np.array([direct_assets.get(nd, 0.0) for nd in nodes])
    try:
        IminusW  = np.eye(n) - W
        equity_vec = np.linalg.solve(IminusW, A_vec)
        inv_IW   = np.linalg.inv(IminusW)
    except np.linalg.LinAlgError:
        equity_vec = A_vec.copy()
        for _ in range(2000):
            new_eq = A_vec + W @ equity_vec
            if np.allclose(new_eq, equity_vec, rtol=1e-10): break
            equity_vec = new_eq
        inv_IW = np.eye(n)
    E = inv_IW - np.eye(n)

    sci_set    = set(nodes)
    all_persons = sorted({m for members in partners_raw.values() for m in members if m not in sci_set})
    P_idx      = {p: i for i, p in enumerate(all_persons)}
    P_direct   = np.zeros((len(all_persons), n))
    sci_shares = {}
    EPSILON_CORRECTIONS = {"LEM VIRY": "MARTIAL"}

    for sci_name, members in partners_raw.items():
        if sci_name not in idx: continue
        j = idx[sci_name]
        total_w = sum(members.values())
        if total_w == 0: continue
        shares  = {m: w / total_w for m, w in members.items()}
        residual = 1.0 - sum(shares.values())
        if abs(residual) > 0:
            target = EPSILON_CORRECTIONS.get(sci_name) or max(shares, key=lambda m: shares[m])
            if target in shares:
                shares[target] += residual
        sci_shares[sci_name] = shares
        for member, pct in shares.items():
            if member in P_idx:
                P_direct[P_idx[member], j] = pct

    person_wealth     = P_direct @ equity_vec
    person_sci_direct = {p: {} for p in all_persons}
    for sci_name, shares in sci_shares.items():
        for member, pct in shares.items():
            if member in P_idx:
                person_sci_direct[member][sci_name] = pct
    P_eff = P_direct @ inv_IW
    # equity_vec = A_vec

    return (nodes, equity_vec, W, E, idx,
            all_persons, P_idx, P_direct, P_eff, person_wealth,
            sci_shares, person_sci_direct)

# ── Graph ─────────────────────────────────────────────────────────────────────
def build_pyvis(nodes, edges, equity_vec, direct_assets, sci_shares,
                show_partners=True, show_effective=False,
                all_persons=None, P_idx=None, P_eff=None, person_wealth=None, idx=None):
    net = Network(height="700px", width="100%", bgcolor="#0D1117", font_color="#C9D1D9", directed=True)
    net.set_options("""{
  "nodes":{"font":{"size":13,"face":"Inter","color":"#C9D1D9"},"borderWidth":2,
           "shadow":{"enabled":true,"size":10,"x":0,"y":0,"color":"rgba(88,166,255,0.3)"}},
  "edges":{"arrows":{"to":{"enabled":true,"scaleFactor":0.7}},
           "color":{"color":"#30363D","hover":"#58A6FF","highlight":"#388BFD"},
           "font":{"size":10,"color":"#8B949E","face":"Inter","align":"middle","strokeWidth":0},
           "smooth":{"type":"curvedCW","roundness":0.2},"width":1.5},
  "physics":{"enabled":true,"solver":"forceAtlas2Based",
             "forceAtlas2Based":{"gravitationalConstant":-110,"centralGravity":0.008,
                                 "springLength":150,"springConstant":0.06},
             "stabilization":{"iterations":200}},
  "interaction":{"hover":true,"tooltipDelay":100,"zoomView":true,"dragNodes":true}
}""")
    idx_map = {n: i for i, n in enumerate(nodes)}
    max_eq  = max(equity_vec) if len(equity_vec) > 0 else 1
    colors  = ["#1C2840","#1A3560","#1A4A7A","#1F6FEB","#388BFD","#58A6FF","#79C0FF"]
    for node in nodes:
        i = idx_map[node]; eq = equity_vec[i]; da = direct_assets.get(node, 0)
        ratio = eq / max_eq if max_eq > 0 else 0
        color = colors[min(int(ratio*(len(colors)-1)), len(colors)-1)]
        shares = sci_shares.get(node, {})
        partner_html = "".join(f"<span style='color:#8B949E'>{m}</span>: <b>{p*100:.2f}%</b><br/>"
                               for m,p in sorted(shares.items(), key=lambda x:-x[1]))
        title = (f"<div style='font-family:Inter;padding:8px;min-width:200px'>"
                 f"<b style='color:#58A6FF'>{node}</b><hr style='border-color:#30363D;margin:4px 0'/>"
                 f"<span style='color:#8B949E'>Direct assets</span>: <b>{da:,.0f} €</b><br/>"
                 f"<span style='color:#8B949E'>Total equity</span>: <b style='color:#3FB950'>{eq:,.0f} €</b>"
                 f"<hr style='border-color:#30363D;margin:4px 0'/>{partner_html}</div>")
        net.add_node(node, label=f"{node}\n{da:,.0f}€", title=title, shape="dot",
                     color={"background":color,"border":"#58A6FF","highlight":{"background":"#388BFD","border":"#79C0FF"}},
                     size=26+ratio*34, font={"size":11+int(ratio*3),"color":"#E6EDF3"})
    for src, dst, pct in edges:
        net.add_edge(src, dst, label=f"{pct*100:.2f}%", title=f"{src} owns {pct*100:.2f}% of {dst}",
                     width=1+pct*4, color={"color":"#30363D"})
    if show_partners and all_persons:
        person_colors = ["#E3B341","#DB6D28","#F778BA","#A371F7","#56D364"]
        for p_i, person in enumerate(all_persons):
            wealth  = person_wealth[P_idx[person]] if person_wealth is not None else 0
            max_w   = max(person_wealth) if person_wealth is not None and len(person_wealth)>0 else 1
            w_ratio = wealth/max_w if max_w>0 else 0
            p_color = person_colors[p_i % len(person_colors)]
            holdings_html = ""
            for sci_name in nodes:
                eff_pct = P_eff[P_idx[person], idx[sci_name]] if P_eff is not None else 0
                if eff_pct > 1e-6:
                    direct_pct = sci_shares.get(sci_name,{}).get(person,0)
                    tag_color  = "#3FB950" if direct_pct>1e-9 else "#E3B341"
                    holdings_html += (f"<span style='color:#8B949E'>{sci_name}</span>: "
                                      f"<b>{eff_pct*100:.3f}%</b> "
                                      f"<span style='color:{tag_color};font-size:9px'>({'direct' if direct_pct>1e-9 else 'indirect'})</span><br/>")
            title = (f"<div style='font-family:Inter;padding:8px;min-width:210px'>"
                     f"<b style='color:{p_color}'>{person}</b><hr style='border-color:#30363D;margin:4px 0'/>"
                     f"<span style='color:#8B949E'>Total wealth</span>: <b style='color:#3FB950'>{wealth:,.0f} €</b>"
                     f"<hr style='border-color:#30363D;margin:4px 0'/>{holdings_html}</div>")
            net.add_node(f"P::{person}", label=person, title=title, shape="dot",
                         color={"background":p_color,"border":"#0D1117","highlight":{"background":p_color,"border":"#E6EDF3"}},
                         size=12+w_ratio*16, font={"size":11,"color":"#C9D1D9"})
            for sci_name in nodes:
                direct_pct = sci_shares.get(sci_name,{}).get(person,0)
                eff_pct    = P_eff[P_idx[person], idx[sci_name]] if P_eff is not None else 0
                if direct_pct > 1e-9:
                    lbl = f"{eff_pct*100:.2f}%" if show_effective else f"{direct_pct*100:.2f}%"
                    net.add_edge(f"P::{person}", sci_name, label=lbl, width=0.8+direct_pct*3,
                                 color={"color":p_color,"opacity":0.55}, dashes=False)
                elif show_effective and eff_pct > 1e-6:
                    net.add_edge(f"P::{person}", sci_name, label=f"{eff_pct*100:.3f}%",
                                 width=0.6, color={"color":p_color,"opacity":0.25}, dashes=True)
    return net

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem'>
  <div style='width:44px;height:44px;background:linear-gradient(135deg,#1F6FEB,#388BFD);
              border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.4rem'>🏗️</div>
  <div>
    <h1 style='margin:0;font-size:1.6rem;color:#E6EDF3'>Investment Cycle · Equity Calculator</h1>
    <p style='margin:0;color:#8B949E;font-size:.85rem'>SCI ownership · partner wealth · no double-counting</p>
  </div>
</div>
""", unsafe_allow_html=True)

tab_input, tab_results, tab_partners, tab_cashflow, tab_profile, tab_graph = st.tabs([
    "📋 Data Input", "📊 SCI Equity", "👥 Partner Wealth", "💶 Cash Flow", "🔍 Partner Profile", "🕸️ Relationship Graph"
])

# ── Input Tab ─────────────────────────────────────────────────────────────────
with tab_input:
    col1, col2, col3 = st.columns([2, 1.5, 2], gap="large")
    with col1:
        st.markdown('<div class="section-header">Ownership Relations</div>', unsafe_allow_html=True)
        relations_text = st.text_area("Relations", value=DEFAULT_RELATIONS, height=360, label_visibility="collapsed")
    with col2:
        st.markdown('<div class="section-header">Direct Assets (€)</div>', unsafe_allow_html=True)
        assets_text = st.text_area("Assets", value=DEFAULT_ASSETS, height=240, label_visibility="collapsed")
        st.markdown('<div class="section-header">Add a Link</div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns([3,3,2,1])
        with c1: new_src = st.text_input("From", placeholder="LEM IMMO", label_visibility="collapsed")
        with c2: new_dst = st.text_input("To",   placeholder="LEM INVEST", label_visibility="collapsed")
        with c3: new_pct = st.number_input("%", min_value=0.0, max_value=100.0, value=10.0, step=0.5, label_visibility="collapsed")
        with c4:
            if st.button("＋"):
                if new_src and new_dst:
                    st.session_state["extra_relations"] = st.session_state.get("extra_relations","") + f"\n{new_src.upper()} -> {new_dst.upper()} : {new_pct}%"
                    st.success("Added")
    with col3:
        st.markdown('<div class="section-header">Partner Shareholdings</div>', unsafe_allow_html=True)
        partners_text = st.text_area("Partners", value=DEFAULT_PARTNERS, height=500, label_visibility="collapsed")
    full_relations = relations_text + st.session_state.get("extra_relations", "")
    if st.button("⚙️  Calculate", type="primary"):
        st.session_state.update({"calc_done": True, "relations_text": full_relations,
                                  "assets_text": assets_text, "partners_text": partners_text})
        st.success("✅ Done — see results tabs.")

if "calc_done" not in st.session_state:
    st.session_state.update({"calc_done": True,
                              "relations_text": DEFAULT_RELATIONS,
                              "assets_text": DEFAULT_ASSETS,
                              "partners_text": DEFAULT_PARTNERS})

edges        = parse_relations(st.session_state["relations_text"])
dir_assets   = parse_assets(st.session_state["assets_text"])
partners_raw = parse_partners(st.session_state.get("partners_text", DEFAULT_PARTNERS))

(nodes, equity_vec, W, E, idx,
 all_persons, P_idx, P_direct, P_eff, person_wealth,
 sci_shares, person_sci_direct) = compute_all(edges, dir_assets, partners_raw)

total_group_assets = sum(dir_assets.values())   # TRUE group total — never double-counted

# ── Cash flow module-scope ────────────────────────────────────────────────────
_cf_data = parse_cashflow(st.session_state.get("cf_text", DEFAULT_CASHFLOW))
for _sci in nodes:
    if _sci not in _cf_data:
        _cf_data[_sci] = {"revenue": 0, "to_partners": 0, "to_charges": 0}

sci_cf = {}
for _sci in nodes:
    _cfg = _cf_data.get(_sci, {})
    _rev = _cfg.get("revenue", 0)
    _tp  = _cfg.get("to_partners", 0)
    _tc  = _cfg.get("to_charges", 0)
    _ret = max(_rev - _tp - _tc, 0)
    sci_cf[_sci] = {"revenue": _rev, "to_partners": _tp, "to_charges": _tc,
                    "retained": _ret,
                    "partners_pct": _tp/_rev if _rev>0 else 0,
                    "charges_pct":  _tc/_rev if _rev>0 else 0,
                    "retained_pct": _ret/_rev if _rev>0 else 0}

pool_vec = np.array([sci_cf[_sci]["to_partners"] for _sci in nodes])
try:
    inv_ImWT = np.linalg.inv(np.eye(len(nodes)) - W.T)
except:
    inv_ImWT = np.eye(len(nodes))

# ── Effective pool per SCI ────────────────────────────────────────────────────
# When SCI i owns % of SCI j, SCI j distributes part of its pool to SCI i.
# SCI i then re-distributes what it received to ITS own partners (human + SCI).
# So the effective pool each SCI distributes =
#   its own fixed pool + its share of received distributions from SCIs it owns.
#
# Let R[i] = total received by SCI i from SCIs it owns:
#   R[i] = sum_j  W[i,j] * pool_eff[j]   (i owns W[i,j] of j)
# So pool_eff[i] = pool_vec[i] + sum_j W[i,j] * pool_eff[j]
# => pool_eff = pool_vec + W @ pool_eff
# => (I - W) @ pool_eff = pool_vec
# => pool_eff = inv(I - W) @ pool_vec   ← same matrix as equity solve
#
# Note: W (not W.T) because SCI i receives from SCIs j it OWNS (i→j ownership).

try:
    inv_IW = np.linalg.inv(np.eye(len(nodes)) - W)
except:
    inv_IW = np.eye(len(nodes))

pool_eff = inv_IW @ pool_vec   # what each SCI actually distributes after receiving upstream

# Direct: person's share of their SCI's FIXED pool (what they see on paper)
person_direct_cf   = P_direct @ pool_vec

# Total: person's share of each SCI's EFFECTIVE pool (fixed + inter-SCI receipts)
person_total_cf    = P_direct @ pool_eff

# Cascade = augmentation from inter-SCI receipts flowing through parent SCIs
person_indirect_cf = person_total_cf - person_direct_cf

# Per-SCI breakdown: person's direct % × that SCI's effective pool
person_sci_cf_matrix = P_direct * pool_eff[np.newaxis, :]

# ── Compute initial investment per person ─────────────────────────────────────
def compute_initial_investments(partners_raw, sci_shares, SCI_UNIT_COST, sci_set):
    """Return {person: {sci: amount_invested}, person: total_invested}"""
    person_inv_by_sci = {p: {} for p in all_persons}
    for sci_name, shares in sci_shares.items():
        unit_cost = SCI_UNIT_COST.get(sci_name, 0)
        if unit_cost == 0: continue
        raw_members = partners_raw.get(sci_name, {})
        total_w = sum(raw_members.values())
        if total_w == 0: continue
        for member, weight in raw_members.items():
            mu = member.upper()
            if mu in {p.upper() for p in all_persons}:
                # find canonical name
                canon = next((p for p in all_persons if p.upper() == mu), None)
                if canon:
                    invested = weight * unit_cost
                    person_inv_by_sci[canon][sci_name] = person_inv_by_sci[canon].get(sci_name, 0) + invested
    person_total_inv = {p: sum(v.values()) for p, v in person_inv_by_sci.items()}
    return person_inv_by_sci, person_total_inv

person_inv_by_sci, person_total_inv = compute_initial_investments(
    partners_raw, sci_shares, SCI_UNIT_COST, set(nodes))

# ── SCI Equity Tab ────────────────────────────────────────────────────────────
with tab_results:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class='metric-card'><div class='label'>Total Group Assets</div>
            <div class='value'>{total_group_assets:,.0f} €</div>
            <div class='sub'>Sum of direct assets · no double-counting</div></div>""", unsafe_allow_html=True)
    with k2:
        top_node = nodes[int(np.argmax(equity_vec))]
        st.markdown(f"""<div class='metric-card'><div class='label'>Largest SCI (equity)</div>
            <div class='value' style='font-size:1.15rem'>{top_node}</div>
            <div class='sub'>{equity_vec[int(np.argmax(equity_vec))]:,.0f} € total equity</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class='metric-card'><div class='label'>SCIs Modelled</div>
            <div class='value'>{len(nodes)}</div>
            <div class='sub'>{len(edges)} ownership links</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class='metric-card'><div class='label'>Partners</div>
            <div class='value'>{len(all_persons)}</div>
            <div class='sub'>across all SCIs</div></div>""", unsafe_allow_html=True)

    st.markdown("""<div class='info-box'>
    ⓘ <b>Total Equity</b> per SCI = own direct assets + proportional share of subsidiaries,
    solved via (I−W)·equity = direct_assets. The group total is always the <b>sum of direct assets only</b>.
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">SCI Equity Breakdown</div>', unsafe_allow_html=True)
    rows = []
    for node in nodes:
        i = idx[node]; da = dir_assets.get(node,0); eq = equity_vec[i]
        owners = [(nodes[j], W[j,i]*100) for j in range(len(nodes)) if W[j,i]>0]
        owned  = [(nodes[j], W[i,j]*100) for j in range(len(nodes)) if W[i,j]>0]
        shares = sci_shares.get(node,{})
        rows.append({
            "SCI": node,
            "Direct Assets (€)": da,
            "Total Equity (€)": eq,
            "Human Partners": sum(1 for m in shares if m not in set(nodes)),
            "Owned by SCIs": ", ".join(f"{o} ({p:.2f}%)" for o,p in owners) if owners else "—",
            "Owns SCIs":     ", ".join(f"{o} ({p:.2f}%)" for o,p in owned) if owned else "—",
        })
    df = pd.DataFrame(rows).sort_values("Total Equity (€)", ascending=False).reset_index(drop=True)
    st.dataframe(
        df.style.format({"Direct Assets (€)":"{:,.0f}","Total Equity (€)":"{:,.0f}"})
               .background_gradient(subset=["Total Equity (€)"], cmap="Blues")
               .background_gradient(subset=["Direct Assets (€)"], cmap="Greens"),
        use_container_width=True, height=320)

    with st.expander("🔍 Effective SCI→SCI Ownership Matrix"):
        df_E = pd.DataFrame(E*100, index=nodes, columns=nodes)
        st.dataframe(df_E.style.format("{:.3f}%").background_gradient(cmap="Blues",vmin=0,vmax=50), use_container_width=True)

# ── Partner Wealth Tab ────────────────────────────────────────────────────────
with tab_partners:
    total_person_wealth = person_wealth.sum()
    rounding_gap = abs(total_group_assets - total_person_wealth)

    kp1, kp2, kp3 = st.columns(3)
    with kp1:
        st.markdown(f"""<div class='metric-card'><div class='label'>Total Partner Wealth</div>
            <div class='value'>{total_person_wealth:,.0f} €</div>
            <div class='sub'>Sum across {len(all_persons)} partners</div></div>""", unsafe_allow_html=True)
    with kp2:
        st.markdown(f"""<div class='metric-card'><div class='label'>Group Real Assets</div>
            <div class='value'>{total_group_assets:,.0f} €</div>
            <div class='sub'>True consolidated total</div></div>""", unsafe_allow_html=True)
    with kp3:
        st.markdown(f"""<div class='metric-card'><div class='label'>Reconciliation Gap</div>
            <div class='value' style='color:{"#3FB950" if rounding_gap<100 else "#F85149"}'>{rounding_gap:,.2f} €</div>
            <div class='sub'>{"✓ Rounding only" if rounding_gap<100 else "⚠ Check partner weights"}</div></div>""",
            unsafe_allow_html=True)

    filter_col, _ = st.columns([2, 4])
    with filter_col:
        partner_filter = st.selectbox(
            "Filter partner",
            options=["— All partners —"] + sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]]),
            label_visibility="collapsed",
        )

    sorted_persons = sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]])
    display_persons = sorted_persons if partner_filter == "— All partners —" else [partner_filter]

    view_mode = st.radio("View", ["💰 Wealth %", "💰 Wealth €", "🥧 Camembert"], horizontal=True, label_visibility="collapsed")

    if view_mode == "💰 Wealth %":
        st.markdown('<div class="section-header">Partner Wealth — % of Group Assets</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for rank_all, person in enumerate(sorted_persons):
            if person not in display_persons: continue
            pw      = person_wealth[P_idx[person]]
            pct_grp = pw / total_group_assets * 100
            bar_pct = int(pw / max(person_wealth) * 100)
            sci_h   = person_sci_direct.get(person, {})
            badges  = "".join(f"<span class='badge badge-blue'>{sci} {p*100:.1f}%</span>"
                              for sci,p in sorted(sci_h.items(), key=lambda x:-x[1]))
            with cols[rank_all % 3]:
                st.markdown(f"""
                <div class='person-card'>
                  <div style='display:flex;justify-content:space-between;align-items:baseline'>
                    <div class='name'>#{rank_all+1} {person}</div>
                    <div class='wealth'>{pct_grp:.2f}%</div>
                  </div>
                  <div style='font-size:.8rem;color:#8B949E;margin:.1rem 0'>{pw:,.0f} € of {total_group_assets:,.0f} €</div>
                  <div class='bar-bg'><div class='bar-fg' style='width:{bar_pct}%'></div></div>
                  <div style='margin-top:.4rem'>{badges}</div>
                </div>""", unsafe_allow_html=True)

    elif view_mode == "💰 Wealth €":
        st.markdown('<div class="section-header">Partner Wealth — € breakdown by SCI</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for rank_all, person in enumerate(sorted_persons):
            if person not in display_persons: continue
            pw      = person_wealth[P_idx[person]]
            bar_pct = int(pw / max(person_wealth) * 100)
            sci_h   = person_sci_direct.get(person, {})
            # show € amount per SCI
            sci_badges = "".join(
                f"<span class='badge badge-blue'>{sci} {p*equity_vec[idx[sci]]:,.0f}€</span>"
                for sci,p in sorted(sci_h.items(), key=lambda x:-x[1]*equity_vec[idx[x[0]]])
            )
            with cols[rank_all % 3]:
                st.markdown(f"""
                <div class='person-card'>
                  <div style='display:flex;justify-content:space-between;align-items:baseline'>
                    <div class='name'>#{rank_all+1} {person}</div>
                    <div class='wealth'>{pw:,.0f} €</div>
                  </div>
                  <div style='font-size:.8rem;color:#8B949E;margin:.1rem 0'>{pw/total_group_assets*100:.2f}% of group · {len(sci_h)} SCI(s)</div>
                  <div class='bar-bg'><div class='bar-fg' style='width:{bar_pct}%'></div></div>
                  <div style='margin-top:.4rem'>{sci_badges}</div>
                </div>""", unsafe_allow_html=True)

    else:  # 🥧 Camembert — wealth only
        st.markdown('<div class="section-header">Wealth Distribution — Camembert</div>', unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            persons_show = display_persons
            w_vals = [person_wealth[P_idx[p]] for p in persons_show]

            if len(persons_show) == 1:
                # Single partner: wealth broken down by SCI
                p    = persons_show[0]
                sci_h = person_sci_direct.get(p, {})
                labels = list(sci_h.keys())
                vals   = [sci_h[s] * equity_vec[idx[s]] for s in labels]
                center_txt = f"{person_wealth[P_idx[p]]:,.0f}€<br>total"
            else:
                labels = persons_show
                vals   = w_vals
                center_txt = f"{sum(w_vals):,.0f}€<br>total"

            palette = ["#1F6FEB","#3FB950","#E3B341","#F85149","#A371F7","#58A6FF","#DB6D28",
                       "#79C0FF","#F778BA","#56D364","#388BFD","#FF6B6B","#C9D1D9"]
            fig_cam = go.Figure(go.Pie(
                labels=labels, values=vals, hole=0.52,
                textinfo="label+percent+value", textfont_size=11,
                texttemplate="%{label}<br>%{percent}<br>%{value:,.0f}€",
                marker=dict(colors=[palette[i % len(palette)] for i in range(len(labels))]),
                sort=True,
            ))
            fig_cam.update_layout(
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                showlegend=True, legend=dict(orientation="v", x=1.01, y=0.5),
                annotations=[dict(text=center_txt, x=0.5, y=0.5, font_size=13,
                                  showarrow=False, font_color="#C9D1D9")],
                margin=dict(t=30, b=20, l=20, r=160), height=480,
            )
            st.plotly_chart(fig_cam, use_container_width=True)
        except ImportError:
            st.info("Install plotly for charts.")

# ── Cash Flow Tab ─────────────────────────────────────────────────────────────
with tab_cashflow:
    st.markdown("""<div class='info-box'>
    ⓘ Revenue split into <b>partners</b> (distributed by %) and <b>charges</b>. Retained = remainder.
    Cascade: SCI members re-distribute received cash to their own partners.
    </div>""", unsafe_allow_html=True)

    with st.expander("⚙️ Configure monthly cash flow per SCI", expanded=False):
        cf_col1, cf_col2 = st.columns(2)
        with cf_col1:
            cf_text = st.text_area("Cash flow config", value=DEFAULT_CASHFLOW, height=380, label_visibility="collapsed")
        with cf_col2:
            st.caption("""**Format:**
```
SCI NAME:
  revenue  : 3000   ← monthly revenue €
  partners : 2000   ← fixed € to partners
  charges  : 1000   ← operating costs
```
Retained = revenue − partners − charges.""")
        if st.button("💾 Apply"):
            st.session_state["cf_text"] = cf_text
            st.success("Updated.")

    total_rev  = sum(v["revenue"]     for v in sci_cf.values())
    total_to_p = sum(v["to_partners"] for v in sci_cf.values())
    total_charg= sum(v["to_charges"]  for v in sci_cf.values())

    k1,k2,k3 = st.columns(3)
    for col,label,val,color,sub in [
        (k1,"Total Monthly Revenue", total_rev,   "#58A6FF", f"{total_rev*12:,.0f} €/yr"),
        (k2,"→ Partners (pool)",     total_to_p,  "#3FB950", f"{total_to_p*12:,.0f} €/yr"),
        (k3,"→ Charges",             total_charg, "#F85149", f"{total_charg*12:,.0f} €/yr"),
    ]:
        with col:
            col.markdown(f"""<div class='metric-card'><div class='label'>{label}</div>
                <div class='value' style='color:{color}'>{val:,.0f} €</div>
                <div class='sub'>{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Monthly Cash Flow by SCI</div>', unsafe_allow_html=True)
    try:
        import plotly.graph_objects as go
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(name="→ Partners", x=list(nodes), y=[sci_cf[s]["to_partners"] for s in nodes], marker_color="#3FB950"))
        fig_cf.add_trace(go.Bar(name="→ Charges",  x=list(nodes), y=[sci_cf[s]["to_charges"]  for s in nodes], marker_color="#F85149"))
        fig_cf.update_layout(barmode="stack", plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                             font_color="#C9D1D9", legend=dict(orientation="h",y=1.08,x=0),
                             yaxis=dict(gridcolor="#21262D",title="€/month"),
                             xaxis=dict(gridcolor="#21262D"), margin=dict(t=50,b=40,l=60,r=20))
        st.plotly_chart(fig_cf, use_container_width=True)
    except ImportError: pass

    # sci_rows_cf = []
    # for sci in nodes:
    #     cf = sci_cf[sci]
    #     sci_rows_cf.append({"SCI":sci,"Revenue (€/mo)":cf["revenue"],"Partners (€/mo)":cf["to_partners"],
    #                          "Charges (€/mo)":cf["to_charges"],"Annual Rev (€)":cf["revenue"]*12})
    # st.dataframe(pd.DataFrame(sci_rows_cf).style.format({
    #     "Revenue (€/mo)":"{:,.0f}","Partners (€/mo)":"{:,.0f}",
    #     "Charges (€/mo)":"{:,.0f}","Annual Rev (€)":"{:,.0f}"
    # }).background_gradient(subset=["Revenue (€/mo)"],cmap="Blues")
    #   .background_gradient(subset=["Partners (€/mo)"],cmap="Greens"),
    # use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">Partner Cash Flow Distribution</div>', unsafe_allow_html=True)
    cf_view = st.radio("CF View", ["Summary cards", "By SCI"], horizontal=True)
    sorted_persons_cf = sorted(all_persons, key=lambda p: -person_total_cf[P_idx[p]])

    if cf_view == "Summary cards":
        max_pcf = max(person_total_cf) if len(person_total_cf)>0 else 1
        cols3 = st.columns(3)
        for rank, person in enumerate(sorted_persons_cf):
            pi = P_idx[person]
            total_m=person_total_cf[pi]; direct_m=person_direct_cf[pi]; indir_m=person_indirect_cf[pi]
            bar_pct=int(total_m/max_pcf*100)
            sci_bd="".join(f"<span class='badge badge-blue'>{nodes[j]} {person_sci_cf_matrix[pi,j]:,.0f}€</span>"
                           for j in range(len(nodes)) if person_sci_cf_matrix[pi,j]>0.5)
            with cols3[rank%3]:
                st.markdown(f"""<div class='person-card'>
                  <div style='display:flex;justify-content:space-between;align-items:baseline'>
                    <div class='name'>#{rank+1} {person}</div>
                    <div class='wealth'>{total_m:,.0f} €<span style='font-size:.75rem;color:#6E7681'>/mo</span></div>
                  </div>
                  <div class='bar-bg'><div class='bar-fg' style='width:{bar_pct}%'></div></div>
                  <div style='font-size:.77rem;color:#8B949E;margin:.3rem 0'>
                    Direct: <b style='color:#3FB950'>{direct_m:,.0f}€</b> &nbsp;·&nbsp;
                    Cascade: <b style='color:#E3B341'>{indir_m:,.0f}€</b> &nbsp;·&nbsp;
                    Annual: <b style='color:#58A6FF'>{total_m*12:,.0f}€</b>
                  </div><div>{sci_bd}</div></div>""", unsafe_allow_html=True)

    elif cf_view == "By SCI":
        sci_cf_select=st.selectbox("Select SCI",nodes,key="cf_sci_select",label_visibility="collapsed")
        pool_this=sci_cf[sci_cf_select]["to_partners"]
        ca,cb=st.columns(2)
        with ca: ca.markdown(f"""<div class='metric-card'><div class='label'>Monthly Revenue</div>
            <div class='value'>{sci_cf[sci_cf_select]['revenue']:,.0f} €</div></div>""",unsafe_allow_html=True)
        with cb: cb.markdown(f"""<div class='metric-card'><div class='label'>Partner Pool</div>
            <div class='value' style='color:#3FB950'>{pool_this:,.0f} €/mo</div></div>""",unsafe_allow_html=True)
        shares_this=sci_shares.get(sci_cf_select,{})
        rows_bysci=[]
        for member,pct in sorted(shares_this.items(),key=lambda x:-x[1]):
            mtype="SCI" if member in set(nodes) else "Person"
            cash_d=pct*pool_this
            cash_t=person_total_cf[P_idx[member]] if member in P_idx else cash_d
            rows_bysci.append({"Member":member,"Type":mtype,"Direct %":pct*100,
                                "Direct CF (€/mo)":cash_d,"Direct CF (€/yr)":cash_d*12,
                                "Total CF (€/mo)":cash_t if mtype=="Person" else cash_d})
        df_bs=pd.DataFrame(rows_bysci)
        st.dataframe(df_bs.style.format({"Direct %":"{:.3f}%","Direct CF (€/mo)":"{:,.0f}",
            "Direct CF (€/yr)":"{:,.0f}","Total CF (€/mo)":"{:,.0f}"})
            .background_gradient(subset=["Direct CF (€/mo)"],cmap="Greens"),
            use_container_width=True, hide_index=True)

# ── Partner Profile Tab ───────────────────────────────────────────────────────
with tab_profile:
    sel_col, _ = st.columns([2, 4])
    with sel_col:
        selected_person = st.selectbox(
            "Select a partner",
            options=sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]]),
            format_func=lambda p: f"{p}  —  {person_wealth[P_idx[p]]:,.0f} €",
            label_visibility="collapsed",
        )

    pi      = P_idx[selected_person]
    pw      = person_wealth[pi]
    dir_cf  = person_direct_cf[pi]
    casc_cf = person_indirect_cf[pi]
    tot_cf  = person_total_cf[pi]
    direct_scis = person_sci_direct.get(selected_person, {})
    eff_stakes  = {nodes[j]: P_eff[pi, idx[nodes[j]]] for j in range(len(nodes)) if P_eff[pi,idx[nodes[j]]]>1e-7}
    cf_per_sci  = {nodes[j]: person_sci_cf_matrix[pi, j] for j in range(len(nodes))}
    total_invested = person_total_inv.get(selected_person, 0)
    gain           = pw - total_invested
    roi            = gain / total_invested * 100 if total_invested > 0 else 0

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    for col,label,val,color,sub in [
        (k1,"Total Wealth (direct)",  pw,            "#58A6FF", f"{pw/total_group_assets*100:.2f}% of group"),
        (k2,"Initial Investment",     total_invested,"#8B949E", f"{len(person_inv_by_sci.get(selected_person,{})) } SCI(s)"),
        (k3,"Gain / Loss",            gain,          "#3FB950" if gain>=0 else "#F85149", f"ROI {roi:+.1f}%"),
        (k4,"Monthly Cash · Direct",  dir_cf,        "#3FB950", f"{dir_cf*12:,.0f} €/yr"),
        (k5,"Monthly Cash · Cascade", casc_cf,       "#E3B341", f"{casc_cf*12:,.0f} €/yr"),
        (k6,"Total Monthly Income",   tot_cf,        "#79C0FF", f"{tot_cf*12:,.0f} €/yr"),
    ]:
        col.markdown(f"""<div class='metric-card'>
            <div class='label'>{label}</div>
            <div class='value' style='color:{color};font-size:1.1rem'>{val:,.0f} €</div>
            <div class='sub'>{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_mid = st.columns([1.1, 1.1], gap="large")

    # LEFT: memberships
    with col_left:
        st.markdown('<div class="section-header">SCI Memberships</div>', unsafe_allow_html=True)
        membership_rows=[]
        for sci in nodes:
            d_pct=direct_scis.get(sci,0); e_pct=eff_stakes.get(sci,0)
            if e_pct<1e-7: continue
            membership_rows.append({
                "SCI":sci,"Type":"Direct" if d_pct>1e-9 else "Indirect",
                "Direct %":d_pct*100,"Effective %":e_pct*100,
                "My Claim (€)":e_pct*equity_vec[idx[sci]],
                "CF (€/mo)":cf_per_sci.get(sci,0),
            })
        df_mem=pd.DataFrame(membership_rows).sort_values("Effective %",ascending=False)
        def _rs(row): bg="#0F2918" if row["Type"]=="Direct" else "#1A1600"; return [f"background-color:{bg}"]*len(row)
        st.dataframe(df_mem.style.apply(_rs,axis=1).format({
            "Direct %":"{:.3f}%","Effective %":"{:.4f}%","My Claim (€)":"{:,.0f}","CF (€/mo)":"{:,.0f}"}),
            use_container_width=True, hide_index=True, height=310)
        try:
            import plotly.graph_objects as go
            sci_w=[(s,d*equity_vec[idx[s]]) for s,d in sorted(direct_scis.items(),key=lambda x:-x[1]*equity_vec[idx[x[0]]])]
            if sci_w:
                fig_wb=go.Figure(go.Bar(x=[s for s,_ in sci_w],y=[v for _,v in sci_w],
                    marker_color="#1F6FEB",text=[f"{v:,.0f}€" for _,v in sci_w],textposition="outside",textfont_size=10))
                fig_wb.update_layout(plot_bgcolor="#0D1117",paper_bgcolor="#0D1117",font_color="#C9D1D9",
                    title=dict(text="Wealth by SCI (direct)",font_size=12),
                    yaxis=dict(gridcolor="#21262D",title="€"),xaxis=dict(gridcolor="#21262D"),
                    margin=dict(t=35,b=30,l=55,r=10),height=210)
                st.plotly_chart(fig_wb, use_container_width=True)
        except ImportError: pass

    # MID: cash flow donut + rank
    with col_mid:
        st.markdown('<div class="section-header">Cash Flow Breakdown</div>', unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            cf_labels=[s for s in nodes if cf_per_sci.get(s,0)>0.5]
            cf_vals_d=[cf_per_sci[s] for s in cf_labels]
            if cf_labels:
                fig_donut=go.Figure(go.Pie(labels=cf_labels,values=cf_vals_d,hole=0.55,
                    textinfo="label+percent",textfont_size=10,
                    marker=dict(colors=["#1F6FEB","#3FB950","#E3B341","#F85149","#A371F7","#58A6FF","#DB6D28"]),sort=True))
                fig_donut.update_layout(plot_bgcolor="#0D1117",paper_bgcolor="#0D1117",font_color="#C9D1D9",
                    showlegend=False,title=dict(text="CF by source SCI",font_size=12,x=0.5),
                    annotations=[dict(text=f"{tot_cf:,.0f}€<br>/mo",x=0.5,y=0.5,font_size=12,showarrow=False,font_color="#C9D1D9")],
                    margin=dict(t=40,b=5,l=5,r=5),height=270)
                st.plotly_chart(fig_donut, use_container_width=True)

            sorted_by_cf=sorted(all_persons,key=lambda p:-person_total_cf[P_idx[p]])
            colors_rank=["#F85149" if p==selected_person else "#388BFD" for p in sorted_by_cf]
            fig_rank=go.Figure(go.Bar(x=sorted_by_cf,y=[person_total_cf[P_idx[p]] for p in sorted_by_cf],
                marker_color=colors_rank,text=[f"{person_total_cf[P_idx[p]]:,.0f}" for p in sorted_by_cf],
                textposition="outside",textfont_size=8))
            fig_rank.update_layout(plot_bgcolor="#0D1117",paper_bgcolor="#0D1117",font_color="#C9D1D9",
                yaxis=dict(gridcolor="#21262D",title="€/mo"),xaxis=dict(gridcolor="#21262D",tickangle=-40,tickfont_size=8),
                title=dict(text="CF rank vs all partners",font_size=12),margin=dict(t=30,b=70,l=55,r=10),height=270)
            st.plotly_chart(fig_rank, use_container_width=True)
        except ImportError: pass

    # ── Investment section — full width below ──────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">Investment vs Current Wealth</div>', unsafe_allow_html=True)
    try:
        import plotly.graph_objects as go
        inv_by_sci = person_inv_by_sci.get(selected_person, {})
        if inv_by_sci:
            inv_col1, inv_col2 = st.columns([1.4, 1], gap="large")
            with inv_col1:
                sci_names_inv = list(inv_by_sci.keys())
                inv_vals    = [inv_by_sci[s] for s in sci_names_inv]
                wealth_vals = [direct_scis.get(s,0)*equity_vec[idx[s]] for s in sci_names_inv]
                gain_vals   = [w-i for w,i in zip(wealth_vals,inv_vals)]
                colors_gain = ["#3FB950" if g>=0 else "#F85149" for g in gain_vals]

                fig_inv = go.Figure()
                fig_inv.add_trace(go.Bar(name="Initial investment",x=sci_names_inv,y=inv_vals,
                    marker_color="#8B949E",opacity=0.85))
                fig_inv.add_trace(go.Bar(name="Current wealth",x=sci_names_inv,y=wealth_vals,
                    marker_color="#1F6FEB",opacity=0.85))
                fig_inv.update_layout(barmode="group",plot_bgcolor="#0D1117",paper_bgcolor="#0D1117",
                    font_color="#C9D1D9",legend=dict(orientation="h",y=1.06,x=0,font_size=10),
                    yaxis=dict(gridcolor="#21262D",title="€"),xaxis=dict(gridcolor="#21262D"),
                    title=dict(text="Invested vs current wealth per SCI",font_size=12),
                    margin=dict(t=45,b=40,l=60,r=10),height=260)
                st.plotly_chart(fig_inv, use_container_width=True)

                fig_gain = go.Figure(go.Bar(x=sci_names_inv, y=gain_vals,
                    marker_color=colors_gain, text=[f"{g:+,.0f}€" for g in gain_vals],
                    textposition="outside", textfont_size=10))
                fig_gain.update_layout(plot_bgcolor="#0D1117",paper_bgcolor="#0D1117",font_color="#C9D1D9",
                    yaxis=dict(gridcolor="#21262D",title="Gain / Loss €",zeroline=True,zerolinecolor="#58A6FF",zerolinewidth=1),
                    xaxis=dict(gridcolor="#21262D"),title=dict(text="Gain / Loss per SCI",font_size=12),
                    margin=dict(t=35,b=40,l=60,r=10),height=210)
                st.plotly_chart(fig_gain, use_container_width=True)

            with inv_col2:
                summary_rows = []
                for s in sci_names_inv:
                    inv  = inv_by_sci[s]
                    curr = direct_scis.get(s,0)*equity_vec[idx[s]]
                    g    = curr-inv
                    r    = g/inv*100 if inv>0 else 0
                    raw_w = partners_raw.get(s,{})
                    canon = next((k for k in raw_w if k.upper()==selected_person.upper()),None)
                    shares_held = raw_w.get(canon,0) if canon else 0
                    summary_rows.append({"SCI":s,"Shares":shares_held,
                        "Invested (€)":inv,"Current (€)":curr,
                        "Gain/Loss (€)":g,"ROI":f"{r:+.1f}%"})
                df_summ = pd.DataFrame(summary_rows)
                total_row = pd.DataFrame([{"SCI":"TOTAL","Shares":"—",
                    "Invested (€)":total_invested,"Current (€)":pw,
                    "Gain/Loss (€)":gain,"ROI":f"{roi:+.1f}%"}])
                df_summ = pd.concat([df_summ, total_row], ignore_index=True)
                st.dataframe(df_summ.style.format({
                    "Invested (€)":"{:,.0f}","Current (€)":"{:,.0f}",
                    "Gain/Loss (€)":"{:+,.0f}"})
                    .background_gradient(subset=["Gain/Loss (€)"],cmap="RdYlGn"),
                    use_container_width=True, hide_index=True, height=530)
        else:
            st.info("No initial investment data found for this partner.")
    except ImportError:
        st.info("Install plotly for charts.")

# ── Graph Tab ─────────────────────────────────────────────────────────────────
with tab_graph:
    ctrl1, ctrl2, ctrl3 = st.columns([1.3,1.3,3])
    with ctrl1: show_partners  = st.toggle("👥 Show partners",   value=True)
    with ctrl2: show_effective = st.toggle("📈 Show effective %", value=False)
    with ctrl3:
        if show_effective: st.caption("Solid = direct · dashed = indirect-only · % = effective")
        else:              st.caption("Showing direct stakes only")

    col_g1, col_g2 = st.columns([4,1])
    with col_g2:
        st.markdown('<div class="section-header">Legend</div>', unsafe_allow_html=True)
        st.markdown("""<div style='font-size:.8rem;color:#8B949E;line-height:1.9'>
        <span style='color:#58A6FF'>●</span> SCI (size = equity)<br/>
        <span style='color:#E3B341'>●</span> Partner (size = wealth)<br/>
        <span style='color:#3FB950'>—</span> Direct stake<br/>
        <span style='color:#E3B341'>┄</span> Indirect-only</div>""", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="margin-top:1rem">SCI Equity</div>', unsafe_allow_html=True)
        for node in nodes:
            eq=equity_vec[idx[node]]
            st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.8rem'>"
                        f"<span style='color:#C9D1D9'>{node}</span>"
                        f"<span style='color:#58A6FF;font-weight:600'>{eq:,.0f}€</span></div>", unsafe_allow_html=True)
        if show_partners:
            st.markdown('<div class="section-header" style="margin-top:1rem">Top 5</div>', unsafe_allow_html=True)
            for p in sorted(all_persons,key=lambda p:-person_wealth[P_idx[p]])[:5]:
                w=person_wealth[P_idx[p]]
                st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.8rem'>"
                            f"<span style='color:#C9D1D9'>{p}</span>"
                            f"<span style='color:#E3B341;font-weight:600'>{w:,.0f}€</span></div>", unsafe_allow_html=True)
    with col_g1:
        net = build_pyvis(nodes, edges, equity_vec, dir_assets, sci_shares,
                          show_partners=show_partners, show_effective=show_effective,
                          all_persons=all_persons, P_idx=P_idx, P_eff=P_eff,
                          person_wealth=person_wealth, idx=idx)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
            net.save_graph(f.name); html_path=f.name
        with open(html_path,"r",encoding="utf-8") as f: html_content=f.read()
        html_content=html_content.replace("<body>","<body style='background:#0D1117;margin:0;padding:0'>")
        os.unlink(html_path)
        st.components.v1.html(html_content, height=730, scrolling=False)