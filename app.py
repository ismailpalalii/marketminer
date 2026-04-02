#!/usr/bin/env python3
"""MarketMiner Cloud — Read-only panel (Streamlit Community Cloud)"""

import streamlit as st
import json
import os
from datetime import datetime
from collections import Counter

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

st.set_page_config(page_title="MarketMiner", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
.block-container { padding-top: 2.5rem; max-width: 1100px; }
.tag { display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:600; margin-right:4px; margin-bottom:4px; }
.t-strong { background:#dcfce7; color:#15803d; }
.t-medium { background:#fef9c3; color:#a16207; }
.t-weak { background:#f1f5f9; color:#64748b; }
.t-sub { background:#fee2e2; color:#dc2626; }
.t-cat { background:#ede9fe; color:#7c3aed; }
.t-kw { background:#e0f2fe; color:#0369a1; }
.t-blue_ocean { background:#dbeafe; color:#1d4ed8; font-weight:700; }
.t-opportunity { background:#dcfce7; color:#15803d; font-weight:700; }
.t-competitive { background:#fef9c3; color:#a16207; }
.t-saturated { background:#fee2e2; color:#dc2626; }
.meta { color:#94a3b8; font-size:0.78rem; }
.competitor { border:1px solid rgba(148,163,184,0.3); border-radius:8px; padding:8px 12px; margin-top:6px; font-size:0.8rem; color:inherit; }
</style>""", unsafe_allow_html=True)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"signals": [], "last_run": None, "total_runs": 0}


def signal_sort_key(s):
    gap_order = {"blue_ocean": 0, "opportunity": 1, "competitive": 2, "saturated": 3, "unknown": 4}
    strength_order = {"strong": 0, "medium": 1, "weak": 2}
    return (
        gap_order.get(s.get("market_gap", "unknown"), 4),
        strength_order.get(s.get("signal_strength", "weak"), 2),
        -(s.get("upvotes", 0)),
    )


data = load_data()
signals = data.get("signals", [])

if not signals:
    st.info("Henuz sinyal yok.")
    st.stop()

# ===== HEADER =====
strong_n = sum(1 for s in signals if s.get("signal_strength") == "strong")
starred_n = sum(1 for s in signals if s.get("status") == "starred")
last_run = data.get("last_run", "")
last_run_str = ""
if last_run:
    try:
        last_run_str = f" · Son tarama: {datetime.fromisoformat(last_run).strftime('%d %b %Y %H:%M')}"
    except Exception:
        pass

st.markdown(f"### MarketMiner")
st.caption(f"{strong_n} guclu · {starred_n} yildiz · {len(signals)} toplam{last_run_str}")

# ===== FILTERS =====
scan_dates = sorted(set(s.get("found_date", "") for s in signals if s.get("found_date")), reverse=True)

with st.expander("Filtreler", expanded=False):
    f1, f2, f3, f4, f5, f6, f7 = st.columns([1.5, 1, 1, 1, 1, 1, 1])

    with f1:
        if scan_dates:
            date_labels = ["Tum Taramalar"] + [
                f"{datetime.fromisoformat(d).strftime('%d %b %Y')} ({sum(1 for s in signals if s.get('found_date')==d)})"
                for d in scan_dates
            ]
            date_values = [None] + scan_dates
            sel_idx = st.selectbox("Tarih", range(len(date_labels)), format_func=lambda i: date_labels[i])
            selected_scan_date = date_values[sel_idx]
        else:
            selected_scan_date = None

    with f2:
        status_options = {"Tumu": None, "Yeni": "new", "Yildizli": "starred", "Insada": "building", "Arsiv": "archived"}
        sel_status = st.selectbox("Durum", list(status_options.keys()))

    with f3:
        cats = ["Tumu"] + sorted(set(s.get("category", "") for s in signals if s.get("category")))
        sel_cat = st.selectbox("Kategori", cats)

    with f4:
        strength_opts = {"Tumu": None, "Guclu": "strong", "Orta": "medium", "Zayif": "weak"}
        sel_str = st.selectbox("Sinyal", list(strength_opts.keys()))

    with f5:
        subs = ["Tumu"] + sorted(set(s.get("subreddit", "") for s in signals if s.get("subreddit")))
        sel_sub = st.selectbox("Subreddit", subs)

    with f6:
        gap_opts = {"Tumu": None, "Blue Ocean": "blue_ocean", "Firsat": "opportunity", "Rekabetci": "competitive", "Doymus": "saturated"}
        sel_gap = st.selectbox("Pazar", list(gap_opts.keys()))

    with f7:
        search_q = st.text_input("Ara", placeholder="keyword...")

# Defaults when expander not opened
if 'sel_status' not in dir():
    gap_opts = {"Tumu": None}
    selected_scan_date = None
    sel_status = "Tumu"
    sel_cat = "Tumu"
    sel_str = "Tumu"
    sel_sub = "Tumu"
    sel_gap = "Tumu"
    search_q = ""

# ===== APPLY FILTERS =====
filtered = signals.copy()

if selected_scan_date:
    filtered = [s for s in filtered if s.get("found_date") == selected_scan_date]

sv = status_options.get(sel_status)
if sv:
    filtered = [s for s in filtered if s.get("status") == sv]
else:
    filtered = [s for s in filtered if s.get("status") != "archived"]

if sel_cat != "Tumu":
    filtered = [s for s in filtered if s.get("category") == sel_cat]
if strength_opts.get(sel_str):
    filtered = [s for s in filtered if s.get("signal_strength") == strength_opts[sel_str]]
if sel_sub != "Tumu":
    filtered = [s for s in filtered if s.get("subreddit") == sel_sub]
if gap_opts.get(sel_gap):
    filtered = [s for s in filtered if s.get("market_gap") == gap_opts[sel_gap]]
if search_q:
    q = search_q.lower()
    filtered = [s for s in filtered if
                q in s.get("title", "").lower() or q in s.get("body", "").lower()
                or q in s.get("pain_summary", "").lower() or q in s.get("ios_angle", "").lower()
                or any(q in kw.lower() for kw in s.get("keywords", []))]

filtered.sort(key=signal_sort_key)

# ===== TABS =====
tab_signals, tab_keywords, tab_insights = st.tabs(["Sinyaller", "Keywords", "Ozet"])

# ----- TAB 1: SIGNALS -----
with tab_signals:
    if not filtered:
        st.info("Filtreye uyan sinyal yok.")
    else:
        total = len(filtered)

        if "page" not in st.session_state:
            st.session_state.page = 1
        if "page_size" not in st.session_state:
            st.session_state.page_size = 10

        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            new_size = st.selectbox("Sayfa", [10, 50, 100],
                                    index=[10, 50, 100].index(st.session_state.page_size),
                                    label_visibility="collapsed", key="_ps")
            if new_size != st.session_state.page_size:
                st.session_state.page_size = new_size
                st.session_state.page = 1
                st.rerun()

        page_size = st.session_state.page_size
        total_pages = max((total + page_size - 1) // page_size, 1)
        if st.session_state.page > total_pages:
            st.session_state.page = total_pages
        page = st.session_state.page
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)

        with p3:
            st.caption(f"{page}/{total_pages}")

        st.caption(f"{total} sinyal ({start_idx+1}-{end_idx})")

        for signal in filtered[start_idx:end_idx]:
            strength = signal.get("signal_strength", "medium")
            status = signal.get("status", "new")

            with st.container(border=True):
                sub = signal.get("subreddit", "")
                cat = signal.get("category", "")
                gap = signal.get("market_gap", "")
                str_cls = {"strong": "t-strong", "medium": "t-medium", "weak": "t-weak"}.get(strength, "t-medium")
                str_lbl = {"strong": "Guclu", "medium": "Orta", "weak": "Zayif"}.get(strength, "?")
                gap_cls = f"t-{gap}" if gap else ""
                gap_lbl = {"blue_ocean": "Blue Ocean", "opportunity": "Firsat", "competitive": "Rekabetci", "saturated": "Doymus"}.get(gap, "")

                tags = f'<span class="tag {str_cls}">{str_lbl}</span>'
                if gap_lbl:
                    tags += f'<span class="tag {gap_cls}">{gap_lbl}</span>'
                if sub:
                    tags += f'<span class="tag t-sub">r/{sub}</span>'
                if cat:
                    tags += f'<span class="tag t-cat">{cat}</span>'
                st.markdown(tags, unsafe_allow_html=True)

                title = signal.get("title", "")
                url = signal.get("url", "")
                if title:
                    st.markdown(f"**[{title}]({url})**" if url else f"**{title}**")

                pain = signal.get("pain_summary", "")
                ios = signal.get("ios_angle", "")
                if pain:
                    st.markdown(f"Aci: {pain}")
                if ios:
                    st.markdown(f"iOS Fikri: _{ios}_")

                keywords = signal.get("keywords", [])
                if keywords:
                    kw_html = " ".join(f'<span class="tag t-kw">{kw}</span>' for kw in keywords)
                    st.markdown(kw_html, unsafe_allow_html=True)

                comps = signal.get("competitors", [])
                if comps:
                    comp_parts = []
                    for c in comps[:3]:
                        stars = f"{c['rating']}/5" if c.get("rating") else ""
                        reviews = f"{c['reviews']:,} yorum" if c.get("reviews") else ""
                        price = c.get("price", "")
                        comp_parts.append(f"<b>{c['name']}</b> — {stars} ({reviews}) {price}")
                    st.markdown('<div class="competitor">Rakipler: ' + " | ".join(comp_parts) + '</div>', unsafe_allow_html=True)

                upvotes = signal.get("upvotes", 0)
                comments = signal.get("comments", 0)
                post_date = signal.get("post_date", "")
                meta = []
                if upvotes:
                    meta.append(f"{upvotes:,} up")
                if comments:
                    meta.append(f"{comments} yorum")
                if post_date:
                    meta.append(post_date)
                if meta:
                    st.markdown(f'<span class="meta">{" · ".join(meta)}</span>', unsafe_allow_html=True)

        # Bottom pagination
        bp1, bp2, bp3, bp4, bp5 = st.columns([2, 1, 1, 1, 2])
        with bp2:
            if page > 1:
                if st.button("← Onceki", key="prev", use_container_width=True):
                    st.session_state.page = page - 1
                    st.rerun()
        with bp3:
            st.markdown(f"<div style='text-align:center;padding:8px;color:#94a3b8;'>{page}/{total_pages}</div>", unsafe_allow_html=True)
        with bp4:
            if page < total_pages:
                if st.button("Sonraki →", key="next", use_container_width=True):
                    st.session_state.page = page + 1
                    st.rerun()

# ----- TAB 2: KEYWORDS -----
with tab_keywords:
    all_kw = {}
    for s in signals:
        if s.get("status") == "archived":
            continue
        for kw in s.get("keywords", []):
            kw_lower = kw.lower().strip()
            if kw_lower and len(kw_lower) > 2:
                all_kw[kw_lower] = all_kw.get(kw_lower, 0) + 1

    if all_kw:
        import pandas as pd
        top_kw = sorted(all_kw.items(), key=lambda x: x[1], reverse=True)[:30]
        kw_df = pd.DataFrame(top_kw, columns=["Keyword", "Sinyal"])
        st.markdown("#### App Store Keyword Trendleri")
        st.bar_chart(kw_df.set_index("Keyword"), height=400)
        st.dataframe(kw_df, use_container_width=True, hide_index=True)
    else:
        st.info("Keyword verisi yok.")

# ----- TAB 3: INSIGHTS -----
with tab_insights:
    import pandas as pd
    active = [s for s in signals if s.get("status") != "archived"]

    # Market gap summary
    st.markdown("#### Pazar Durumu")
    gap_counts = Counter(s.get("market_gap", "unknown") for s in active)
    gap_labels = {"blue_ocean": "Blue Ocean", "opportunity": "Firsat", "competitive": "Rekabetci", "saturated": "Doymus", "unknown": "Bilinmiyor"}
    gap_data = [(gap_labels.get(g, g), c) for g, c in gap_counts.most_common()]
    if gap_data:
        st.bar_chart(pd.DataFrame(gap_data, columns=["Pazar", "Sayi"]).set_index("Pazar"))

    i1, i2 = st.columns(2)
    with i1:
        st.markdown("#### Kategori")
        cc = Counter(s.get("category", "?") for s in active)
        if cc:
            st.bar_chart(pd.DataFrame(cc.most_common(15), columns=["Kategori", "Sayi"]).set_index("Kategori"))

    with i2:
        st.markdown("#### Subreddit")
        sc = Counter(s.get("subreddit", "") for s in active if s.get("subreddit"))
        if sc:
            st.bar_chart(pd.DataFrame(sc.most_common(15), columns=["Sub", "Sayi"]).set_index("Sub"))

    st.divider()
    st.markdown("#### En Iyi Firsatlar (Blue Ocean + Opportunity)")
    opportunities = sorted(
        [s for s in active if s.get("market_gap") in ("blue_ocean", "opportunity")],
        key=lambda x: x.get("upvotes", 0), reverse=True
    )
    if opportunities:
        for s in opportunities[:10]:
            gap_lbl = {"blue_ocean": "🔵 Blue Ocean", "opportunity": "🟢 Firsat"}.get(s.get("market_gap"), "")
            kws = ", ".join(s.get("keywords", [])[:3])
            comp_names = ", ".join(c["name"] for c in s.get("competitors", [])[:2])
            st.markdown(f"- {gap_lbl} **{s.get('title','')[:70]}** ({s.get('upvotes',0)} up)")
            st.caption(f"  {s.get('pain_summary','')} | iOS: {s.get('ios_angle','')} | KW: {kws}")
            if comp_names:
                st.caption(f"  Rakipler: {comp_names}")
    else:
        st.caption("Blue ocean / firsat sinyali yok henuz. Daha fazla tarama yap.")

    st.divider()
    st.markdown("#### En Guclu Sinyaller")
    strong = sorted([s for s in active if s.get("signal_strength") == "strong"],
                   key=lambda x: x.get("upvotes", 0), reverse=True)
    if strong:
        for s in strong[:10]:
            kws = ", ".join(s.get("keywords", [])[:3])
            comp_names = ", ".join(c["name"] for c in s.get("competitors", [])[:2])
            st.markdown(f"- **{s.get('title','')[:70]}** ({s.get('upvotes',0)} up)")
            st.caption(f"  {s.get('pain_summary','')} | iOS: {s.get('ios_angle','')} | KW: {kws}")
            if comp_names:
                st.caption(f"  Rakipler: {comp_names}")
    else:
        st.caption("Guclu sinyal yok.")
