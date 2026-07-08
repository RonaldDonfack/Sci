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

# ── CSS ──────────────────────────────────────────────────────────────────────
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

# ── Defaults ─────────────────────────────────────────────────────────────────
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

# Partners: "NAME : weight" or "SCI NAME : weight" per line, one block per SCI
# SCI blocks separated by blank lines, header line = SCI name
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
    """Returns dict: {SCI_NAME: {member_name: weight}}"""
    result = {}
    current_sci = None
    for line in text.strip().splitlines():
        line = line.strip()
        if not line: continue
        # Header line ends with ':'
        if line.endswith(":") and ":" == line[-1] and line.count(":") == 1:
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

# ── Default cash flow config per SCI ─────────────────────────────────────────
# Format per block: SCI NAME:
#   revenue  : fixed € per month
#   partners : fixed € per month distributed to partners
#   staff    : fixed € per month for salaries / payroll
#   charges  : fixed € per month for operating charges
#   (remainder = revenue - partners - staff - charges → retained cash)
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

def parse_cashflow(text):
    """Parse cash flow config into {SCI: {revenue, to_partners, to_staff, to_charges}}
    All values are fixed € amounts per month."""
    result = {}
    current = None
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped: continue
        if stripped.endswith(":") and stripped.count(":") == 1:
            current = stripped[:-1].strip().upper()
            result[current] = {"revenue": 0, "to_partners": 0,
                                "to_staff": 0, "to_charges": 0}
        elif current and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip().lower().replace(" ", "")
            try:
                v = float(val.strip().replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            if "revenue" in key:
                result[current]["revenue"] = v
            elif "partner" in key:
                result[current]["to_partners"] = v
            elif "staff" in key:
                result[current]["to_staff"] = v
            elif "charge" in key:
                result[current]["to_charges"] = v
    return result

# ── Core calculation ──────────────────────────────────────────────────────────
def compute_all(edges, direct_assets, partners_raw):
    nodes = sorted({n for e in edges for n in (e[0], e[1])} | set(direct_assets.keys()))
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)

    W = np.zeros((n, n))
    for src, dst, pct in edges:
        W[idx[src], idx[dst]] += pct

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

    # ── Partner analysis ──────────────────────────────────────────────────────
    # Identify all human persons (not SCI nodes)
    sci_set = set(nodes)
    all_persons = set()
    for sci, members in partners_raw.items():
        for m in members:
            if m not in sci_set:
                all_persons.add(m)
    all_persons = sorted(all_persons)
    P_idx = {p: i for i, p in enumerate(all_persons)}
    np_persons = len(all_persons)

    # P_direct[person, sci] = direct % that person holds in that SCI
    P_direct = np.zeros((np_persons, n))
    # sci_shares[sci] = {member: normalized_pct}
    sci_shares = {}

    # Designated residual-absorber per SCI (optional). If a SCI isn't listed
    # here, the residual falls back to whoever already holds the largest share.
    EPSILON_CORRECTIONS = {
        "LEM VIRY": "MARTIAL",
    }

    for sci_name, members in partners_raw.items():
        if sci_name not in idx: continue
        j = idx[sci_name]
        total_w = sum(members.values())
        if total_w == 0: continue
        shares = {m: w / total_w for m, w in members.items()}

        # ── Residual correction so shares always sum to exactly 1.0 ─────────────
        # Floating point division (e.g. 1/9 = 0.111111...) can leave a tiny gap.
        residual = 1.0 - sum(shares.values())
        if abs(residual) > 0:
            target_member = EPSILON_CORRECTIONS.get(sci_name) or max(shares, key=lambda m: shares[m])
            if target_member in shares:
                shares[target_member] += residual

        sci_shares[sci_name] = shares
        for member, pct in shares.items():
            if member in P_idx:
                P_direct[P_idx[member], j] = pct

    # Person wealth (no double counting):
    # wealth[p] = sum_k P_direct[p,k] * equity[k]
    # This works because equity[k] = inv(I-W)[k,:] @ assets, which already
    # propagates all indirect SCI chains. Multiplying by person's direct % in k
    # gives their true consolidated claim on underlying assets.
    person_wealth = P_direct @ equity_vec

    # Person's direct % breakdown per SCI (for display)
    # person_sci_pct[p, j] = direct % person p holds in SCI j
    person_sci_direct = {p: {} for p in all_persons}
    for sci_name, shares in sci_shares.items():
        for member, pct in shares.items():
            if member in P_idx:
                person_sci_direct[member][sci_name] = pct

    # Person's effective % in each SCI (through all chains)
    # eff[p, sci_j] = sum_k P_direct[p,k] * inv_IW[k,j]
    P_eff = P_direct @ inv_IW  # shape (persons, scis)

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
    sci_set = set(nodes)
    max_eq = max(equity_vec) if len(equity_vec) > 0 else 1
    colors = ["#1C2840","#1A3560","#1A4A7A","#1F6FEB","#388BFD","#58A6FF","#79C0FF"]

    # ── SCI nodes ──────────────────────────────────────────────────────────────
    for node in nodes:
        i = idx_map[node]
        eq = equity_vec[i]
        da = direct_assets.get(node, 0)
        ratio = eq / max_eq if max_eq > 0 else 0
        color = colors[min(int(ratio * (len(colors)-1)), len(colors)-1)]
        size = 26 + ratio * 34
        shares = sci_shares.get(node, {})
        partner_html = "".join(
            f"<span style='color:#8B949E'>{m}</span>: <b>{p*100:.2f}%</b><br/>"
            for m, p in sorted(shares.items(), key=lambda x: -x[1])
        ) if shares else ""
        title = (f"<div style='font-family:Inter;padding:8px;min-width:200px'>"
                 f"<b style='color:#58A6FF'>{node}</b> <span style='color:#6E7681;font-size:10px'>(SCI)</span>"
                 f"<hr style='border-color:#30363D;margin:4px 0'/>"
                 f"<span style='color:#8B949E'>Direct assets</span>: <b>{da:,.0f} €</b><br/>"
                 f"<span style='color:#8B949E'>Total equity</span>: <b style='color:#3FB950'>{eq:,.0f} €</b>"
                 f"<hr style='border-color:#30363D;margin:4px 0'/>"
                 f"<span style='color:#8B949E;font-size:11px'>Direct stakeholders:</span><br/>{partner_html}"
                 f"</div>")
        net.add_node(node, label=node, title=title, shape="dot",
                     color={"background":color,"border":"#58A6FF",
                            "highlight":{"background":"#388BFD","border":"#79C0FF"}},
                     size=size, font={"size":13+int(ratio*4),"color":"#E6EDF3"})

    # ── SCI → SCI ownership edges ────────────────────────────────────────────
    for src, dst, pct in edges:
        net.add_edge(src, dst, label=f"{pct*100:.2f}%",
                     title=f"{src} owns {pct*100:.2f}% of {dst}",
                     width=1+pct*4, color={"color":"#30363D"})

    # ── Partner nodes + their direct / indirect links ────────────────────────
    if show_partners and all_persons:
        person_colors = ["#E3B341","#DB6D28","#F778BA","#A371F7","#56D364"]
        for p_i, person in enumerate(all_persons):
            wealth = person_wealth[P_idx[person]] if person_wealth is not None else 0
            max_wealth = max(person_wealth) if person_wealth is not None and len(person_wealth) > 0 else 1
            w_ratio = wealth / max_wealth if max_wealth > 0 else 0
            p_color = person_colors[p_i % len(person_colors)]
            p_size = 12 + w_ratio * 16

            # Build per-SCI breakdown for tooltip: direct vs effective
            holdings_html = ""
            for sci_name in nodes:
                eff_pct = P_eff[P_idx[person], idx[sci_name]] if P_eff is not None else 0
                if eff_pct > 1e-6:
                    direct_pct = sci_shares.get(sci_name, {}).get(person, 0)
                    is_direct = direct_pct > 1e-9
                    tag = "direct" if is_direct else "indirect"
                    tag_color = "#3FB950" if is_direct else "#E3B341"
                    holdings_html += (
                        f"<span style='color:#8B949E'>{sci_name}</span>: "
                        f"<b>{eff_pct*100:.3f}%</b> "
                        f"<span style='color:{tag_color};font-size:9px'>({tag})</span><br/>"
                    )

            title = (f"<div style='font-family:Inter;padding:8px;min-width:210px'>"
                     f"<b style='color:{p_color}'>{person}</b> <span style='color:#6E7681;font-size:10px'>(Partner)</span>"
                     f"<hr style='border-color:#30363D;margin:4px 0'/>"
                     f"<span style='color:#8B949E'>Total wealth</span>: <b style='color:#3FB950'>{wealth:,.0f} €</b>"
                     f"<hr style='border-color:#30363D;margin:4px 0'/>"
                     f"<span style='color:#8B949E;font-size:11px'>Effective stake per SCI:</span><br/>{holdings_html}"
                     f"</div>")
            net.add_node(f"P::{person}", label=person, title=title, shape="dot",
                         color={"background":p_color,"border":"#0D1117",
                                "highlight":{"background":p_color,"border":"#E6EDF3"}},
                         size=p_size, font={"size":11,"color":"#C9D1D9"})

            # Edges: direct stakes always shown solid; indirect shown dashed if toggle on
            for sci_name in nodes:
                direct_pct = sci_shares.get(sci_name, {}).get(person, 0)
                eff_pct = P_eff[P_idx[person], idx[sci_name]] if P_eff is not None else 0

                if direct_pct > 1e-9:
                    label = f"{eff_pct*100:.2f}%" if show_effective else f"{direct_pct*100:.2f}%"
                    net.add_edge(f"P::{person}", sci_name, label=label,
                                 title=f"{person} owns {direct_pct*100:.2f}% direct"
                                       + (f" · {eff_pct*100:.3f}% effective" if show_effective else ""),
                                 width=0.8+direct_pct*3,
                                 color={"color": p_color, "opacity": 0.55},
                                 dashes=False)
                elif show_effective and eff_pct > 1e-6:
                    # indirect-only relationship, shown as dashed thin edge when effective view is on
                    net.add_edge(f"P::{person}", sci_name, label=f"{eff_pct*100:.3f}%",
                                 title=f"{person} has {eff_pct*100:.3f}% indirect (through subsidiary chains)",
                                 width=0.6, color={"color": p_color, "opacity": 0.25},
                                 dashes=True)

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

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_input, tab_results, tab_partners, tab_cashflow, tab_profile, tab_graph = st.tabs([
    "📋 Data Input", "📊 SCI Equity", "👥 Partner Wealth", "💶 Cash Flow", "🔍 Partner Profile", "🕸️ Relationship Graph"
])

# ── Input Tab ─────────────────────────────────────────────────────────────────
with tab_input:
    col1, col2, col3 = st.columns([2, 1.5, 2], gap="large")
    with col1:
        st.markdown('<div class="section-header">Ownership Relations</div>', unsafe_allow_html=True)
        st.caption("Format: `SCI A -> SCI B : XX%`")
        relations_text = st.text_area("Relations", value=DEFAULT_RELATIONS, height=360, label_visibility="collapsed")
    with col2:
        st.markdown('<div class="section-header">Direct Assets (€)</div>', unsafe_allow_html=True)
        st.caption("Format: `SCI : value`")
        assets_text = st.text_area("Assets", value=DEFAULT_ASSETS, height=240, label_visibility="collapsed")
        st.markdown('<div class="section-header">Add a Link</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: new_src = st.text_input("From", placeholder="LEM IMMO", label_visibility="collapsed")
        with c2: new_dst = st.text_input("To", placeholder="LEM INVEST", label_visibility="collapsed")
        with c3: new_pct = st.number_input("%", min_value=0.0, max_value=100.0, value=10.0, step=0.5, label_visibility="collapsed")
        with c4:
            if st.button("＋"):
                if new_src and new_dst:
                    st.session_state["extra_relations"] = st.session_state.get("extra_relations","") + f"\n{new_src.upper()} -> {new_dst.upper()} : {new_pct}%"
                    st.success("Added")
    with col3:
        st.markdown('<div class="section-header">Partner Shareholdings</div>', unsafe_allow_html=True)
        st.caption("One block per SCI. Header = `SCI NAME:` then `Member : weight` per line. SCI names as members are allowed.")
        partners_text = st.text_area("Partners", value=DEFAULT_PARTNERS, height=500, label_visibility="collapsed")

    full_relations = relations_text + st.session_state.get("extra_relations", "")
    if st.button("⚙️  Calculate", type="primary"):
        st.session_state.update({"calc_done": True, "relations_text": full_relations,
                                  "assets_text": assets_text, "partners_text": partners_text})
        st.success("✅ Done — see results tabs.")

# ── Run calculation ───────────────────────────────────────────────────────────
if "calc_done" not in st.session_state:
    st.session_state.update({"calc_done": True,
                              "relations_text": DEFAULT_RELATIONS,
                              "assets_text": DEFAULT_ASSETS,
                              "partners_text": DEFAULT_PARTNERS})

edges     = parse_relations(st.session_state["relations_text"])
dir_assets = parse_assets(st.session_state["assets_text"])
partners_raw = parse_partners(st.session_state.get("partners_text", DEFAULT_PARTNERS))

(nodes, equity_vec, W, E, idx,
 all_persons, P_idx, P_direct, P_eff, person_wealth,
 sci_shares, person_sci_direct) = compute_all(edges, dir_assets, partners_raw)

# ── Module-scope cash flow computation (shared by Cash Flow + Partner Profile tabs) ──
_cf_source = st.session_state.get("cf_text", DEFAULT_CASHFLOW)
_cf_data   = parse_cashflow(_cf_source)
for _sci in nodes:
    if _sci not in _cf_data:
        _cf_data[_sci] = {"revenue": 0, "to_partners": 0, "to_staff": 0, "to_charges": 0}

sci_cf = {}
for _sci in nodes:
    _cfg  = _cf_data.get(_sci, {})
    _rev  = _cfg.get("revenue",     0)
    _tp   = _cfg.get("to_partners", 0)
    _ts   = _cfg.get("to_staff",    0)
    _tc   = _cfg.get("to_charges",  0)
    _ret  = max(_rev - _tp - _ts - _tc, 0)
    sci_cf[_sci] = {
        "revenue":      _rev,  "to_partners":  _tp,
        "to_staff":     _ts,   "to_charges":   _tc,
        "retained":     _ret,
        "partners_pct": _tp / _rev if _rev > 0 else 0,
        "staff_pct":    _ts / _rev if _rev > 0 else 0,
        "charges_pct":  _tc / _rev if _rev > 0 else 0,
        "retained_pct": _ret / _rev if _rev > 0 else 0,
    }

pool_vec = np.array([sci_cf[_sci]["to_partners"] for _sci in nodes])
try:
    inv_ImWT = np.linalg.inv(np.eye(len(nodes)) - W.T)
except np.linalg.LinAlgError:
    inv_ImWT = np.eye(len(nodes))

person_direct_cf   = P_direct @ pool_vec
person_total_cf    = P_direct @ (inv_ImWT @ pool_vec)
person_indirect_cf = person_total_cf - person_direct_cf
person_sci_cf_matrix = (P_direct @ inv_ImWT) * pool_vec[np.newaxis, :]

# ── SCI Equity Tab ────────────────────────────────────────────────────────────
with tab_results:
    total_direct = sum(dir_assets.values())
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class='metric-card'><div class='label'>Total Real Assets (Group)</div>
            <div class='value'>{total_direct:,.0f} €</div>
            <div class='sub'>Each euro counted once — true consolidated value</div></div>""", unsafe_allow_html=True)
    with k2:
        top_node = nodes[int(np.argmax(equity_vec))]
        st.markdown(f"""<div class='metric-card'><div class='label'>Largest SCI</div>
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
    ⓘ <b>No double-counting:</b> each SCI's <b>Total Equity</b> = its own direct assets + its proportional share
    of subsidiaries' equity, solved simultaneously as a linear system (I−W)·equity = assets. 
    The group total shown above is the sum of direct assets only — the single correct consolidated figure.
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">SCI Equity Breakdown</div>', unsafe_allow_html=True)

    rows = []
    for node in nodes:
        i = idx[node]
        da = dir_assets.get(node, 0)
        eq = equity_vec[i]
        indirect = max(eq - da, 0)
        owners = [(nodes[j], W[j,i]*100) for j in range(len(nodes)) if W[j,i] > 0]
        owned  = [(nodes[j], W[i,j]*100) for j in range(len(nodes)) if W[i,j] > 0]
        shares = sci_shares.get(node, {})
        person_members = {m: p for m,p in shares.items() if m not in set(nodes)}
        rows.append({
            "SCI": node,
            "Direct Assets (€)": da,
            "Subsidiary Equity (€)": indirect,
            "Total Equity (€)": eq,
            "Human Partners": len(person_members),
            "Owned by SCIs": ", ".join(f"{o} ({p:.2f}%)" for o,p in owners) if owners else "—",
            "Owns SCIs": ", ".join(f"{o} ({p:.2f}%)" for o,p in owned) if owned else "—",
        })
    df = pd.DataFrame(rows).sort_values("Total Equity (€)", ascending=False).reset_index(drop=True)
    styled = (df.style
              .format({"Direct Assets (€)":"{:,.0f}","Subsidiary Equity (€)":"{:,.0f}","Total Equity (€)":"{:,.0f}"})
              .background_gradient(subset=["Total Equity (€)"], cmap="Blues")
              .background_gradient(subset=["Direct Assets (€)"], cmap="Greens"))
    st.dataframe(styled, use_container_width=True, height=320)

    with st.expander("🔍 Effective SCI→SCI Ownership Matrix (direct + indirect %)"):
        st.caption("E[row, col] = total effective % that ROW has in COL through all chains")
        df_E = pd.DataFrame(E*100, index=nodes, columns=nodes)
        st.dataframe(df_E.style.format("{:.3f}%").background_gradient(cmap="Blues", vmin=0, vmax=50), use_container_width=True)

    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Direct Assets", x=df["SCI"], y=df["Direct Assets (€)"],
                             marker_color="#238636", marker_line_color="#2EA043", marker_line_width=1))
        fig.add_trace(go.Bar(name="Subsidiary Equity", x=df["SCI"], y=df["Subsidiary Equity (€)"],
                             marker_color="#1F6FEB", marker_line_color="#388BFD", marker_line_width=1))
        fig.update_layout(barmode="stack", plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                          font_color="#C9D1D9", font_family="Inter",
                          legend=dict(orientation="h", y=1.08, x=0),
                          xaxis=dict(gridcolor="#21262D"), yaxis=dict(gridcolor="#21262D", title="Equity (€)"),
                          title=dict(text="SCI Equity Composition", font_size=14), margin=dict(t=60,b=40,l=60,r=20))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        pass

# ── Partners Tab ──────────────────────────────────────────────────────────────
with tab_partners:
    st.markdown("""<div class='info-box'>
    ⓘ <b>How partner wealth is computed — no double-counting:</b><br/>
    Each person holds a direct % in one or more SCIs. Each SCI's <i>equity</i> already encodes
    all subsidiary chains. So <b>wealth = Σ (direct % in SCI_k) × equity(SCI_k)</b>.
    Because the equity formula absorbs all loops via matrix inversion, multiplying once by
    direct personal stakes produces the true consolidated wealth with no duplication.
    </div>""", unsafe_allow_html=True)

    total_person_wealth = person_wealth.sum()
    total_direct = sum(dir_assets.values())
    rounding_gap = abs(total_direct - total_person_wealth)

    kp1, kp2, kp3, kp4 = st.columns(4)
    with kp1:
        st.markdown(f"""<div class='metric-card'><div class='label'>Total Partner Wealth</div>
            <div class='value'>{total_person_wealth:,.0f} €</div>
            <div class='sub'>Sum across all {len(all_persons)} partners</div></div>""", unsafe_allow_html=True)
    with kp2:
        st.markdown(f"""<div class='metric-card'><div class='label'>Real Group Assets</div>
            <div class='value'>{total_direct:,.0f} €</div>
            <div class='sub'>Expected total (no double-counting)</div></div>""", unsafe_allow_html=True)
    with kp3:
        st.markdown(f"""<div class='metric-card'><div class='label'>Reconciliation Gap</div>
            <div class='value' style='color:{"#3FB950" if rounding_gap < 100 else "#F85149"}'>{rounding_gap:,.2f} €</div>
            <div class='sub'>{"✓ Rounding only" if rounding_gap < 100 else "⚠ Check partner weights"}</div></div>""",
            unsafe_allow_html=True)
    with kp4:
        richest = all_persons[int(np.argmax(person_wealth))]
        st.markdown(f"""<div class='metric-card'><div class='label'>Largest Stakeholder</div>
            <div class='value' style='font-size:1.1rem'>{richest}</div>
            <div class='sub'>{person_wealth[np.argmax(person_wealth)]:,.0f} €</div></div>""", unsafe_allow_html=True)

    # ── View selector
    view_mode = st.radio("View", ["Cards", "Table", "By SCI"], horizontal=True, label_visibility="collapsed")

    sorted_persons = sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]])
    max_wealth = max(person_wealth) if len(person_wealth) > 0 else 1

    if view_mode == "Cards":
        st.markdown('<div class="section-header">Partner Wealth Overview</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for rank, person in enumerate(sorted_persons):
            pw = person_wealth[P_idx[person]]
            bar_pct = int(pw / max_wealth * 100)
            sci_holdings = person_sci_direct.get(person, {})
            badges = "".join(f"<span class='badge badge-blue'>{sci} {p*100:.1f}%</span>"
                             for sci, p in sorted(sci_holdings.items(), key=lambda x: -x[1]))
            col = cols[rank % 3]
            with col:
                st.markdown(f"""
                <div class='person-card'>
                  <div style='display:flex;justify-content:space-between;align-items:baseline'>
                    <div class='name'>#{rank+1} {person}</div>
                    <div class='wealth'>{pw:,.0f} €</div>
                  </div>
                  <div class='bar-bg'><div class='bar-fg' style='width:{bar_pct}%'></div></div>
                  <div style='margin-top:.4rem'>{badges}</div>
                </div>""", unsafe_allow_html=True)

    elif view_mode == "Table":
        st.markdown('<div class="section-header">Partner Wealth Table</div>', unsafe_allow_html=True)
        table_rows = []
        for person in sorted_persons:
            pw = person_wealth[P_idx[person]]
            sci_holdings = person_sci_direct.get(person, {})
            holdings_str = ", ".join(f"{s} ({p*100:.2f}%)" for s,p in sorted(sci_holdings.items(), key=lambda x:-x[1]))
            # Effective % in each SCI (through chains)
            eff_row = {f"Eff. {nd}": P_eff[P_idx[person], idx[nd]]*100 for nd in nodes}
            row = {"Partner": person, "Total Wealth (€)": pw,
                   "% of Group": pw/total_direct*100, "Direct Holdings": holdings_str}
            row.update(eff_row)
            table_rows.append(row)
        df_p = pd.DataFrame(table_rows)
        fmt = {"Total Wealth (€)": "{:,.0f}", "% of Group": "{:.2f}%"}
        fmt.update({f"Eff. {nd}": "{:.3f}%" for nd in nodes})
        styled_p = df_p.style.format(fmt).background_gradient(subset=["Total Wealth (€)"], cmap="Greens")
        st.dataframe(styled_p, use_container_width=True, height=560)

    else:  # By SCI
        st.markdown('<div class="section-header">Partner Stakes by SCI</div>', unsafe_allow_html=True)
        sci_select = st.selectbox("Select SCI", nodes, label_visibility="collapsed")
        if sci_select in sci_shares:
            shares = sci_shares[sci_select]
            eq_sci = equity_vec[idx[sci_select]]
            da_sci = dir_assets.get(sci_select, 0)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class='metric-card'><div class='label'>SCI Total Equity</div>
                    <div class='value'>{eq_sci:,.0f} €</div>
                    <div class='sub'>Direct: {da_sci:,.0f} € + subsidiaries</div></div>""", unsafe_allow_html=True)
            with c2:
                n_persons_here = sum(1 for m in shares if m not in set(nodes))
                n_scis_here = sum(1 for m in shares if m in set(nodes))
                st.markdown(f"""<div class='metric-card'><div class='label'>Composition</div>
                    <div class='value'>{n_persons_here + n_scis_here}</div>
                    <div class='sub'>{n_persons_here} persons · {n_scis_here} SCI members</div></div>""", unsafe_allow_html=True)
            sci_rows = []
            for member, pct in sorted(shares.items(), key=lambda x: -x[1]):
                member_type = "SCI" if member in set(nodes) else "Person"
                money_amount = pct * eq_sci
                if member in P_idx:
                    total_w = person_wealth[P_idx[member]]
                elif member in idx:
                    total_w = equity_vec[idx[member]]
                else:
                    total_w = 0
                sci_rows.append({
                    "Member": member, "Type": member_type,
                    "Direct %": pct * 100,
                    "Share of SCI Equity (€)": money_amount,
                    "Member Total Wealth (€)": total_w,
                })
            df_sci = pd.DataFrame(sci_rows)
            styled_sci = (df_sci.style
                .format({"Direct %": "{:.3f}%", "Share of SCI Equity (€)": "{:,.0f}", "Member Total Wealth (€)": "{:,.0f}"})
                .background_gradient(subset=["Direct %"], cmap="Blues")
                .background_gradient(subset=["Share of SCI Equity (€)"], cmap="Greens"))
            st.dataframe(styled_sci, use_container_width=True)

            # Bar chart
            try:
                import plotly.graph_objects as go
                persons_m = [m for m in sorted(shares, key=lambda x: -shares[x]) if m not in set(nodes)]
                scis_m    = [m for m in sorted(shares, key=lambda x: -shares[x]) if m in set(nodes)]
                all_m = persons_m + scis_m
                colors_m = ["#3FB950"]*len(persons_m) + ["#388BFD"]*len(scis_m)
                vals = [shares[m]*eq_sci for m in all_m]
                fig2 = go.Figure(go.Bar(x=all_m, y=vals, marker_color=colors_m))
                fig2.update_layout(plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                                   yaxis_title="Share of equity (€)", margin=dict(t=20,b=40,l=60,r=20),
                                   title=dict(text=f"Partner shares in {sci_select}", font_size=13))
                st.plotly_chart(fig2, use_container_width=True)
            except ImportError:
                pass


# ── Cash Flow Tab ─────────────────────────────────────────────────────────────
with tab_cashflow:

    st.markdown("""<div class='info-box'>
    ⓘ Each SCI generates monthly revenue split into fixed € amounts: <b>partners</b> (distributed by ownership %),
    <b>staff</b> (salaries/payroll), <b>charges</b> (operating costs), and <b>retained cash</b> (remainder).
    Partner distributions cascade through SCI chains — an SCI receiving a distribution then
    passes its share on to <em>its</em> partners. Both direct and effective (consolidated) views
    are shown side by side.
    </div>""", unsafe_allow_html=True)

    # ── Cash flow input ────────────────────────────────────────────────────────
    with st.expander("⚙️ Configure monthly revenue & split % per SCI", expanded=False):
        cf_col1, cf_col2 = st.columns(2)
        with cf_col1:
            cf_text = st.text_area("Cash flow config", value=DEFAULT_CASHFLOW,
                                   height=420, label_visibility="collapsed")
        with cf_col2:
            st.caption("""**Format per SCI block:**
```
SCI NAME:
  revenue  : 25000   ← total monthly revenue €
  partners : 12500   ← fixed € paid out to partners
  staff    : 5000    ← fixed € for salaries / payroll
  charges  : 3750    ← fixed € for operating costs
```
Retained cash = revenue − partners − staff − charges.""")
        if st.button("💾 Apply cash flow config"):
            st.session_state["cf_text"] = cf_text
            st.success("Cash flow config updated.")

    # sci_cf, pool_vec, person_*_cf computed at module scope above
    # ── KPI row ────────────────────────────────────────────────────────────────
    total_rev   = sum(v["revenue"]     for v in sci_cf.values())
    total_to_p  = sum(v["to_partners"] for v in sci_cf.values())
    total_staff = sum(v["to_staff"]    for v in sci_cf.values())
    total_charg = sum(v["to_charges"]  for v in sci_cf.values())
    total_ret   = sum(v["retained"]    for v in sci_cf.values())

    k1, k2, k3, k4, k5 = st.columns(5)
    for col, label, val, color, sub in [
        (k1, "Total Monthly Revenue",  total_rev,   "#58A6FF", f"{total_rev*12:,.0f} €/yr"),
        (k2, "→ Partners (pool)",      total_to_p,  "#3FB950", f"{total_to_p*12:,.0f} €/yr"),
        (k3, "→ Staff",                total_staff, "#E3B341", f"{total_staff*12:,.0f} €/yr"),
        (k4, "→ Charges",              total_charg, "#F85149", f"{total_charg*12:,.0f} €/yr"),
        (k5, "→ Retained",             total_ret,   "#8B949E", f"{total_ret*12:,.0f} €/yr"),
    ]:
        with col:
            col.markdown(f"""<div class='metric-card'>
                <div class='label'>{label}</div>
                <div class='value' style='color:{color}'>{val:,.0f} €</div>
                <div class='sub'>{sub}</div></div>""", unsafe_allow_html=True)

    # ── SCI cash flow breakdown table ─────────────────────────────────────────
    st.markdown('<div class="section-header">Monthly Cash Flow by SCI</div>', unsafe_allow_html=True)
    try:
        import plotly.graph_objects as go
        sci_names_cf = list(nodes)
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(name="→ Partners", x=sci_names_cf,
                                y=[sci_cf[s]["to_partners"] for s in sci_names_cf],
                                marker_color="#3FB950"))
        fig_cf.add_trace(go.Bar(name="→ Staff",    x=sci_names_cf,
                                y=[sci_cf[s]["to_staff"]    for s in sci_names_cf],
                                marker_color="#E3B341"))
        fig_cf.add_trace(go.Bar(name="→ Charges",  x=sci_names_cf,
                                y=[sci_cf[s]["to_charges"]  for s in sci_names_cf],
                                marker_color="#F85149"))
        fig_cf.add_trace(go.Bar(name="Retained",   x=sci_names_cf,
                                y=[sci_cf[s]["retained"]    for s in sci_names_cf],
                                marker_color="#30363D"))
        fig_cf.update_layout(barmode="stack", plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                             font_color="#C9D1D9", font_family="Inter",
                             legend=dict(orientation="h", y=1.08, x=0),
                             yaxis=dict(gridcolor="#21262D", title="€ / month"),
                             xaxis=dict(gridcolor="#21262D"),
                             margin=dict(t=50,b=40,l=60,r=20))
        st.plotly_chart(fig_cf, use_container_width=True)
    except ImportError:
        pass

    sci_rows_cf = []
    for sci in nodes:
        cf = sci_cf[sci]
        sci_rows_cf.append({
            "SCI": sci,
            "Monthly Revenue (€)": cf["revenue"],
            "Partners (€/mo)":  cf["to_partners"],
            "Staff (€/mo)":     cf["to_staff"],
            "Charges (€/mo)":   cf["to_charges"],
            "Retained (€/mo)":  cf["retained"],
            "Annual Revenue (€)": cf["revenue"] * 12,
        })
    df_scicf = pd.DataFrame(sci_rows_cf)
    st.dataframe(
        df_scicf.style.format({
            "Monthly Revenue (€)":  "{:,.0f}",
            "Partners (€/mo)":      "{:,.0f}",
            "Staff (€/mo)":         "{:,.0f}",
            "Charges (€/mo)":       "{:,.0f}",
            "Retained (€/mo)":      "{:,.0f}",
            "Annual Revenue (€)":   "{:,.0f}",
        }).background_gradient(subset=["Monthly Revenue (€)"], cmap="Blues")
          .background_gradient(subset=["Partners (€/mo)"],     cmap="Greens"),
        use_container_width=True, hide_index=True
    )

    # ── Partner distribution ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Partner Cash Flow Distribution</div>', unsafe_allow_html=True)
    st.caption("Each SCI's partner pool is split by ownership %. SCIs that receive a distribution cascade it to their own partners.")
    # pool_vec, person_direct_cf, person_total_cf, person_indirect_cf, person_sci_cf_matrix
    # are all computed at module scope above.

    # ── View toggle ────────────────────────────────────────────────────────────
    cf_view = st.radio("View", ["Summary cards", "Full table", "Annual projection", "By SCI"], horizontal=True)

    sorted_persons_cf = sorted(all_persons, key=lambda p: -person_total_cf[P_idx[p]])

    if cf_view == "Summary cards":
        max_pcf = max(person_total_cf) if len(person_total_cf) > 0 else 1
        cols3 = st.columns(3)
        for rank, person in enumerate(sorted_persons_cf):
            pi = P_idx[person]
            total_m  = person_total_cf[pi]
            direct_m = person_direct_cf[pi]
            indir_m  = person_indirect_cf[pi]
            bar_pct  = int(total_m / max_pcf * 100)
            sci_breakdown = "".join(
                f"<span class='badge badge-blue'>{nodes[j]} {person_sci_cf_matrix[pi,j]:,.0f}€</span>"
                for j in range(len(nodes)) if person_sci_cf_matrix[pi,j] > 0.5
            )
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
                  </div>
                  <div>{sci_breakdown}</div>
                </div>""", unsafe_allow_html=True)

    elif cf_view == "Full table":
        rows_cf = []
        for person in sorted_persons_cf:
            pi = P_idx[person]
            row = {
                "Partner":              person,
                "Direct monthly (€)":   person_direct_cf[pi],
                "Cascade monthly (€)":  person_indirect_cf[pi],
                "Total monthly (€)":    person_total_cf[pi],
                "Total annual (€)":     person_total_cf[pi] * 12,
                "% of total pool":      person_total_cf[pi] / max(total_to_p, 1) * 100,
            }
            for j, sci in enumerate(nodes):
                row[f"{sci} (€/mo)"] = person_sci_cf_matrix[pi, j]
            rows_cf.append(row)
        df_cf = pd.DataFrame(rows_cf)
        fmt_cf = {
            "Direct monthly (€)":  "{:,.0f}",
            "Cascade monthly (€)": "{:,.0f}",
            "Total monthly (€)":   "{:,.0f}",
            "Total annual (€)":    "{:,.0f}",
            "% of total pool":     "{:.2f}%",
        }
        fmt_cf.update({f"{s} (€/mo)": "{:,.0f}" for s in nodes})
        st.dataframe(
            df_cf.style.format(fmt_cf)
                       .background_gradient(subset=["Total monthly (€)"], cmap="Greens")
                       .background_gradient(subset=["Total annual (€)"],  cmap="Blues"),
            use_container_width=True, height=480
        )

    elif cf_view == "Annual projection":
        try:
            import plotly.graph_objects as go
            months = [f"M{i}" for i in range(1, 13)]
            # Top 8 by income for readability
            top_persons = sorted_persons_cf[:8]
            fig_ann = go.Figure()
            for person in top_persons:
                pi = P_idx[person]
                monthly = person_total_cf[pi]
                cumulative = [monthly * m for m in range(1, 13)]
                fig_ann.add_trace(go.Scatter(
                    x=months, y=cumulative, mode="lines+markers",
                    name=person, line=dict(width=2),
                ))
            fig_ann.update_layout(
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                font_family="Inter",
                title=dict(text="Cumulative partner cash flow — top 8 partners", font_size=13),
                xaxis=dict(gridcolor="#21262D", title="Month"),
                yaxis=dict(gridcolor="#21262D", title="Cumulative cash received (€)"),
                legend=dict(orientation="v", x=1.01, y=1),
                margin=dict(t=50, b=50, l=70, r=140),
            )
            st.plotly_chart(fig_ann, use_container_width=True)

            # Annual totals bar
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=[p for p in sorted_persons_cf],
                y=[person_direct_cf[P_idx[p]]*12   for p in sorted_persons_cf],
                name="Direct (annual)", marker_color="#3FB950",
            ))
            fig_bar.add_trace(go.Bar(
                x=[p for p in sorted_persons_cf],
                y=[person_indirect_cf[P_idx[p]]*12 for p in sorted_persons_cf],
                name="Cascade (annual)", marker_color="#E3B341",
            ))
            fig_bar.update_layout(
                barmode="stack", plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                font_color="#C9D1D9", font_family="Inter",
                title=dict(text="Annual cash flow per partner — direct vs cascade", font_size=13),
                xaxis=dict(gridcolor="#21262D", tickangle=-35),
                yaxis=dict(gridcolor="#21262D", title="€ / year"),
                legend=dict(orientation="h", y=1.06),
                margin=dict(t=50, b=100, l=70, r=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        except ImportError:
            st.info("Install plotly for charts.")

    else:  # By SCI
        sci_cf_select = st.selectbox("Select SCI", nodes, key="cf_sci_select", label_visibility="collapsed")
        j_sci = idx[sci_cf_select]
        pool_this = sci_cf[sci_cf_select]["to_partners"]

        ca, cb, cc = st.columns(3)
        with ca:
            ca.markdown(f"""<div class='metric-card'><div class='label'>Monthly Revenue</div>
                <div class='value'>{sci_cf[sci_cf_select]['revenue']:,.0f} €</div>
                <div class='sub'>Annual: {sci_cf[sci_cf_select]['revenue']*12:,.0f} €</div></div>""",
                unsafe_allow_html=True)
        with cb:
            cb.markdown(f"""<div class='metric-card'><div class='label'>Partner Pool / month</div>
                <div class='value' style='color:#3FB950'>{pool_this:,.0f} €</div>
                <div class='sub'>{sci_cf[sci_cf_select]['partners_pct']*100:.0f}% of revenue · {pool_this*12:,.0f} €/yr</div></div>""",
                unsafe_allow_html=True)
        with cc:
            staff_v  = sci_cf[sci_cf_select]['to_staff']
            charge_v = sci_cf[sci_cf_select]['to_charges']
            cc.markdown(f"""<div class='metric-card'><div class='label'>Staff + Charges / month</div>
                <div class='value' style='color:#E3B341'>{staff_v+charge_v:,.0f} €</div>
                <div class='sub'>Staff {staff_v:,.0f}€ · Charges {charge_v:,.0f}€</div></div>""",
                unsafe_allow_html=True)

        # Direct members of this SCI and their cash share
        shares_this = sci_shares.get(sci_cf_select, {})
        rows_bysci = []
        for member, pct in sorted(shares_this.items(), key=lambda x: -x[1]):
            mtype = "SCI" if member in set(nodes) else "Person"
            cash_direct = pct * pool_this
            # If person: also show what they receive total (cascade from this SCI + upstreams)
            if member in P_idx:
                cash_total = person_total_cf[P_idx[member]]
                pct_of_total = cash_total / max(person_total_cf.max(), 1) * 100
            elif member in idx:
                # SCI member gets cash, then redistributes — show what it passes on
                cash_total = cash_direct  # first-level only
                pct_of_total = 0
            else:
                cash_total = cash_direct
                pct_of_total = 0
            rows_bysci.append({
                "Member": member, "Type": mtype,
                "Direct %": pct * 100,
                "Direct cash /mo (€)": cash_direct,
                "Direct cash /yr (€)": cash_direct * 12,
                "Member total /mo (€)": cash_total if mtype == "Person" else cash_direct,
            })
        df_bysci = pd.DataFrame(rows_bysci)
        st.dataframe(
            df_bysci.style.format({
                "Direct %":             "{:.3f}%",
                "Direct cash /mo (€)":  "{:,.0f}",
                "Direct cash /yr (€)":  "{:,.0f}",
                "Member total /mo (€)": "{:,.0f}",
            }).background_gradient(subset=["Direct cash /mo (€)"], cmap="Greens"),
            use_container_width=True, hide_index=True
        )
        try:
            import plotly.graph_objects as go
            persons_bysci = [r["Member"] for r in rows_bysci if r["Type"]=="Person"]
            scis_bysci    = [r["Member"] for r in rows_bysci if r["Type"]=="SCI"]
            all_m_bysci   = persons_bysci + scis_bysci
            vals_bysci    = [shares_this[m]*pool_this for m in all_m_bysci]
            colors_bysci  = ["#3FB950"]*len(persons_bysci) + ["#388BFD"]*len(scis_bysci)
            fig_bysci = go.Figure(go.Bar(x=all_m_bysci, y=vals_bysci, marker_color=colors_bysci))
            fig_bysci.update_layout(
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                yaxis_title="€ / month", xaxis=dict(tickangle=-30),
                title=dict(text=f"Cash distribution from {sci_cf_select} partner pool", font_size=13),
                margin=dict(t=40,b=80,l=60,r=20))
            st.plotly_chart(fig_bysci, use_container_width=True)
        except ImportError:
            pass

# ── Partner Profile Tab ───────────────────────────────────────────────────────
with tab_profile:

    # ── Person selector ────────────────────────────────────────────────────────
    sel_col, spacer = st.columns([2, 4])
    with sel_col:
        selected_person = st.selectbox(
            "Select a partner",
            options=sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]]),
            format_func=lambda p: f"{p}  —  {person_wealth[P_idx[p]]:,.0f} €",
            label_visibility="collapsed",
        )

    pi       = P_idx[selected_person]
    pw       = person_wealth[pi]
    dir_cf   = person_direct_cf[pi]
    casc_cf  = person_indirect_cf[pi]
    tot_cf   = person_total_cf[pi]

    # SCIs this person is directly in
    direct_scis = {sci: pct for sci, pct in
                   person_sci_direct.get(selected_person, {}).items()}

    # Effective stakes (all chains)
    eff_stakes = {nodes[j]: P_eff[pi, idx[nodes[j]]]
                  for j in range(len(nodes)) if P_eff[pi, idx[nodes[j]]] > 1e-7}

    # Cash received per SCI — effective (direct + cascade) from module-scope person_sci_cf_matrix
    cf_per_sci = {nodes[j]: person_sci_cf_matrix[pi, j] for j in range(len(nodes))}

    # ── KPI strip ──────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "Total Wealth",         pw,          "#58A6FF", f"{pw*12/1e6:.3f} M€ equiv."),
        (k2, "Monthly Cash (direct)", dir_cf,      "#3FB950", f"{dir_cf*12:,.0f} €/yr"),
        (k3, "Monthly Cash (cascade)",casc_cf,     "#E3B341", f"{casc_cf*12:,.0f} €/yr"),
        (k4, "Total Monthly Cash",    tot_cf,      "#79C0FF", f"{tot_cf*12:,.0f} €/yr"),
        (k5, "SCIs (direct)",         len(direct_scis), "#A371F7", f"{len(eff_stakes)} incl. indirect"),
    ]
    for col, label, val, color, sub in kpis:
        fmt = f"{val:,.0f} €" if isinstance(val, float) else str(val)
        col.markdown(f"""<div class='metric-card'>
            <div class='label'>{label}</div>
            <div class='value' style='color:{color}'>{fmt}</div>
            <div class='sub'>{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    left, right = st.columns([1, 1], gap="large")

    # ── LEFT: SCI membership table ─────────────────────────────────────────────
    with left:
        st.markdown('<div class="section-header">SCI Memberships</div>', unsafe_allow_html=True)

        membership_rows = []
        for sci in nodes:
            d_pct  = direct_scis.get(sci, 0)
            e_pct  = eff_stakes.get(sci, 0)
            is_dir = d_pct > 1e-9
            sci_eq = equity_vec[idx[sci]]
            wealth_share = e_pct * equity_vec[idx[sci]]   # effective claim on this SCI's equity
            cf_share     = cf_per_sci.get(sci, 0)
            if e_pct < 1e-7: continue
            membership_rows.append({
                "SCI":            sci,
                "Type":           "Direct" if is_dir else "Indirect",
                "Direct %":       d_pct * 100 if is_dir else 0,
                "Effective %":    e_pct * 100,
                "SCI Equity (€)": sci_eq,
                "My Claim (€)":   wealth_share,
                "CF share (€/mo)":cf_share,
            })

        df_mem = pd.DataFrame(membership_rows).sort_values("Effective %", ascending=False)

        def highlight_type(row):
            color = "background-color:#0F2918" if row["Type"] == "Direct" else "background-color:#1A1600"
            return [color] * len(row)

        st.dataframe(
            df_mem.style
                  .apply(highlight_type, axis=1)
                  .format({
                      "Direct %":        "{:.3f}%",
                      "Effective %":     "{:.4f}%",
                      "SCI Equity (€)":  "{:,.0f}",
                      "My Claim (€)":    "{:,.0f}",
                      "CF share (€/mo)": "{:,.0f}",
                  }),
            use_container_width=True, hide_index=True, height=310
        )

        # Cash flow breakdown donut
        try:
            import plotly.graph_objects as go
            cf_labels = [s for s in nodes if cf_per_sci.get(s, 0) > 0.5]
            cf_vals   = [cf_per_sci[s] for s in cf_labels]
            if cf_labels:
                fig_donut = go.Figure(go.Pie(
                    labels=cf_labels, values=cf_vals,
                    hole=0.55,
                    textinfo="label+percent",
                    textfont_size=11,
                    marker=dict(colors=["#1F6FEB","#3FB950","#E3B341","#F85149","#A371F7","#58A6FF","#DB6D28"]),
                ))
                fig_donut.update_layout(
                    plot_bgcolor="#0D1117", paper_bgcolor="#0D1117", font_color="#C9D1D9",
                    showlegend=False,
                    title=dict(text="Monthly cash flow by SCI (direct)", font_size=12, x=0.5),
                    annotations=[dict(text=f"{tot_cf:,.0f}€<br>/mo", x=0.5, y=0.5,
                                      font_size=13, showarrow=False, font_color="#C9D1D9")],
                    margin=dict(t=50, b=10, l=10, r=10), height=280,
                )
                st.plotly_chart(fig_donut, use_container_width=True)
        except ImportError:
            pass

    # ── RIGHT: Wealth evolution chart ──────────────────────────────────────────
    with right:
        st.markdown('<div class="section-header">Wealth & Cash Flow Evolution</div>', unsafe_allow_html=True)

        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Wealth evolution: simulate over 10 years monthly
            # Assumptions: equity stays fixed (static model), cash accumulates,
            # user can toggle growth rate
            growth_rate = st.slider(
                "Annual equity growth rate (%)",
                min_value=0.0, max_value=15.0, value=3.0, step=0.5,
                help="Hypothetical annual appreciation of underlying SCI assets"
            )
            months_horizon = st.select_slider(
                "Projection horizon",
                options=[12, 24, 36, 60, 120],
                value=60,
                format_func=lambda x: f"{x//12} yr" + ("s" if x//12 > 1 else ""),
            )

            monthly_rate = (1 + growth_rate / 100) ** (1/12) - 1
            months = list(range(months_horizon + 1))

            # Equity grows with compounding
            equity_curve = [pw * (1 + monthly_rate) ** m for m in months]
            # Cash accumulates linearly (constant monthly income)
            cash_curve   = [tot_cf * m for m in months]
            # Total = equity + accumulated cash
            total_curve  = [e + c for e, c in zip(equity_curve, cash_curve)]

            month_labels = []
            for m in months:
                yr  = m // 12
                mo  = m % 12
                month_labels.append(f"Y{yr}" if mo == 0 else ("" if mo != 6 else f"Y{yr}M6"))

            fig_evo = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                row_heights=[0.65, 0.35],
                vertical_spacing=0.06,
            )

            # ── Top: wealth stack ──
            fig_evo.add_trace(go.Scatter(
                x=months, y=equity_curve,
                name="SCI Equity (growing)",
                mode="lines", fill="tozeroy",
                line=dict(color="#1F6FEB", width=2),
                fillcolor="rgba(31,111,235,0.15)",
            ), row=1, col=1)

            fig_evo.add_trace(go.Scatter(
                x=months, y=total_curve,
                name="+ Accumulated cash",
                mode="lines", fill="tonexty",
                line=dict(color="#3FB950", width=2),
                fillcolor="rgba(63,185,80,0.12)",
            ), row=1, col=1)

            # Milestone markers every 12 months
            for m in range(0, months_horizon+1, 12):
                fig_evo.add_vline(x=m, line_dash="dot",
                                  line_color="#30363D", line_width=1, row=1, col=1)

            # ── Bottom: monthly cash bar ──
            fig_evo.add_trace(go.Bar(
                x=months, y=[tot_cf] * len(months),
                name="Monthly cash",
                marker_color="#E3B341", opacity=0.7,
                showlegend=True,
            ), row=2, col=1)

            fig_evo.update_layout(
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                font_color="#C9D1D9", font_family="Inter",
                legend=dict(orientation="h", y=1.04, x=0, font_size=11),
                margin=dict(t=30, b=40, l=65, r=20),
                height=430,
            )
            fig_evo.update_xaxes(
                tickvals=[m for m in months if m % 12 == 0],
                ticktext=[f"Y{m//12}" for m in months if m % 12 == 0],
                gridcolor="#21262D", row=1, col=1,
            )
            fig_evo.update_xaxes(gridcolor="#21262D", row=2, col=1)
            fig_evo.update_yaxes(gridcolor="#21262D", tickformat=",.0f",
                                  title_text="€", row=1, col=1)
            fig_evo.update_yaxes(gridcolor="#21262D", tickformat=",.0f",
                                  title_text="€/mo", row=2, col=1)

            st.plotly_chart(fig_evo, use_container_width=True)

            # ── Milestone table ────────────────────────────────────────────────
            milestone_rows = []
            for m in range(0, months_horizon+1, 12):
                yr = m // 12
                milestone_rows.append({
                    "Year":                  f"Y{yr}",
                    "SCI Equity (€)":        equity_curve[m],
                    "Accumulated Cash (€)":  cash_curve[m],
                    "Total Wealth (€)":      total_curve[m],
                    "Growth vs today":       f"+{(total_curve[m]/pw - 1)*100:.1f}%",
                })
            df_ms = pd.DataFrame(milestone_rows)
            st.dataframe(
                df_ms.style
                     .format({
                         "SCI Equity (€)":       "{:,.0f}",
                         "Accumulated Cash (€)":  "{:,.0f}",
                         "Total Wealth (€)":      "{:,.0f}",
                     })
                     .background_gradient(subset=["Total Wealth (€)"], cmap="Blues"),
                use_container_width=True, hide_index=True, height=230,
            )

        except ImportError:
            st.info("Install plotly for wealth evolution charts.")

# ── Graph Tab ─────────────────────────────────────────────────────────────────
with tab_graph:
    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([1.3, 1.3, 3])
    with ctrl1:
        show_partners = st.toggle("👥 Show partners", value=True,
                                   help="Display individual partners and their links to each SCI")
    with ctrl2:
        show_effective = st.toggle("📈 Show effective %", value=False,
                                    help="Show effective (direct + indirect) ownership % instead of direct-only, "
                                         "and reveal indirect-only links as dashed edges")
    with ctrl3:
        if show_effective:
            st.caption("Solid edges = direct stake · dashed edges = indirect-only relationship · % shown is **effective** (through all chains)")
        else:
            st.caption("Showing **direct** stakes only · toggle 'effective %' to reveal indirect relationships too")

    col_g1, col_g2 = st.columns([4, 1])
    with col_g2:
        st.markdown('<div class="section-header">Legend</div>', unsafe_allow_html=True)
        st.markdown("""<div style='font-size:.8rem;color:#8B949E;line-height:1.9'>
        <span style='color:#58A6FF'>●</span> SCI (size = equity)<br/>
        <span style='color:#E3B341'>●</span> Partner (size = wealth)<br/><br/>
        <span style='color:#3FB950'>—</span> Direct stake<br/>
        <span style='color:#E3B341'>┄</span> Indirect-only (effective view)<br/><br/>
        Edge width ∝ stake %<br/>Hover any node for full breakdown.</div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:1.5rem">SCI Equity</div>', unsafe_allow_html=True)
        for node in nodes:
            eq = equity_vec[idx[node]]
            st.markdown(f"""<div style='display:flex;justify-content:space-between;margin:.3rem 0;font-size:.8rem'>
              <span style='color:#C9D1D9'>{node}</span>
              <span style='color:#58A6FF;font-weight:600'>{eq:,.0f}€</span></div>""", unsafe_allow_html=True)

        if show_partners:
            st.markdown('<div class="section-header" style="margin-top:1.5rem">Top Partners</div>', unsafe_allow_html=True)
            top5 = sorted(all_persons, key=lambda p: -person_wealth[P_idx[p]])[:5]
            for p in top5:
                w = person_wealth[P_idx[p]]
                st.markdown(f"""<div style='display:flex;justify-content:space-between;margin:.3rem 0;font-size:.8rem'>
                  <span style='color:#C9D1D9'>{p}</span>
                  <span style='color:#E3B341;font-weight:600'>{w:,.0f}€</span></div>""", unsafe_allow_html=True)

    with col_g1:
        net = build_pyvis(nodes, edges, equity_vec, dir_assets, sci_shares,
                          show_partners=show_partners, show_effective=show_effective,
                          all_persons=all_persons, P_idx=P_idx, P_eff=P_eff,
                          person_wealth=person_wealth, idx=idx)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
            net.save_graph(f.name)
            html_path = f.name
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        html_content = html_content.replace("<body>", "<body style='background:#0D1117;margin:0;padding:0'>")
        os.unlink(html_path)
        st.components.v1.html(html_content, height=730, scrolling=False)