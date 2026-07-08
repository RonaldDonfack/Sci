import streamlit as st
import pandas as pd
import numpy as np
import re
from pyvis.network import Network
import tempfile, os

st.set_page_config(page_title="Investment Cycle · Equity Calculator", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
h1,h2,h3{font-family:'Space Grotesk',sans-serif;}
.stApp{background:#0D1117;color:#E6EDF3;}
.block-container{padding-top:2rem;max-width:1500px;}
.metric-card{background:linear-gradient(135deg,#161B22 0%,#1C2128 100%);border:1px solid #30363D;border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:.8rem;transition:border-color .2s;}
.metric-card:hover{border-color:#58A6FF;}
.metric-card .label{font-size:.72rem;font-weight:600;color:#8B949E;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.3rem;}
.metric-card .value{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;color:#58A6FF;}
.metric-card .sub{font-size:.78rem;color:#6E7681;margin-top:.2rem;}
.section-header{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;color:#C9D1D9;border-left:3px solid #58A6FF;padding-left:.75rem;margin:1.5rem 0 1rem 0;}
.stTextArea textarea{background:#161B22!important;border:1px solid #30363D!important;color:#C9D1D9!important;border-radius:8px!important;font-size:.85rem!important;}
.stNumberInput input,.stTextInput input{background:#161B22!important;border:1px solid #30363D!important;color:#C9D1D9!important;border-radius:8px!important;}
.stButton>button{background:linear-gradient(135deg,#1F6FEB,#388BFD);color:white;border:none;border-radius:8px;font-weight:600;padding:.5rem 1.5rem;}
.stButton>button:hover{background:linear-gradient(135deg,#388BFD,#58A6FF);transform:translateY(-1px);}
.stDataFrame{border-radius:10px;overflow:hidden;}
thead tr th{background:#161B22!important;color:#8B949E!important;font-size:.78rem!important;letter-spacing:.06em!important;text-transform:uppercase!important;}
tbody tr td{color:#C9D1D9!important;font-size:.88rem!important;}
tbody tr:nth-child(even) td{background:#161B22!important;}
.person-card{background:#161B22;border:1px solid #30363D;border-radius:10px;padding:1rem 1.2rem;margin-bottom:.6rem;transition:border-color .2s;}
.person-card:hover{border-color:#3FB950;}
.person-card .name{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;color:#E6EDF3;}
.person-card .wealth{font-family:'Space Grotesk',sans-serif;font-size:1.3rem;font-weight:700;color:#3FB950;}
.person-card .bar-bg{background:#21262D;border-radius:4px;height:6px;margin:.5rem 0;}
.person-card .bar-fg{background:linear-gradient(90deg,#238636,#3FB950);border-radius:4px;height:6px;}
.badge{display:inline-block;background:#0F2918;border:1px solid #238636;border-radius:999px;padding:.1rem .55rem;font-size:.72rem;color:#3FB950;margin:.15rem;}
.badge-blue{background:#0D1F3C;border-color:#1F6FEB;color:#58A6FF;}
.badge-gray{background:#161B22;border-color:#444C56;color:#8B949E;}
.info-box{background:#0D1F3C;border:1px solid #1F6FEB;border-radius:8px;padding:.75rem 1rem;font-size:.83rem;color:#8B949E;margin:1rem 0;}
</style>
""", unsafe_allow_html=True)

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

DEFAULT_CASHFLOW = """LEM IMMO : 3000 : 60 : 40
M2N IMMO : 3000 : 60 : 40
LEM2 IMMO : 4500 : 60 : 40
LEM SYNERGIE : 4500 : 60 : 40
LEM VIRY : 3000 : 60 : 40
LEM ALLIANCE : 3500 : 60 : 40
LEM INVEST : 2000 : 60 : 40"""

SCI_UNIT_COST = {
    "M2N IMMO":45000,"LEM IMMO":23000,"LEM2 IMMO":26000,
    "LEM ALLIANCE":10000,"LEM INVEST":7500,"LEM SYNERGIE":28000,"LEM VIRY":25000,
}

PALETTE = ["#58A6FF","#3FB950","#E3B341","#F85149","#A371F7","#DB6D28","#79C0FF",
           "#56D364","#F778BA","#388BFD","#FF6B6B","#C9D1D9","#FFD700","#00CED1"]

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
            assets[m.group(1).strip().upper()] = float(m.group(2).replace(" ", "").replace(",", "."))
    return assets

def parse_partners(text):
    result = {}; current_sci = None
    for line in text.strip().splitlines():
        line = line.strip()
        if not line: continue
        if line.endswith(":") and line.count(":") == 1:
            current_sci = line[:-1].strip().upper(); result[current_sci] = {}
        elif current_sci and ":" in line:
            parts = line.rsplit(":", 1); name = parts[0].strip()
            try: weight = float(parts[1].strip().replace(",", "."))
            except: weight = 1.0
            result[current_sci][name.upper()] = weight
    return result

def parse_cashflow(text):
    result = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = [p.strip() for p in line.split(":")]
        if len(parts) >= 4:
            sci = parts[0].upper()
            try:
                rev = float(parts[1]); pp = float(parts[2]) / 100.0; cp = float(parts[3]) / 100.0
                result[sci] = {"revenue": rev, "partner_pct": pp, "charges_pct": cp}
            except: pass
        elif len(parts) == 3:
            sci = parts[0].upper()
            try:
                rev = float(parts[1])
                result[sci] = {"revenue": rev, "partner_pct": 0.60, "charges_pct": 0.40}
            except: pass
    return result

def compute_all(edges, direct_assets, partners_raw):
    nodes = sorted({n for e in edges for n in (e[0], e[1])} | set(direct_assets.keys()))
    idx = {n: i for i, n in enumerate(nodes)}; n = len(nodes)
    W = np.zeros((n, n))
    for src, dst, pct in edges: W[idx[src], idx[dst]] += pct
    A_vec = np.array([direct_assets.get(nd, 0.0) for nd in nodes])
    try:
        IminusW = np.eye(n) - W
        equity_vec = np.linalg.solve(IminusW, A_vec)
        inv_IW = np.linalg.inv(IminusW)
    except np.linalg.LinAlgError:
        equity_vec = A_vec.copy()
        for _ in range(2000):
            new_eq = A_vec + W @ equity_vec
            if np.allclose(new_eq, equity_vec, rtol=1e-10): break
            equity_vec = new_eq
        inv_IW = np.eye(n)
    E = inv_IW - np.eye(n)
    sci_set = set(nodes)
    all_persons = sorted({m for members in partners_raw.values() for m in members if m not in sci_set})
    P_idx = {p: i for i, p in enumerate(all_persons)}
    P_direct = np.zeros((len(all_persons), n)); sci_shares = {}
    EPSILON_CORRECTIONS = {"LEM VIRY": "MARTIAL"}
    for sci_name, members in partners_raw.items():
        if sci_name not in idx: continue
        j = idx[sci_name]; total_w = sum(members.values())
        if total_w == 0: continue
        shares = {m: w / total_w for m, w in members.items()}
        residual = 1.0 - sum(shares.values())
        if abs(residual) > 0:
            target = EPSILON_CORRECTIONS.get(sci_name) or max(shares, key=lambda m: shares[m])
            if target in shares: shares[target] += residual
        sci_shares[sci_name] = shares
        for member, pct in shares.items():
            if member in P_idx: P_direct[P_idx[member], j] = pct
    person_wealth = P_direct @ equity_vec
    person_sci_direct = {p: {} for p in all_persons}
    for sci_name, shares in sci_shares.items():
        for member, pct in shares.items():
            if member in P_idx: person_sci_direct[member][sci_name] = pct
    P_eff = P_direct @ inv_IW
    return (nodes, equity_vec, W, E, idx, all_persons, P_idx, P_direct, P_eff,
            person_wealth, sci_shares, person_sci_direct)

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
    max_eq = max(equity_vec) if len(equity_vec) > 0 else 1
    sci_colors = ["#1C2840","#1A3560","#1A4A7A","#1F6FEB","#388BFD","#58A6FF","#79C0FF"]
    for node in nodes:
        i = idx_map[node]; eq = equity_vec[i]; da = direct_assets.get(node, 0)
        ratio = eq / max_eq if max_eq > 0 else 0
        color = sci_colors[min(int(ratio*(len(sci_colors)-1)), len(sci_colors)-1)]
        shares = sci_shares.get(node, {})
        partner_html = "".join(f"<span style='color:#8B949E'>{m}</span>: <b>{p*100:.2f}%</b><br/>"
                               for m, p in sorted(shares.items(), key=lambda x: -x[1]))
        title = (f"<div style='font-family:Inter;padding:8px;min-width:200px'>"
                 f"<b style='color:#58A6FF'>{node}</b><hr style='border-color:#30363D;margin:4px 0'/>"
                 f"<span style='color:#8B949E'>Direct assets</span>: <b>{da:,.0f} €</b><br/>"
                 f"<span style='color:#8B949E'>Total equity</span>: <b style='color:#3FB950'>{eq:,.0f} €</b>"
                 f"<hr style='border-color:#30363D;margin:4px 0'/>{partner_html}</div>")
        net.add_node(node, label=f"{node}\n{da:,.0f}€", title=title, shape="dot",
                     color={"background": color, "border": "#58A6FF",
                            "highlight": {"background": "#388BFD", "border": "#79C0FF"}},
                     size=26+ratio*34, font={"size": 11+int(ratio*3), "color": "#E6EDF3"})
    for src, dst, pct in edges:
        net.add_edge(src, dst, label=f"{pct*100:.2f}%", title=f"{src} owns {pct*100:.2f}% of {dst}",
                     width=1+pct*4, color={"color": "#30363D"})
    if show_partners and all_persons:
        person_colors = ["#E3B341","#DB6D28","#F778BA","#A371F7","#56D364"]
        for p_i, person in enumerate(all_persons):
            wealth = person_wealth[P_idx[person]] if person_wealth is not None else 0
            max_w = max(person_wealth) if person_wealth is not None and len(person_wealth) > 0 else 1
            w_ratio = wealth / max_w if max_w > 0 else 0
            p_color = person_colors[p_i % len(person_colors)]
            holdings_html = ""
            for sci_name in nodes:
                eff_pct = P_eff[P_idx[person], idx[sci_name]] if P_eff is not None else 0
                if eff_pct > 1e-6:
                    direct_pct = sci_shares.get(sci_name, {}).get(person, 0)
                    tag_color = "#3FB950" if direct_pct > 1e-9 else "#E3B341"
                    holdings_html += (f"<span style='color:#8B949E'>{sci_name}</span>: "
                                      f"<b>{eff_pct*100:.3f}%</b> "
                                      f"<span style='color:{tag_color};font-size:9px'>({'direct' if direct_pct>1e-9 else 'indirect'})</span><br/>")
            title = (f"<div style='font-family:Inter;padding:8px;min-width:210px'>"
                     f"<b style='color:{p_color}'>{person}</b><hr style='border-color:#30363D;margin:4px 0'/>"
                     f"<span style='color:#8B949E'>Total wealth</span>: <b style='color:#3FB950'>{wealth:,.0f} €</b>"
                     f"<hr style='border-color:#30363D;margin:4px 0'/>{holdings_html}</div>")
            net.add_node(f"P::{person}", label=person, title=title, shape="dot",
                         color={"background": p_color, "border": "#0D1117",
                                "highlight": {"background": p_color, "border": "#E6EDF3"}},
                         size=12+w_ratio*16, font={"size": 11, "color": "#C9D1D9"})
            for sci_name in nodes:
                direct_pct = sci_shares.get(sci_name, {}).get(person, 0)
                eff_pct = P_eff[P_idx[person], idx[sci_name]] if P_eff is not None else 0
                if direct_pct > 1e-9:
                    lbl = f"{eff_pct*100:.2f}%" if show_effective else f"{direct_pct*100:.2f}%"
                    net.add_edge(f"P::{person}", sci_name, label=lbl, width=0.8+direct_pct*3,
                                 color={"color": p_color, "opacity": 0.55}, dashes=False)
                elif show_effective and eff_pct > 1e-6:
                    net.add_edge(f"P::{person}", sci_name, label=f"{eff_pct*100:.3f}%",
                                 width=0.6, color={"color": p_color, "opacity": 0.25}, dashes=True)
    return net

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

with tab_input:
    col1, col2, col3 = st.columns([2, 1.5, 2], gap="large")
    with col1:
        st.markdown('<div class="section-header">Ownership Relations</div>', unsafe_allow_html=True)
        relations_text = st.text_area("Relations", value=DEFAULT_RELATIONS, height=300, label_visibility="collapsed")
        st.markdown('<div class="section-header">➕ Add New SCI (simulation)</div>', unsafe_allow_html=True)
        nc1, nc2, nc3 = st.columns([2, 2, 1])
        with nc1: new_sci_name = st.text_input("SCI name", placeholder="LEM NOUVEAU", label_visibility="collapsed")
        with nc2: new_sci_assets = st.number_input("Direct assets €", min_value=0, value=100000, step=10000, label_visibility="collapsed")
        with nc3:
            if st.button("＋ SCI"):
                if new_sci_name:
                    nm = new_sci_name.strip().upper()
                    st.session_state["extra_assets"] = st.session_state.get("extra_assets", "") + f"\n{nm} : {new_sci_assets}"
                    st.session_state["extra_cf"] = st.session_state.get("extra_cf", "") + f"\n{nm} : 1000 : 60 : 40"
                    st.success(f"Added {nm}")
        st.markdown('<div class="section-header">➕ Add Ownership Link</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: new_src = st.text_input("From", placeholder="LEM IMMO", label_visibility="collapsed")
        with c2: new_dst = st.text_input("To", placeholder="LEM INVEST", label_visibility="collapsed")
        with c3: new_pct = st.number_input("%", min_value=0.0, max_value=100.0, value=10.0, step=0.5, label_visibility="collapsed")
        with c4:
            if st.button("＋ Link"):
                if new_src and new_dst:
                    st.session_state["extra_relations"] = st.session_state.get("extra_relations", "") + f"\n{new_src.upper()} -> {new_dst.upper()} : {new_pct}%"
                    st.success("Link added.")
    with col2:
        st.markdown('<div class="section-header">Direct Assets (€)</div>', unsafe_allow_html=True)
        assets_text = st.text_area("Assets", value=DEFAULT_ASSETS + st.session_state.get("extra_assets", ""),
                                   height=200, label_visibility="collapsed")
        st.markdown('<div class="section-header">Cash Flow Config</div>', unsafe_allow_html=True)
        st.caption("`SCI : revenue : partner% : charges%` — default 60/40")
        cf_default = DEFAULT_CASHFLOW + st.session_state.get("extra_cf", "")
        cf_text = st.text_area("CF", value=st.session_state.get("cf_text", cf_default),
                               height=210, label_visibility="collapsed")
        st.markdown('<div class="section-header">➕ Add SCI Cash Flow</div>', unsafe_allow_html=True)
        acf1, acf2, acf3, acf4 = st.columns([2, 1, 1, 1])
        with acf1: new_cf_sci = st.text_input("SCI", placeholder="NEW SCI", label_visibility="collapsed", key="cf_sci_add")
        with acf2: new_cf_rev = st.number_input("Rev €", min_value=0, value=2000, step=500, label_visibility="collapsed", key="cf_rev")
        with acf3: new_cf_pp = st.number_input("P%", min_value=0, max_value=100, value=60, label_visibility="collapsed", key="cf_pp")
        with acf4:
            if st.button("＋ CF"):
                if new_cf_sci:
                    line = f"\n{new_cf_sci.upper()} : {new_cf_rev} : {new_cf_pp} : {100-new_cf_pp}"
                    st.session_state["cf_text"] = st.session_state.get("cf_text", cf_default) + line
                    st.success("CF line added.")
    with col3:
        st.markdown('<div class="section-header">Partner Shareholdings</div>', unsafe_allow_html=True)
        partners_text = st.text_area("Partners", value=DEFAULT_PARTNERS, height=480, label_visibility="collapsed")
    full_relations = relations_text + st.session_state.get("extra_relations", "")
    if st.button("⚙️  Calculate", type="primary"):
        st.session_state.update({"calc_done": True, "relations_text": full_relations,
                                  "assets_text": assets_text, "partners_text": partners_text,
                                  "cf_text": cf_text})
        st.success("✅ Done — see results tabs.")

if "calc_done" not in st.session_state:
    st.session_state.update({"calc_done": True, "relations_text": DEFAULT_RELATIONS,
                              "assets_text": DEFAULT_ASSETS, "partners_text": DEFAULT_PARTNERS,
                              "cf_text": DEFAULT_CASHFLOW})

edges = parse_relations(st.session_state["relations_text"])
dir_assets = parse_assets(st.session_state["assets_text"])
partners_raw = parse_partners(st.session_state.get("partners_text", DEFAULT_PARTNERS))

(nodes, equity_vec, W, E, idx,
 all_persons, P_idx, P_direct, P_eff, person_wealth,
 sci_shares, person_sci_direct) = compute_all(edges, dir_assets, partners_raw)

total_group_assets = sum(dir_assets.values())

_cf_raw = parse_cashflow(st.session_state.get("cf_text", DEFAULT_CASHFLOW))
sci_cf = {}
for _sci in nodes:
    cfg = _cf_raw.get(_sci, {"revenue": 0, "partner_pct": 0.60, "charges_pct": 0.40})
    rev = cfg["revenue"]; pp = cfg["partner_pct"]; cp = cfg["charges_pct"]
    sci_cf[_sci] = {"revenue": rev, "to_partners": rev * pp, "to_charges": rev * cp,
                    "partner_pct": pp, "charges_pct": cp}

pool_vec = np.array([sci_cf[_sci]["to_partners"] for _sci in nodes])
try:    inv_IW_cf = np.linalg.inv(np.eye(len(nodes)) - W)
except: inv_IW_cf = np.eye(len(nodes))
pool_eff = inv_IW_cf @ pool_vec

# ── CF matrix: EFFECTIVE % × fixed pool
# person_sci_cf_matrix[p, j] = P_eff[p,j] × pool_vec[j]
# P_eff[p,j] = effective ownership % of person p in SCI j (direct + all chains)
# pool_vec[j] = fixed monthly partner pool of SCI j
# This shows how much each person draws from each SCI via all ownership paths.
# Total conserved: sum across all persons = pool_vec.sum() (no double-counting)
person_sci_cf_matrix = P_eff * pool_vec[np.newaxis, :]      # (persons × scis)
person_total_cf      = person_sci_cf_matrix.sum(axis=1)
person_direct_cf     = (P_direct * pool_vec[np.newaxis, :]).sum(axis=1)
person_indirect_cf   = person_total_cf - person_direct_cf

def compute_initial_investments(partners_raw, sci_shares, SCI_UNIT_COST):
    person_inv_by_sci = {p: {} for p in all_persons}
    for sci_name, shares in sci_shares.items():
        unit_cost = SCI_UNIT_COST.get(sci_name, 0)
        if unit_cost == 0: continue
        raw_members = partners_raw.get(sci_name, {})
        for member, weight in raw_members.items():
            canon = next((p for p in all_persons if p.upper() == member.upper()), None)
            if canon:
                person_inv_by_sci[canon][sci_name] = person_inv_by_sci[canon].get(sci_name, 0) + weight * unit_cost
    return person_inv_by_sci, {p: sum(v.values()) for p, v in person_inv_by_sci.items()}

person_inv_by_sci, person_total_inv = compute_initial_investments(partners_raw, sci_shares, SCI_UNIT_COST)

sci_total_inv = {}
for sci_name in nodes:
    unit_cost = SCI_UNIT_COST.get(sci_name, 0)
    raw_members = partners_raw.get(sci_name, {})
    sci_total_inv[sci_name] = sum(
        w * unit_cost for m, w in raw_members.items()
        if next((p for p in all_persons if p.upper() == m.upper()), None) is not None and unit_cost > 0)

def eff_badges(person):
    html = ""
    for sci in nodes:
        e_pct = P_eff[P_idx[person], idx[sci]]
        if e_pct < 1e-7: continue
        d_pct = person_sci_direct.get(person, {}).get(sci, 0)
        if d_pct > 1e-9:
            html += f"<span class='badge badge-blue'>{sci} {e_pct*100:.2f}%</span>"
        else:
            html += f"<span class='badge badge-gray'>{sci} {e_pct*100:.2f}% ↗</span>"
    return html

# ── SCI Equity Tab ─────────────────────────────────────────────────────────────
with tab_results:
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class='metric-card'><div class='label'>Total Group Assets</div>
        <div class='value'>{total_group_assets:,.0f} €</div>
        <div class='sub'>Sum of direct assets · no double-counting</div></div>""", unsafe_allow_html=True)
    with k2:
        top_node = nodes[int(np.argmax(equity_vec))]
        st.markdown(f"""<div class='metric-card'><div class='label'>Largest SCI (equity)</div>
        <div class='value' style='font-size:1.15rem'>{top_node}</div>
        <div class='sub'>{equity_vec[int(np.argmax(equity_vec))]:,.0f} €</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class='metric-card'><div class='label'>SCIs Modelled</div>
        <div class='value'>{len(nodes)}</div><div class='sub'>{len(edges)} ownership links</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class='metric-card'><div class='label'>Partners</div>
        <div class='value'>{len(all_persons)}</div><div class='sub'>across all SCIs</div></div>""", unsafe_allow_html=True)
    st.markdown("""<div class='info-box'>
    ⓘ <b>Total Equity</b> per SCI = own direct assets + proportional share of subsidiaries,
    solved via (I−W)·equity = direct_assets. Group total = sum of direct assets only.
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-header">SCI Equity Breakdown</div>', unsafe_allow_html=True)
    rows = []
    for node in nodes:
        i = idx[node]; da = dir_assets.get(node, 0); eq = equity_vec[i]
        owners = [(nodes[j], W[j,i]*100) for j in range(len(nodes)) if W[j,i] > 0]
        owned  = [(nodes[j], W[i,j]*100) for j in range(len(nodes)) if W[i,j] > 0]
        shares = sci_shares.get(node, {})
        rows.append({"SCI": node,"Unit Cost (€)": SCI_UNIT_COST.get(node, 0),
                     "Total Invested (€)": sci_total_inv.get(node, 0),
                     "Direct Assets (€)": da, "Total Equity (€)": eq,
                     "Human Partners": sum(1 for m in shares if m not in set(nodes)),
                     "Owned by SCIs": ", ".join(f"{o} ({p:.2f}%)" for o, p in owners) if owners else "—",
                     "Owns SCIs":     ", ".join(f"{o} ({p:.2f}%)" for o, p in owned) if owned else "—"})
    df = pd.DataFrame(rows).sort_values("Total Equity (€)", ascending=False).reset_index(drop=True)
    st.dataframe(
        df.style.format({"Direct Assets (€)": "{:,.0f}", "Total Equity (€)": "{:,.0f}",
                          "Unit Cost (€)": "{:,.0f}", "Total Invested (€)": "{:,.0f}"})
               .background_gradient(subset=["Total Equity (€)"], cmap="Blues")
               .background_gradient(subset=["Direct Assets (€)"], cmap="Greens")
               .background_gradient(subset=["Total Invested (€)"], cmap="Oranges"),
        use_container_width=True, height=340)
    with st.expander("🔍 Effective SCI→SCI Ownership Matrix"):
        df_E = pd.DataFrame(E*100, index=nodes, columns=nodes)
        st.dataframe(df_E.style.format("{:.3f}%").background_gradient(cmap="Blues", vmin=0, vmax=50), use_container_width=True)

# ── Partner Wealth Tab ─────────────────────────────────────────────────────────
with tab_partners:
    total_person_wealth = person_wealth.sum()
    rounding_gap = abs(total_group_assets - total_person_wealth)
    kp1, kp2, kp3 = st.columns(3)
    with kp1: st.markdown(f"""<div class='metric-card'><div class='label'>Total Partner Wealth</div>
        <div class='value'>{total_person_wealth:,.0f} €</div>
        <div class='sub'>Sum across {len(all_persons)} partners</div></div>""", unsafe_allow_html=True)
    with kp2: st.markdown(f"""<div class='metric-card'><div class='label'>Group Real Assets</div>
        <div class='value'>{total_group_assets:,.0f} €</div>
        <div class='sub'>True consolidated total</div></div>""", unsafe_allow_html=True)
    with kp3: st.markdown(f"""<div class='metric-card'><div class='label'>Reconciliation Gap</div>
        <div class='value' style='color:{"#3FB950" if rounding_gap<100 else "#F85149"}'>{rounding_gap:,.2f} €</div>
        <div class='sub'>{"✓ Rounding only" if rounding_gap<100 else "⚠ Check partner weights"}</div></div>""",
        unsafe_allow_html=True)
    fc, _ = st.columns([2, 4])
    with fc:
        partner_filter = st.selectbox("Filter partner",
            options=["— All partners —"] + sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]]),
            label_visibility="collapsed")
    sorted_persons = sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]])
    display_persons = sorted_persons if partner_filter == "— All partners —" else [partner_filter]
    view_mode = st.radio("View", ["💰 Wealth %", "💰 Wealth €", "🥧 Camembert"],
                         horizontal=True, label_visibility="collapsed")

    if view_mode == "💰 Wealth %":
        st.markdown('<div class="section-header">Partner Wealth — % of Group Assets</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for ri, person in enumerate(sorted_persons):
            if person not in display_persons: continue
            pw = person_wealth[P_idx[person]]
            pct_grp = pw / total_group_assets * 100
            bar_pct = int(pw / max(person_wealth) * 100)
            with cols[ri % 3]:
                st.markdown(f"""
                <div class='person-card'>
                  <div style='display:flex;justify-content:space-between;align-items:baseline'>
                    <div class='name'>#{ri+1} {person}</div>
                    <div class='wealth'>{pct_grp:.2f}%</div>
                  </div>
                  <div style='font-size:.8rem;color:#8B949E;margin:.1rem 0'>{pw:,.0f} € of {total_group_assets:,.0f} €</div>
                  <div class='bar-bg'><div class='bar-fg' style='width:{bar_pct}%'></div></div>
                  <div style='margin-top:.4rem'>{eff_badges(person)}</div>
                </div>""", unsafe_allow_html=True)

    elif view_mode == "💰 Wealth €":
        # ── CHANGE 1: show effective wealth (eff % × equity) per SCI, no % badges ──
        st.markdown('<div class="section-header">Partner Wealth — € from effective ownership per SCI</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for ri, person in enumerate(sorted_persons):
            if person not in display_persons: continue
            pi_p = P_idx[person]
            pw = person_wealth[pi_p]
            bar_pct = int(pw / max(person_wealth) * 100)
            # Effective wealth per SCI = P_eff[p, j] × equity[j]
            sci_eff_wealth = [(nodes[j], P_eff[pi_p, j] * equity_vec[j])
                              for j in range(len(nodes)) if P_eff[pi_p, j] > 1e-7]
            sci_eff_wealth.sort(key=lambda x: -x[1])
            # Badges show SCI name + € amount from effective ownership
            sci_badges = "".join(
                f"<span class='badge badge-blue'>{sci} {amt:,.0f}€</span>"
                for sci, amt in sci_eff_wealth
            )
            with cols[ri % 3]:
                st.markdown(f"""
                <div class='person-card'>
                  <div style='display:flex;justify-content:space-between;align-items:baseline'>
                    <div class='name'>#{ri+1} {person}</div>
                    <div class='wealth'>{pw:,.0f} €</div>
                  </div>
                  <div style='font-size:.8rem;color:#8B949E;margin:.1rem 0'>{pw/total_group_assets*100:.2f}% of group</div>
                  <div class='bar-bg'><div class='bar-fg' style='width:{bar_pct}%'></div></div>
                  <div style='margin-top:.4rem'>{sci_badges}</div>
                </div>""", unsafe_allow_html=True)

    else:
        st.markdown('<div class="section-header">Wealth Distribution — Camembert</div>', unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            if len(display_persons) == 1:
                p = display_persons[0]; pi_p = P_idx[p]
                # Effective wealth per SCI for this single person
                labels = [nodes[j] for j in range(len(nodes)) if P_eff[pi_p, j] > 1e-7]
                vals   = [P_eff[pi_p, idx[s]] * equity_vec[idx[s]] for s in labels]
                center_txt = f"{person_wealth[pi_p]:,.0f}€<br>total"
            else:
                labels = display_persons; vals = [person_wealth[P_idx[p]] for p in display_persons]
                center_txt = f"{sum(vals):,.0f}€<br>total"
            fig_cam = go.Figure(go.Pie(
                labels=labels, values=vals, hole=0.52,
                textinfo="label+percent+value", textfont_size=11,
                texttemplate="%{label}<br>%{percent}<br>%{value:,.0f}€",
                marker=dict(colors=[PALETTE[i % len(PALETTE)] for i in range(len(labels))]), sort=True))
            fig_cam.update_layout(
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                showlegend=True, legend=dict(orientation="v", x=1.01, y=0.5),
                annotations=[dict(text=center_txt, x=0.5, y=0.5, font_size=13,
                                  showarrow=False, font_color="#C9D1D9")],
                margin=dict(t=30, b=20, l=20, r=160), height=480)
            st.plotly_chart(fig_cam, use_container_width=True)
            if len(display_persons) == 1:
                st.markdown(f"**Effective stakes:** {eff_badges(display_persons[0])}", unsafe_allow_html=True)
        except ImportError: st.info("Install plotly.")

# ── Cash Flow Tab ──────────────────────────────────────────────────────────────
with tab_cashflow:
    st.markdown("""<div class='info-box'>
    ⓘ Cash flow uses <b>effective ownership % × effective pool</b>. Each partner's share from
    each SCI = their total effective % (direct + indirect chains) × that SCI's augmented pool.
    Total distributed = total fixed pool (conserved).
    </div>""", unsafe_allow_html=True)
    with st.expander("⚙️ Configure monthly cash flow per SCI", expanded=False):
        cf_col1, cf_col2 = st.columns(2)
        with cf_col1:
            cf_edit = st.text_area("CF config", value=st.session_state.get("cf_text", DEFAULT_CASHFLOW),
                                   height=300, label_visibility="collapsed")
        with cf_col2:
            st.caption("""**Format:** `SCI : revenue : partner% : charges%`
```
LEM IMMO : 3000 : 60 : 40
```
- **revenue** = monthly € generated by the SCI
- **partner%** = % distributed to partners (default 60)
- **charges%** = % for operating costs (default 40)""")
        if st.button("💾 Apply CF config"):
            st.session_state["cf_text"] = cf_edit
            st.success("Updated — click Calculate to refresh.")
    total_rev   = sum(v["revenue"]     for v in sci_cf.values())
    total_to_p  = sum(v["to_partners"] for v in sci_cf.values())
    total_charg = sum(v["to_charges"]  for v in sci_cf.values())
    k1, k2, k3 = st.columns(3)
    for col, label, val, color, sub in [
        (k1, "Total Monthly Revenue", total_rev,   "#58A6FF", f"{total_rev*12:,.0f} €/yr"),
        (k2, "→ Partners (pool)",     total_to_p,  "#3FB950", f"{total_to_p*12:,.0f} €/yr"),
        (k3, "→ Charges",             total_charg, "#F85149", f"{total_charg*12:,.0f} €/yr"),
    ]:
        with col: col.markdown(f"""<div class='metric-card'><div class='label'>{label}</div>
            <div class='value' style='color:{color}'>{val:,.0f} €</div>
            <div class='sub'>{sub}</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Revenue & Split by SCI</div>', unsafe_allow_html=True)
    try:
        import plotly.graph_objects as go
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(name="→ Partners", x=list(nodes),
                                y=[sci_cf[s]["to_partners"] for s in nodes], marker_color="#3FB950"))
        fig_cf.add_trace(go.Bar(name="→ Charges",  x=list(nodes),
                                y=[sci_cf[s]["to_charges"]  for s in nodes], marker_color="#F85149"))
        fig_cf.update_layout(barmode="stack", plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                             font_color="#C9D1D9", legend=dict(orientation="h", y=1.08, x=0),
                             yaxis=dict(gridcolor="#21262D", title="€/month"),
                             xaxis=dict(gridcolor="#21262D"), margin=dict(t=50, b=40, l=60, r=20))
        st.plotly_chart(fig_cf, use_container_width=True)
    except ImportError: pass
    st.markdown('<div class="section-header">Partner Cash Flow Distribution</div>', unsafe_allow_html=True)
    cf_view = st.radio("CF View", ["Summary cards", "By SCI"], horizontal=True)
    sorted_persons_cf = sorted(all_persons, key=lambda p: -person_total_cf[P_idx[p]])
    if cf_view == "Summary cards":
        max_pcf = max(person_total_cf) if len(person_total_cf) > 0 else 1
        cols3 = st.columns(3)
        for rank, person in enumerate(sorted_persons_cf):
            pi = P_idx[person]
            total_m = person_total_cf[pi]; direct_m = person_direct_cf[pi]; indir_m = person_indirect_cf[pi]
            bar_pct = int(total_m / max_pcf * 100)
            sci_bd = "".join(
                f"<span class='badge badge-blue'>{nodes[j]} {person_sci_cf_matrix[pi,j]:,.0f}€</span>"
                for j in range(len(nodes)) if person_sci_cf_matrix[pi, j] > 0.5)
            with cols3[rank % 3]:
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
    else:
        sci_cf_select = st.selectbox("Select SCI", nodes, key="cf_sci_select", label_visibility="collapsed")
        pool_this = sci_cf[sci_cf_select]["to_partners"]
        pool_eff_this = pool_eff[idx[sci_cf_select]]
        pct_label = f"{sci_cf[sci_cf_select]['partner_pct']*100:.0f}% of {sci_cf[sci_cf_select]['revenue']:,.0f} €"
        ca, cb, cc = st.columns(3)
        with ca: ca.markdown(f"""<div class='metric-card'><div class='label'>Monthly Revenue</div>
            <div class='value'>{sci_cf[sci_cf_select]['revenue']:,.0f} €</div>
            <div class='sub'>{pct_label} → partners</div></div>""", unsafe_allow_html=True)
        with cb: cb.markdown(f"""<div class='metric-card'><div class='label'>Fixed Partner Pool</div>
            <div class='value' style='color:#3FB950'>{pool_this:,.0f} €/mo</div></div>""", unsafe_allow_html=True)
        with cc: cc.markdown(f"""<div class='metric-card'><div class='label'>Effective Pool (augmented)</div>
            <div class='value' style='color:#58A6FF'>{pool_eff_this:,.0f} €/mo</div>
            <div class='sub'>incl. inter-SCI receipts</div></div>""", unsafe_allow_html=True)
        shares_this = sci_shares.get(sci_cf_select, {})
        rows_bysci = []
        for member, pct in sorted(shares_this.items(), key=lambda x: -x[1]):
            mtype = "SCI" if member in set(nodes) else "Person"
            cash_d = pct * pool_this
            if member in P_idx:
                eff_pct_here = P_eff[P_idx[member], idx[sci_cf_select]]
                cash_eff = eff_pct_here * pool_eff_this
                cash_t = person_total_cf[P_idx[member]]
            else:
                eff_pct_here = pct; cash_eff = pct * pool_eff_this; cash_t = cash_d
            rows_bysci.append({"Member": member, "Type": mtype, "Direct %": pct * 100,
                                "Eff % in SCI": eff_pct_here * 100,
                                "CF direct (€/mo)": cash_d, "CF effective (€/mo)": cash_eff,
                                "Member total CF": cash_t if mtype == "Person" else cash_d})
        df_bs = pd.DataFrame(rows_bysci)
        # Table kept in code but hidden
        # st.dataframe(df_bs...)
        try:
            import plotly.graph_objects as go
            persons_m = [r["Member"] for r in rows_bysci if r["Type"] == "Person"]
            scis_m    = [r["Member"] for r in rows_bysci if r["Type"] == "SCI"]
            all_m = persons_m + scis_m
            vals_eff = [next(r["CF effective (€/mo)"] for r in rows_bysci if r["Member"] == m) for m in all_m]
            colors_b = ["#3FB950"] * len(persons_m) + ["#58A6FF"] * len(scis_m)
            fig_bs = go.Figure(go.Bar(x=all_m, y=vals_eff, marker_color=colors_b,
                text=[f"{v:,.0f}€" for v in vals_eff], textposition="outside", textfont_size=9))
            fig_bs.update_layout(plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                yaxis=dict(gridcolor="#21262D", title="€/month"), xaxis=dict(gridcolor="#21262D", tickangle=-30),
                title=dict(text=f"Effective CF from {sci_cf_select} (eff % × eff. pool)", font_size=13),
                margin=dict(t=40, b=80, l=60, r=20))
            st.plotly_chart(fig_bs, use_container_width=True)
        except ImportError: pass

# ── Partner Profile Tab ────────────────────────────────────────────────────────
with tab_profile:
    sel_col, _ = st.columns([2, 4])
    with sel_col:
        selected_person = st.selectbox(
            "Select a partner",
            options=sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]]),
            format_func=lambda p: f"{p}  —  {person_wealth[P_idx[p]]:,.0f} €",
            label_visibility="collapsed")

    pi = P_idx[selected_person]; pw = person_wealth[pi]
    dir_cf = person_direct_cf[pi]; casc_cf = person_indirect_cf[pi]; tot_cf = person_total_cf[pi]
    direct_scis = person_sci_direct.get(selected_person, {})
    eff_stakes  = {nodes[j]: P_eff[pi, idx[nodes[j]]] for j in range(len(nodes)) if P_eff[pi, idx[nodes[j]]] > 1e-7}
    # CF per SCI = effective % × fixed pool — shows each SCI's contribution via all ownership chains
    cf_per_sci  = {nodes[j]: P_eff[pi, j] * pool_vec[j] for j in range(len(nodes))}
    total_invested = person_total_inv.get(selected_person, 0)
    gain = pw - total_invested; roi = gain / total_invested * 100 if total_invested > 0 else 0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    for col, label, val, color, sub in [
        (k1, "Total Wealth (direct)",   pw,            "#58A6FF", f"{pw/total_group_assets*100:.2f}% of group"),
        (k2, "Initial Investment",      total_invested, "#8B949E", f"{len(person_inv_by_sci.get(selected_person, {}))} SCI(s)"),
        (k3, "Gain / Loss",             gain,          "#3FB950" if gain >= 0 else "#F85149", f"ROI {roi:+.1f}%"),
        (k4, "Monthly Cash · Direct",   dir_cf,        "#3FB950", f"{dir_cf*12:,.0f} €/yr"),
        (k5, "Monthly Cash · Cascade",  casc_cf,       "#E3B341", f"{casc_cf*12:,.0f} €/yr"),
        (k6, "Total Monthly Income",    tot_cf,        "#79C0FF", f"{tot_cf*12:,.0f} €/yr"),
    ]:
        col.markdown(f"""<div class='metric-card'>
            <div class='label'>{label}</div>
            <div class='value' style='color:{color};font-size:1.1rem'>{val:,.0f} €</div>
            <div class='sub'>{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_mid = st.columns([1.1, 1.1], gap="large")

    with col_left:
        st.markdown('<div class="section-header">SCI Memberships</div>', unsafe_allow_html=True)
        membership_rows = []
        for sci in nodes:
            d_pct = direct_scis.get(sci, 0); e_pct = eff_stakes.get(sci, 0)
            if e_pct < 1e-7: continue
            membership_rows.append({
                "SCI": sci, "Type": "Direct" if d_pct > 1e-9 else "Indirect",
                "Direct %": d_pct * 100, "Effective %": e_pct * 100,
                # Wealth = effective % × equity (correct claim)
                "My Claim (€)": e_pct * equity_vec[idx[sci]],
                # CF = effective % × effective pool
                "CF eff (€/mo)": cf_per_sci.get(sci, 0),
            })
        df_mem = pd.DataFrame(membership_rows).sort_values("Effective %", ascending=False)
        def _rs(row): bg = "#0F2918" if row["Type"] == "Direct" else "#1A1600"; return [f"background-color:{bg}"] * len(row)
        st.dataframe(
            df_mem.style.apply(_rs, axis=1).format({
                "Direct %": "{:.3f}%", "Effective %": "{:.4f}%",
                "My Claim (€)": "{:,.0f}", "CF eff (€/mo)": "{:,.0f}"}),
            use_container_width=True, hide_index=True, height=310)
        try:
            import plotly.graph_objects as go
            sci_w = [(s, d*equity_vec[idx[s]]) for s, d in sorted(direct_scis.items(), key=lambda x: -x[1]*equity_vec[idx[x[0]]])]
            if sci_w:
                fig_wb = go.Figure(go.Bar(x=[s for s, _ in sci_w], y=[v for _, v in sci_w],
                    marker_color="#1F6FEB", text=[f"{v:,.0f}€" for _, v in sci_w],
                    textposition="outside", textfont_size=10))
                fig_wb.update_layout(plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                    title=dict(text="Wealth by SCI (direct)", font_size=12),
                    yaxis=dict(gridcolor="#21262D", title="€"), xaxis=dict(gridcolor="#21262D"),
                    margin=dict(t=35, b=30, l=55, r=10), height=210)
                st.plotly_chart(fig_wb, use_container_width=True)
        except ImportError: pass

    with col_mid:
        st.markdown('<div class="section-header">Cash Flow — effective % × effective pool</div>', unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            # Donut: CF per SCI from effective ownership
            cf_sci_labels = [s for s in nodes if cf_per_sci.get(s, 0) > 0.5]
            cf_sci_vals   = [cf_per_sci[s] for s in cf_sci_labels]
            if cf_sci_labels:
                fig_donut = go.Figure(go.Pie(labels=cf_sci_labels, values=cf_sci_vals, hole=0.55,
                    textinfo="label+percent", textfont_size=10,
                    marker=dict(colors=[PALETTE[i % len(PALETTE)] for i in range(len(cf_sci_labels))]), sort=True))
                fig_donut.update_layout(plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                    showlegend=False, title=dict(text="CF by source SCI (eff %)", font_size=12, x=0.5),
                    annotations=[dict(text=f"{tot_cf:,.0f}€<br>/mo", x=0.5, y=0.5,
                                      font_size=12, showarrow=False, font_color="#C9D1D9")],
                    margin=dict(t=40, b=5, l=5, r=5), height=260)
                st.plotly_chart(fig_donut, use_container_width=True)
            # Bar: CF per source SCI
            cf_sci_all = sorted([(s, cf_per_sci.get(s, 0)) for s in nodes if cf_per_sci.get(s, 0) > 0.1], key=lambda x: -x[1])
            if cf_sci_all:
                fig_cfbar = go.Figure(go.Bar(
                    x=[s for s, _ in cf_sci_all], y=[v for _, v in cf_sci_all],
                    marker_color=[PALETTE[i % len(PALETTE)] for i in range(len(cf_sci_all))],
                    text=[f"{v:,.0f}€" for _, v in cf_sci_all], textposition="outside", textfont_size=9))
                fig_cfbar.update_layout(plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                    title=dict(text="Monthly CF per SCI (eff % × eff pool)", font_size=12),
                    yaxis=dict(gridcolor="#21262D", title="€/mo"), xaxis=dict(gridcolor="#21262D", tickangle=-30),
                    margin=dict(t=35, b=70, l=55, r=10), height=245)
                st.plotly_chart(fig_cfbar, use_container_width=True)
        except ImportError: pass

    # ── Annual Cash ROI on Investment ─────────────────────────────────────────────
    st.markdown('<div class="section-header">Cash Flow ROI on Investment</div>', unsafe_allow_html=True)

    annual_cf = tot_cf * 12
    cash_roi = (annual_cf / total_invested * 100) if total_invested > 0 else 0
    years_to_recoup = (total_invested / annual_cf) if annual_cf > 0 else float("inf")

    r1, r2, r3 = st.columns(3)
    with r1:
        r1.markdown(f"""<div class='metric-card'>
            <div class='label'>Annual Cash Flow</div>
            <div class='value' style='color:#3FB950'>{annual_cf:,.0f} €</div>
            <div class='sub'>{tot_cf:,.0f} €/mo × 12</div></div>""", unsafe_allow_html=True)
    with r2:
        r2.markdown(f"""<div class='metric-card'>
            <div class='label'>Total Invested</div>
            <div class='value' style='color:#8B949E'>{total_invested:,.0f} €</div>
            <div class='sub'>{len(person_inv_by_sci.get(selected_person, {}))} SCI(s)</div></div>""",
                    unsafe_allow_html=True)
    with r3:
        roi_color = "#3FB950" if cash_roi >= 5 else "#E3B341" if cash_roi >= 2 else "#F85149"
        r3.markdown(f"""<div class='metric-card'>
            <div class='label'>Cash ROI (annual)</div>
            <div class='value' style='color:{roi_color}'>{cash_roi:.2f}%</div>
            <div class='sub'>≈ {years_to_recoup:.1f} yrs to recoup investment</div></div>""", unsafe_allow_html=True)

    # Per-SCI breakdown
    try:
        import plotly.graph_objects as go

        inv_by_sci = person_inv_by_sci.get(selected_person, {})
        if inv_by_sci:
            rows_roi = []
            for s in inv_by_sci:
                inv_s = inv_by_sci[s]
                cf_mo_s = person_sci_cf_matrix[pi, idx[s]] if s in idx else 0
                cf_yr_s = cf_mo_s * 12
                roi_s = (cf_yr_s / inv_s * 100) if inv_s > 0 else 0
                recoup_s = (inv_s / cf_yr_s) if cf_yr_s > 0 else float("inf")
                rows_roi.append({
                    "SCI": s,
                    "Invested (€)": inv_s,
                    "CF / month (€)": cf_mo_s,
                    "CF / year (€)": cf_yr_s,
                    "Cash ROI (%)": roi_s,
                    "Recoup (years)": round(recoup_s, 1) if recoup_s != float("inf") else "∞",
                })
            df_roi = pd.DataFrame(rows_roi)

            # Add total row
            total_roi_row = pd.DataFrame([{
                "SCI": "TOTAL",
                "Invested (€)": total_invested,
                "CF / month (€)": tot_cf,
                "CF / year (€)": annual_cf,
                "Cash ROI (%)": cash_roi,
                "Recoup (years)": round(years_to_recoup, 1) if years_to_recoup != float("inf") else "∞",
            }])
            df_roi = pd.concat([df_roi, total_roi_row], ignore_index=True)

            st.dataframe(
                df_roi.style.format({
                    "Invested (€)": "{:,.0f}",
                    "CF / month (€)": "{:,.2f}",
                    "CF / year (€)": "{:,.2f}",
                    "Cash ROI (%)": "{:.2f}%",
                }).background_gradient(subset=["Cash ROI (%)"], cmap="RdYlGn"),
                use_container_width=True, hide_index=True
            )

            # Bar chart
            df_plot = df_roi[df_roi["SCI"] != "TOTAL"]
            fig_roi = go.Figure(go.Bar(
                x=df_plot["SCI"],
                y=df_plot["Cash ROI (%)"],
                marker_color=["#3FB950" if v >= 5 else "#E3B341" if v >= 2 else "#F85149"
                              for v in df_plot["Cash ROI (%)"]],
                text=[f"{v:.2f}%" for v in df_plot["Cash ROI (%)"]],
                textposition="outside", textfont_size=11,
            ))
            fig_roi.add_hline(y=cash_roi, line_dash="dot", line_color="#58A6FF",
                              annotation_text=f"Average {cash_roi:.2f}%",
                              annotation_position="top right")
            fig_roi.update_layout(
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                yaxis=dict(gridcolor="#21262D", title="Annual cash ROI %",
                           zeroline=True, zerolinecolor="#444C56"),
                xaxis=dict(gridcolor="#21262D"),
                title=dict(text="Annual cash ROI per SCI  =  (CF × 12) / invested × 100", font_size=12),
                margin=dict(t=45, b=40, l=60, r=20), height=260,
            )
            st.plotly_chart(fig_roi, use_container_width=True)

    except ImportError:
        st.info("Install plotly for ROI chart.")
    # st.markdown("---")
    # st.markdown('<div class="section-header">Investment vs Current Wealth</div>', unsafe_allow_html=True)
    # try:
    #     import plotly.graph_objects as go
    #     inv_by_sci = person_inv_by_sci.get(selected_person, {})
    #     if inv_by_sci:
    #         inv_col1, inv_col2 = st.columns([1.4, 1], gap="large")
    #         with inv_col1:
    #             sci_names_inv = list(inv_by_sci.keys())
    #             inv_vals    = [inv_by_sci[s] for s in sci_names_inv]
    #             wealth_vals = [direct_scis.get(s, 0)*equity_vec[idx[s]] for s in sci_names_inv]
    #             gain_vals   = [w - i for w, i in zip(wealth_vals, inv_vals)]
    #             colors_gain = ["#3FB950" if g >= 0 else "#F85149" for g in gain_vals]
    #             fig_inv = go.Figure()
    #             fig_inv.add_trace(go.Bar(name="Initial investment", x=sci_names_inv, y=inv_vals,
    #                 marker_color="#8B949E", opacity=0.85))
    #             fig_inv.add_trace(go.Bar(name="Current wealth", x=sci_names_inv, y=wealth_vals,
    #                 marker_color="#1F6FEB", opacity=0.85))
    #             fig_inv.update_layout(barmode="group", plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
    #                 font_color="#C9D1D9", legend=dict(orientation="h", y=1.06, x=0, font_size=10),
    #                 yaxis=dict(gridcolor="#21262D", title="€"), xaxis=dict(gridcolor="#21262D"),
    #                 title=dict(text="Invested vs current wealth per SCI", font_size=12),
    #                 margin=dict(t=45, b=40, l=60, r=10), height=260)
    #             st.plotly_chart(fig_inv, use_container_width=True)
    #             fig_gain = go.Figure(go.Bar(x=sci_names_inv, y=gain_vals, marker_color=colors_gain,
    #                 text=[f"{g:+,.0f}€" for g in gain_vals], textposition="outside", textfont_size=10))
    #             fig_gain.update_layout(plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
    #                 yaxis=dict(gridcolor="#21262D", title="Gain/Loss €", zeroline=True,
    #                            zerolinecolor="#58A6FF", zerolinewidth=1),
    #                 xaxis=dict(gridcolor="#21262D"),
    #                 title=dict(text="Gain/Loss per SCI", font_size=12),
    #                 margin=dict(t=35, b=40, l=60, r=10), height=210)
    #             st.plotly_chart(fig_gain, use_container_width=True)
    #         with inv_col2:
    #             summary_rows = []
    #             for s in sci_names_inv:
    #                 inv  = inv_by_sci[s]; curr = direct_scis.get(s, 0)*equity_vec[idx[s]]
    #                 g = curr - inv; r = g / inv * 100 if inv > 0 else 0
    #                 raw_w = partners_raw.get(s, {})
    #                 canon = next((k for k in raw_w if k.upper() == selected_person.upper()), None)
    #                 shares_held = raw_w.get(canon, 0) if canon else 0
    #                 summary_rows.append({"SCI": s, "Shares": shares_held,
    #                     "Invested (€)": inv, "Current (€)": curr,
    #                     "Gain/Loss (€)": g, "ROI": f"{r:+.1f}%"})
    #             df_summ = pd.DataFrame(summary_rows)
    #             total_row = pd.DataFrame([{"SCI": "TOTAL", "Shares": "—",
    #                 "Invested (€)": total_invested, "Current (€)": pw,
    #                 "Gain/Loss (€)": gain, "ROI": f"{roi:+.1f}%"}])
    #             df_summ = pd.concat([df_summ, total_row], ignore_index=True)
    #             st.dataframe(df_summ.style.format({
    #                 "Invested (€)": "{:,.0f}", "Current (€)": "{:,.0f}", "Gain/Loss (€)": "{:+,.0f}"})
    #                 .background_gradient(subset=["Gain/Loss (€)"], cmap="RdYlGn"),
    #                 use_container_width=True, hide_index=True, height=530)
    #     else:
    #         st.info("No initial investment data found for this partner.")
    # except ImportError: st.info("Install plotly.")

# ── Graph Tab ──────────────────────────────────────────────────────────────────
with tab_graph:
    ctrl1, ctrl2, ctrl3 = st.columns([1.3, 1.3, 3])
    with ctrl1: show_partners  = st.toggle("👥 Show partners",    value=True)
    with ctrl2: show_effective = st.toggle("📈 Show effective %", value=False)
    with ctrl3:
        if show_effective: st.caption("Solid = direct · dashed = indirect-only · % = effective")
        else: st.caption("Showing direct stakes only")
    col_g1, col_g2 = st.columns([4, 1])
    with col_g2:
        st.markdown('<div class="section-header">Legend</div>', unsafe_allow_html=True)
        st.markdown("""<div style='font-size:.8rem;color:#8B949E;line-height:1.9'>
        <span style='color:#58A6FF'>●</span> SCI (size = equity)<br/>
        <span style='color:#E3B341'>●</span> Partner (size = wealth)<br/>
        <span style='color:#3FB950'>—</span> Direct stake<br/>
        <span style='color:#E3B341'>┄</span> Indirect-only</div>""", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="margin-top:1rem">SCI Equity</div>', unsafe_allow_html=True)
        for node in nodes:
            eq = equity_vec[idx[node]]
            st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.8rem'>"
                        f"<span style='color:#C9D1D9'>{node}</span>"
                        f"<span style='color:#58A6FF;font-weight:600'>{eq:,.0f}€</span></div>", unsafe_allow_html=True)
        if show_partners:
            st.markdown('<div class="section-header" style="margin-top:1rem">Top 5</div>', unsafe_allow_html=True)
            for p in sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]])[:5]:
                w = person_wealth[P_idx[p]]
                st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:.8rem'>"
                            f"<span style='color:#C9D1D9'>{p}</span>"
                            f"<span style='color:#E3B341;font-weight:600'>{w:,.0f}€</span></div>", unsafe_allow_html=True)
    with col_g1:
        net = build_pyvis(nodes, edges, equity_vec, dir_assets, sci_shares,
                          show_partners=show_partners, show_effective=show_effective,
                          all_persons=all_persons, P_idx=P_idx, P_eff=P_eff,
                          person_wealth=person_wealth, idx=idx)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
            net.save_graph(f.name); html_path = f.name
        with open(html_path, "r", encoding="utf-8") as f: html_content = f.read()
        html_content = html_content.replace("<body>", "<body style='background:#0D1117;margin:0;padding:0'>")
        os.unlink(html_path)
        st.components.v1.html(html_content, height=730, scrolling=False)