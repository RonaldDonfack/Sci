import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import json
import re
from pyvis.network import Network
import tempfile
import os

st.set_page_config(
    page_title="Investment Cycle · Equity Calculator",
    page_icon="🏗️",
    layout="wide",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
}

.stApp { background: #0D1117; color: #E6EDF3; }

.block-container { padding-top: 2rem; max-width: 1400px; }

.metric-card {
    background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: border-color .2s;
}
.metric-card:hover { border-color: #58A6FF; }
.metric-card .label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #8B949E;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-bottom: .3rem;
}
.metric-card .value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #58A6FF;
}
.metric-card .sub {
    font-size: 0.78rem;
    color: #6E7681;
    margin-top: .2rem;
}

.section-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #C9D1D9;
    border-left: 3px solid #58A6FF;
    padding-left: .75rem;
    margin: 1.5rem 0 1rem 0;
}

.pill {
    display: inline-block;
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 999px;
    padding: .15rem .65rem;
    font-size: .75rem;
    color: #8B949E;
    margin: .15rem;
}
.pill-blue { border-color: #1F6FEB; color: #58A6FF; background: #0D1F3C; }
.pill-green { border-color: #238636; color: #3FB950; background: #0F2918; }

.stTextArea textarea {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #C9D1D9 !important;
    border-radius: 8px !important;
    font-family: 'Inter', monospace !important;
    font-size: .85rem !important;
}
.stNumberInput input, .stTextInput input {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #C9D1D9 !important;
    border-radius: 8px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #1F6FEB, #388BFD);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: .5rem 1.5rem;
    font-family: 'Space Grotesk', sans-serif;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #388BFD, #58A6FF);
    transform: translateY(-1px);
}

/* table */
.stDataFrame { border-radius: 10px; overflow: hidden; }
thead tr th {
    background: #161B22 !important;
    color: #8B949E !important;
    font-size: .78rem !important;
    letter-spacing: .06em !important;
    text-transform: uppercase !important;
}
tbody tr td { color: #C9D1D9 !important; font-size: .88rem !important; }
tbody tr:nth-child(even) td { background: #161B22 !important; }

.warning-box {
    background: #2D1B00;
    border: 1px solid #BB8009;
    border-radius: 8px;
    padding: .8rem 1rem;
    font-size: .85rem;
    color: #E3B341;
}
</style>
""", unsafe_allow_html=True)

# ── Default data ────────────────────────────────────────────────────────────
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


# ── Parsing ──────────────────────────────────────────────────────────────────
def parse_relations(text):
    """Parse 'A -> B : pct%' lines into list of (from, to, pct)."""
    edges = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(.+?)\s*->\s*(.+?)\s*:\s*([\d.,]+)\s*%?$", line)
        if m:
            src = m.group(1).strip().upper()
            dst = m.group(2).strip().upper()
            pct = float(m.group(3).replace(",", ".")) / 100.0
            edges.append((src, dst, pct))
    return edges


def parse_assets(text):
    """Parse 'A : value' lines into dict."""
    assets = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(.+?)\s*:\s*([\d.,\s]+)$", line)
        if m:
            name = m.group(1).strip().upper()
            val = float(m.group(2).replace(" ", "").replace(",", "."))
            assets[name] = val
    return assets


# ── Equity Calculation (iterative fixed-point) ──────────────────────────────
def compute_equity(edges, direct_assets):
    """
    Each SCI's total equity = its own direct assets
    + sum over all SCIs it (directly OR indirectly) owns of (effective_pct * that_sci_equity).

    We solve via iterative fixed-point (handles circular structures).
    effective_% is the matrix-power expansion of the direct ownership matrix.
    """
    nodes = sorted({n for e in edges for n in (e[0], e[1])} | set(direct_assets.keys()))
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)

    # Direct ownership matrix W[i,j] = direct % that i owns in j
    W = np.zeros((n, n))
    for src, dst, pct in edges:
        W[idx[src], idx[dst]] += pct

    # Effective ownership = (I - W)^-1 * W  but for equity we want:
    # equity_i = assets_i + sum_j W_ij * equity_j
    # => equity = assets + W @ equity
    # => (I - W) equity = assets
    # => equity = (I - W)^-1 @ assets
    A_vec = np.array([direct_assets.get(node, 0.0) for node in nodes])

    try:
        IminusW = np.eye(n) - W
        equity_vec = np.linalg.solve(IminusW, A_vec)
    except np.linalg.LinAlgError:
        # Fallback: iterative
        equity_vec = A_vec.copy()
        for _ in range(1000):
            new_eq = A_vec + W @ equity_vec
            if np.allclose(new_eq, equity_vec, rtol=1e-8):
                break
            equity_vec = new_eq

    # Also compute effective ownership matrix E = (I-W)^-1 - I (indirect+direct)
    try:
        inv = np.linalg.inv(np.eye(n) - W)
        E = inv - np.eye(n)  # i owns E[i,j]*100% of j effectively
    except Exception:
        E = W.copy()

    return nodes, equity_vec, W, E


# ── Graph ────────────────────────────────────────────────────────────────────
def build_pyvis(nodes, edges, equity_vec, direct_assets):
    """Build a pyvis network with Neo4j-inspired styling."""
    net = Network(
        height="620px",
        width="100%",
        bgcolor="#0D1117",
        font_color="#C9D1D9",
        directed=True,
    )
    net.set_options("""
{
  "nodes": {
    "font": { "size": 13, "face": "Inter", "color": "#C9D1D9" },
    "borderWidth": 2,
    "shadow": { "enabled": true, "size": 10, "x": 0, "y": 0, "color": "rgba(88,166,255,0.3)" }
  },
  "edges": {
    "arrows": { "to": { "enabled": true, "scaleFactor": 0.8 } },
    "color": { "color": "#30363D", "hover": "#58A6FF", "highlight": "#388BFD" },
    "font": { "size": 11, "color": "#8B949E", "face": "Inter", "align": "middle" },
    "smooth": { "type": "curvedCW", "roundness": 0.2 },
    "width": 1.5
  },
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based",
    "forceAtlas2Based": {
      "gravitationalConstant": -80,
      "centralGravity": 0.01,
      "springLength": 160,
      "springConstant": 0.08
    },
    "stabilization": { "iterations": 150 }
  },
  "interaction": {
    "hover": true,
    "tooltipDelay": 100,
    "zoomView": true,
    "dragNodes": true
  }
}
""")

    idx_map = {n: i for i, n in enumerate(nodes)}
    max_eq = max(equity_vec) if len(equity_vec) > 0 else 1

    # Color scale based on equity rank
    colors = ["#1C2840", "#1A3560", "#1A4A7A", "#1F6FEB", "#388BFD", "#58A6FF", "#79C0FF"]

    for node in nodes:
        i = idx_map[node]
        eq = equity_vec[i]
        da = direct_assets.get(node, 0)
        ratio = eq / max_eq if max_eq > 0 else 0
        c_idx = min(int(ratio * (len(colors) - 1)), len(colors) - 1)
        color = colors[c_idx]
        size = 20 + ratio * 30

        label = node
        title = (
            f"<div style='font-family:Inter;padding:8px;min-width:180px'>"
            f"<b style='color:#58A6FF'>{node}</b><br/>"
            f"<hr style='border-color:#30363D;margin:4px 0'/>"
            f"<span style='color:#8B949E'>Direct assets</span><br/>"
            f"<b>{da:,.0f} €</b><br/>"
            f"<span style='color:#8B949E'>Total equity (incl. subsidiaries)</span><br/>"
            f"<b style='color:#3FB950'>{eq:,.0f} €</b>"
            f"</div>"
        )

        net.add_node(
            node,
            label=label,
            title=title,
            color={"background": color, "border": "#58A6FF",
                   "highlight": {"background": "#388BFD", "border": "#79C0FF"}},
            size=size,
            font={"size": 12 + int(ratio * 4)},
        )

    for src, dst, pct in edges:
        net.add_edge(
            src, dst,
            label=f"{pct * 100:.2f}%",
            title=f"{src} owns {pct * 100:.2f}% of {dst}",
            width=1 + pct * 4,
        )

    return net


# ── UI ───────────────────────────────────────────────────────────────────────
# Header
st.markdown("""
<div style='display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem'>
  <div style='width:44px;height:44px;background:linear-gradient(135deg,#1F6FEB,#388BFD);
              border-radius:10px;display:flex;align-items:center;justify-content:center;
              font-size:1.4rem'>🏗️</div>
  <div>
    <h1 style='margin:0;font-size:1.6rem;color:#E6EDF3'>Investment Cycle · Equity Calculator</h1>
    <p style='margin:0;color:#8B949E;font-size:.85rem'>
      Model SCI ownership structures — compute direct & indirect equity, visualize relationships
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_input, tab_results, tab_graph = st.tabs(["📋 Data Input", "📊 Equity Results", "🕸️ Relationship Graph"])

with tab_input:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="section-header">Ownership Relations</div>', unsafe_allow_html=True)
        st.caption("Format: `COMPANY A -> COMPANY B : XX%`  (one per line)")
        relations_text = st.text_area(
            "Relations",
            value=DEFAULT_RELATIONS,
            height=380,
            label_visibility="collapsed",
        )

    with col2:
        st.markdown('<div class="section-header">Direct Asset Values (€)</div>', unsafe_allow_html=True)
        st.caption("Format: `COMPANY : value`  (one per line — own net assets before subsidiaries)")
        assets_text = st.text_area(
            "Assets",
            value=DEFAULT_ASSETS,
            height=300,
            label_visibility="collapsed",
        )

        st.markdown('<div class="section-header">Add Single Relation</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            new_src = st.text_input("From", placeholder="LEM IMMO", label_visibility="collapsed")
        with c2:
            new_dst = st.text_input("To", placeholder="LEM INVEST", label_visibility="collapsed")
        with c3:
            new_pct = st.number_input("% stake", min_value=0.0, max_value=100.0, value=10.0, step=0.5,
                                      label_visibility="collapsed")
        with c4:
            if st.button("＋ Add"):
                if new_src and new_dst:
                    addition = f"\n{new_src.upper()} -> {new_dst.upper()} : {new_pct}%"
                    st.session_state["extra_relations"] = st.session_state.get("extra_relations", "") + addition
                    st.success(f"Added: {new_src.upper()} → {new_dst.upper()} @ {new_pct}%")

    # Merge any added relations
    full_relations = relations_text + st.session_state.get("extra_relations", "")

    if st.button("⚙️  Calculate Equity", type="primary"):
        st.session_state["calc_done"] = True
        st.session_state["relations_text"] = full_relations
        st.session_state["assets_text"] = assets_text
        st.success("✅ Calculation complete — see Results and Graph tabs.")


# ── Run calculation on stored state ──────────────────────────────────────────
def run_calc():
    rel_text = st.session_state.get("relations_text", DEFAULT_RELATIONS)
    ast_text = st.session_state.get("assets_text", DEFAULT_ASSETS)
    edges = parse_relations(rel_text)
    direct_assets = parse_assets(ast_text)
    nodes, equity_vec, W, E = compute_equity(edges, direct_assets)
    return nodes, equity_vec, W, E, edges, direct_assets


# Compute eagerly so graph tab always works
if "calc_done" not in st.session_state:
    st.session_state["relations_text"] = DEFAULT_RELATIONS
    st.session_state["assets_text"] = DEFAULT_ASSETS
    st.session_state["calc_done"] = True

nodes, equity_vec, W, E, edges, direct_assets = run_calc()
idx_map = {n: i for i, n in enumerate(nodes)}

# ── Results Tab ──────────────────────────────────────────────────────────────
with tab_results:
    total_direct = sum(direct_assets.values())
    total_equity = sum(equity_vec)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class='metric-card'>
            <div class='label'>Total Direct Assets</div>
            <div class='value'>{total_direct:,.0f} €</div>
            <div class='sub'>Sum of own net assets</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class='metric-card'>
            <div class='label'>Total Equity (Group)</div>
            <div class='value'>{total_equity:,.0f} €</div>
            <div class='sub'>Including subsidiary stakes</div></div>""", unsafe_allow_html=True)
    with k3:
        top_node = nodes[int(np.argmax(equity_vec))]
        st.markdown(f"""<div class='metric-card'>
            <div class='label'>Largest Entity</div>
            <div class='value' style='font-size:1.15rem'>{top_node}</div>
            <div class='sub'>{equity_vec[int(np.argmax(equity_vec))]:,.0f} €</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class='metric-card'>
            <div class='label'>Entities Modelled</div>
            <div class='value'>{len(nodes)}</div>
            <div class='sub'>{len(edges)} ownership links</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Entity Equity Breakdown</div>', unsafe_allow_html=True)

    # Build table
    rows = []
    for node in nodes:
        i = idx_map[node]
        da = direct_assets.get(node, 0)
        eq = equity_vec[i]
        indirect = eq - da
        # Who owns this node and how much (direct)
        owners = [(nodes[j], W[j, i] * 100) for j in range(len(nodes)) if W[j, i] > 0]
        owners_str = ", ".join(f"{o} ({p:.2f}%)" for o, p in owners) if owners else "—"
        # What does this node own directly
        owned = [(nodes[j], W[i, j] * 100) for j in range(len(nodes)) if W[i, j] > 0]
        owned_str = ", ".join(f"{o} ({p:.2f}%)" for o, p in owned) if owned else "—"
        rows.append({
            "Entity": node,
            "Direct Assets (€)": da,
            "Indirect Equity (€)": max(indirect, 0),
            "Total Equity (€)": eq,
            "Owns (direct)": owned_str,
            "Owned by": owners_str,
        })

    df = pd.DataFrame(rows).sort_values("Total Equity (€)", ascending=False).reset_index(drop=True)

    # Style and display
    styled = (
        df.style
        .format({
            "Direct Assets (€)": "{:,.0f}",
            "Indirect Equity (€)": "{:,.0f}",
            "Total Equity (€)": "{:,.0f}",
        })
        .background_gradient(subset=["Total Equity (€)"], cmap="Blues")
        .background_gradient(subset=["Direct Assets (€)"], cmap="Greens")
    )
    st.dataframe(styled, use_container_width=True, height=340)

    # Effective ownership matrix
    with st.expander("🔍 Effective Ownership Matrix (direct + indirect %)"):
        st.caption("E[row, col] = effective % that ROW owns in COL (direct + all indirect paths)")
        E_pct = E * 100
        df_E = pd.DataFrame(E_pct, index=nodes, columns=nodes)
        st.dataframe(
            df_E.style.format("{:.3f}%").background_gradient(cmap="Blues", vmin=0, vmax=50),
            use_container_width=True,
        )

    # Bar chart via plotly
    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Direct Assets",
            x=df["Entity"],
            y=df["Direct Assets (€)"],
            marker_color="#238636",
            marker_line_color="#2EA043",
            marker_line_width=1,
        ))
        fig.add_trace(go.Bar(
            name="Indirect Equity",
            x=df["Entity"],
            y=df["Indirect Equity (€)"],
            marker_color="#1F6FEB",
            marker_line_color="#388BFD",
            marker_line_width=1,
        ))
        fig.update_layout(
            barmode="stack",
            plot_bgcolor="#0D1117",
            paper_bgcolor="#0D1117",
            font_color="#C9D1D9",
            font_family="Inter",
            legend=dict(orientation="h", y=1.08, x=0, font_color="#8B949E"),
            xaxis=dict(tickfont_color="#8B949E", gridcolor="#21262D", linecolor="#30363D"),
            yaxis=dict(tickfont_color="#8B949E", gridcolor="#21262D", linecolor="#30363D",
                       title="Equity (€)", title_font_color="#8B949E"),
            title=dict(text="Equity Composition by Entity", font_size=14, font_color="#C9D1D9"),
            margin=dict(t=60, b=40, l=60, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Install plotly for bar charts: `pip install plotly`")

# ── Graph Tab ────────────────────────────────────────────────────────────────
with tab_graph:
    col_g1, col_g2 = st.columns([4, 1])
    with col_g2:
        st.markdown('<div class="section-header">Legend</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size:.8rem;color:#8B949E;line-height:2'>
        <span style='color:#58A6FF'>●</span> High equity<br/>
        <span style='color:#1F6FEB'>●</span> Mid equity<br/>
        <span style='color:#1C2840'>●</span> Low equity<br/>
        <br/>
        <b>Node size</b> = relative equity<br/>
        <b>Edge width</b> = ownership %<br/>
        <br/>
        Hover nodes for details.<br/>
        Drag to rearrange.<br/>
        Scroll to zoom.
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:1.5rem">Quick Stats</div>', unsafe_allow_html=True)
        for node in nodes:
            i = idx_map[node]
            eq = equity_vec[i]
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;margin:.3rem 0;font-size:.8rem'>
              <span style='color:#C9D1D9'>{node}</span>
              <span style='color:#58A6FF;font-weight:600'>{eq:,.0f}€</span>
            </div>
            """, unsafe_allow_html=True)

    with col_g1:
        net = build_pyvis(nodes, edges, equity_vec, direct_assets)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
            net.save_graph(f.name)
            html_path = f.name

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Inject dark background override
        html_content = html_content.replace(
            "<body>",
            "<body style='background:#0D1117;margin:0;padding:0'>"
        )
        os.unlink(html_path)
        st.components.v1.html(html_content, height=650, scrolling=False)

    st.markdown("""
    <div style='font-size:.75rem;color:#484F58;margin-top:.5rem;text-align:center'>
    Graph uses ForceAtlas2 physics · Nodes auto-stabilise · Click & drag to explore
    </div>
    """, unsafe_allow_html=True)