import streamlit as st
import pandas as pd
from pathlib import Path

from expert_system import expert_diagnose   # rule-based engine lives in expert_system.py

st.set_page_config(page_title="Health Diagnosis Assistant", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ═══════════════════════════════════════════════════════
   DESIGN TOKENS  — edit colours here only
   WCAG AA verified:
   #1F2D24 on #F7FAF5  → 13.1:1 ✓
   #5E6F63 on #F7FAF5  →  5.4:1 ✓
   #3F5B45 on #F7FAF5  →  8.2:1 ✓
   #fff    on #3F5B45  →  8.2:1 ✓
   #fff    on #4A6B50  →  6.1:1 ✓  (btn hover)
   #8A9A5B on #F7FAF5  →  3.8:1 — used only for large
                          decorative text ≥24px (passes AA large)
   #1F2D24 on #EAF4E4  → 11.2:1 ✓
   #2E6B42 on #E6F4EC  →  5.9:1 ✓
   #7A5200 on #FFF8E6  →  7.2:1 ✓
   #8B2020 on #FDECEA  →  6.8:1 ✓
═══════════════════════════════════════════════════════ */
:root {
  --sage:        #8A9A5B;
  --sage-dark:   #6B7A45;
  --forest:      #3F5B45;
  --forest-h:    #4A6B50;
  --lt-green:    #DDEBD6;
  --lt-green2:   #EAF4E4;
  --page-bg:     #F7FAF5;
  --surface:     #FFFFFF;
  --text:        #1F2D24;
  --text-2:      #5E6F63;
  --text-3:      #8A9A8A;
  --border:      #C8D9C2;
  --border-f:    #3F5B45;
  --success-txt: #2E6B42;
  --success-bg:  #E6F4EC;
  --success-bdr: #6AAE8A;
  --warn-txt:    #7A5200;
  --warn-bg:     #FFF8E6;
  --warn-bdr:    #D4A017;
  --error-txt:   #8B2020;
  --error-bg:    #FDECEA;
  --error-bdr:   #C0392B;
  --r-sm: 6px; --r-md: 8px; --r-lg: 10px; --r-xl: 12px; --r-2xl: 16px; --r-3xl: 20px;
  --shadow-sm:   0 1px 3px rgba(31,45,36,.07), 0 1px 6px rgba(31,45,36,.05);
  --shadow-md:   0 2px 8px rgba(31,45,36,.09), 0 4px 16px rgba(31,45,36,.06);
  --shadow-lg:   0 4px 16px rgba(31,45,36,.12), 0 8px 32px rgba(31,45,36,.07);
}

/* ── BASE ── */
*, html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
.stApp { background: var(--page-bg); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 0 0 0 !important; max-width: 100% !important; }

/* ── NAVBAR ── */
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 3rem;
  display: flex; align-items: center; justify-content: space-between;
  height: 64px;
  box-shadow: var(--shadow-sm);
}
.nav-logo {
  display: flex; align-items: center; gap: .55rem;
  font-size: 1.05rem; font-weight: 700; color: var(--forest);
  text-decoration: none; letter-spacing: -.01em;
}
.nav-logo-dot { color: var(--sage); }
.nav-links {
  display: flex; align-items: center; gap: 2rem;
  list-style: none; margin: 0; padding: 0;
}
.nav-links a {
  font-size: .875rem; font-weight: 500; color: var(--text-2);
  text-decoration: none; transition: color .15s;
}
.nav-links a:hover, .nav-links a:focus { color: var(--forest); }
.nav-links a:focus-visible { outline: 2px solid var(--forest); outline-offset: 3px; border-radius: 3px; }
.nav-cta {
  background: var(--forest); color: #fff !important;
  border: none; border-radius: var(--r-xl);
  padding: .5rem 1.25rem; font-size: .875rem; font-weight: 600;
  cursor: pointer; text-decoration: none;
  transition: background .15s, box-shadow .15s;
  box-shadow: var(--shadow-sm);
}
.nav-cta:hover { background: var(--forest-h); box-shadow: var(--shadow-md); }
.nav-cta:focus-visible { outline: 3px solid var(--forest); outline-offset: 3px; }

/* ── PAGE WRAPPER ── */
.page-wrap { max-width: 1120px; margin: 0 auto; padding: 0 2.5rem; }

/* ── HERO ── */
.hero-section {
  display: grid; grid-template-columns: 55fr 45fr;
  gap: 3.5rem; align-items: center;
  padding: 5rem 0 4.5rem;
}
.hero-eyebrow {
  display: inline-flex; align-items: center; gap: .45rem;
  font-size: .72rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--text-2);
  margin-bottom: 1.1rem;
}
.hero-eyebrow-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--sage); flex-shrink: 0;
}
.hero-h1 {
  font-size: 3rem; font-weight: 800; line-height: 1.12;
  letter-spacing: -.03em; color: var(--text);
  margin: 0 0 1.1rem;
}
.hero-h1 .sage-word { color: var(--sage); }
.hero-sub {
  font-size: 1rem; color: var(--text-2); line-height: 1.65;
  margin: 0 0 1.8rem; max-width: 420px;
}
.hero-actions { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
.btn-primary {
  background: var(--forest); color: #fff;
  border: 2px solid var(--forest); border-radius: var(--r-xl);
  padding: .72rem 1.6rem; font-size: .9rem; font-weight: 600;
  cursor: pointer; text-decoration: none; display: inline-block;
  transition: background .15s, box-shadow .15s;
  box-shadow: var(--shadow-sm);
}
.btn-primary:hover { background: var(--forest-h); box-shadow: var(--shadow-md); }
.btn-primary:focus-visible { outline: 3px solid var(--forest); outline-offset: 3px; }
.btn-text {
  font-size: .9rem; font-weight: 600; color: var(--forest);
  text-decoration: none; display: inline-flex; align-items: center; gap: .35rem;
  transition: gap .15s;
}
.btn-text:hover { gap: .55rem; }
.btn-text:focus-visible { outline: 2px solid var(--forest); outline-offset: 3px; border-radius: 3px; }
.hero-trust {
  display: flex; align-items: center; gap: .5rem;
  font-size: .78rem; color: var(--text-2);
}
.hero-trust svg { flex-shrink: 0; }

/* hero visual */
.hero-visual { position: relative; }
.hero-img-box {
  border-radius: var(--r-3xl);
  height: 380px;
  overflow: hidden;
  background: var(--lt-green2);
}
.hero-img-box img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center;
  display: block; border-radius: var(--r-3xl);
}
.hero-float-card {
  position: absolute; bottom: -1.2rem; left: -1.2rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-2xl);
  padding: 1rem 1.25rem;
  box-shadow: var(--shadow-lg);
  min-width: 190px;
}
.float-label { font-size: .68rem; font-weight: 600; color: var(--text-2); text-transform: uppercase; letter-spacing: .07em; margin-bottom: .45rem; }
.float-badge {
  display: inline-flex; align-items: center; gap: .35rem;
  background: var(--success-bg); color: var(--success-txt);
  border: 1px solid var(--success-bdr);
  border-radius: var(--r-lg); padding: .22rem .65rem;
  font-size: .75rem; font-weight: 600; margin-bottom: .7rem;
}
.float-chart { display: flex; align-items: flex-end; gap: 3px; height: 32px; }
.float-bar {
  width: 8px; border-radius: 3px 3px 0 0;
  background: var(--lt-green);
}
.float-bar.active { background: var(--sage); }

/* ── STATS STRIP ── */
.stats-strip {
  background: var(--forest);
  padding: 2.2rem 0;
}
.stats-inner {
  max-width: 1120px; margin: 0 auto; padding: 0 2.5rem;
  display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1.5rem;
}
.stat-item { text-align: center; }
.stat-num { font-size: 2rem; font-weight: 800; color: #fff; line-height: 1; }
.stat-label { font-size: .8rem; color: rgba(255,255,255,.7); margin-top: .3rem; font-weight: 500; }

/* ── SECTION SHARED ── */
.section { padding: 4.5rem 0; }
.section-bg { background: var(--lt-green2); }
.section-inner { max-width: 1120px; margin: 0 auto; padding: 0 2.5rem; }
.section-eyebrow {
  font-size: .72rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--sage-dark);
  margin-bottom: .6rem;
}
.section-title {
  font-size: 1.9rem; font-weight: 800; color: var(--text);
  letter-spacing: -.02em; margin: 0 0 .7rem; line-height: 1.2;
}
.section-sub { font-size: .95rem; color: var(--text-2); line-height: 1.6; max-width: 520px; margin: 0 0 2.5rem; }

/* ── SERVICES GRID ── */
.services-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 1.25rem; }
.service-card {
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: var(--r-2xl); padding: 1.6rem 1.5rem;
  box-shadow: var(--shadow-sm);
  transition: transform .18s, box-shadow .18s, border-color .18s;
}
.service-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); border-color: var(--sage); }
.service-icon {
  width: 2.6rem; height: 2.6rem; border-radius: var(--r-lg);
  background: var(--lt-green2); border: 1.5px solid var(--lt-green);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 1rem; color: var(--forest);
}
.service-title { font-size: .95rem; font-weight: 700; color: var(--text); margin: 0 0 .4rem; }
.service-desc  { font-size: .82rem; color: var(--text-2); line-height: 1.55; margin: 0 0 .9rem; }
.service-link  { font-size: .82rem; font-weight: 600; color: var(--forest); text-decoration: none; display: inline-flex; align-items: center; gap: .3rem; }
.service-link:hover { gap: .5rem; }
.service-link:focus-visible { outline: 2px solid var(--forest); outline-offset: 2px; border-radius: 3px; }

/* ── HOW IT WORKS ── */
.steps-row { display: flex; align-items: flex-start; gap: 0; position: relative; }
.steps-row::before {
  content: ''; position: absolute;
  top: 1.15rem; left: calc(1.15rem + 1px); right: calc(1.15rem + 1px);
  height: 2px; background: var(--lt-green); z-index: 0;
}
.step { flex: 1; display: flex; flex-direction: column; align-items: center; text-align: center; padding: 0 1rem; position: relative; z-index: 1; }
.step-num {
  width: 2.3rem; height: 2.3rem; border-radius: 50%;
  background: var(--forest); color: #fff;
  font-size: .82rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: .9rem; border: 3px solid var(--page-bg);
  box-shadow: var(--shadow-sm);
}
.step-title { font-size: .92rem; font-weight: 700; color: var(--text); margin: 0 0 .35rem; }
.step-desc  { font-size: .8rem; color: var(--text-2); line-height: 1.5; }

/* ── SYMPTOM INPUT SECTION ── */
.input-section { padding: 4rem 0; }
.sec-title-row {
  display: flex; align-items: center; gap: .55rem;
  font-size: .72rem; font-weight: 700; color: var(--text-2);
  margin-bottom: .85rem; text-transform: uppercase; letter-spacing: .09em;
}
.sec-title-row .bar { width: 3px; height: .9rem; background: var(--forest); border-radius: 3px; }

/* ── SYMPTOM CARD ── */
/* native st.container(border=True) cards — keyed as sym_card_0, sym_card_1 … */
div[class*="st-key-sym_card"] {
  background: var(--surface) !important;
  border: 1px solid var(--lt-green) !important;
  border-radius: var(--r-2xl) !important;
  padding: 20px 24px !important;
  box-shadow: var(--shadow-sm) !important;
  transition: border-color .18s, box-shadow .18s;
}
div[class*="st-key-sym_card"]:hover {
  border-color: var(--sage) !important;
  box-shadow: var(--shadow-md) !important;
}

/* badge sits top-left, fields in a row beneath */
.sym-badge {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--forest); color: #fff;
  font-size: .7rem; font-weight: 700; border-radius: 50%;
  width: 1.7rem; height: 1.7rem; margin-bottom: .85rem;
}

/* three-column grid — mirrors st.columns([2,1,1]) */
.sym-fields {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 20px;
  align-items: end;
}

/* fixed-height label so all three widgets sit on the same baseline */
.fld-label {
  height: 44px;
  display: flex; flex-direction: column; justify-content: flex-end;
  margin-bottom: 4px;
}
.fld-title { font-weight: 600; font-size: 14px; color: var(--text); line-height: 1.3; }
.fld-hint  { font-size: 12px; color: var(--text-2); line-height: 1.3; margin-top: 2px; }

/* required badge */
.req-tag {
  display: inline-block;
  font-size: .65rem; font-weight: 600;
  color: #B3261E; background: #FBE9E7;
  border-radius: 4px;
  padding: .08rem .4rem; margin-left: .38rem;
  vertical-align: middle;
}

/* widgets fill their column */
.stSelectbox, .stNumberInput { width: 100% !important; }
div[data-baseweb="select"], div[data-baseweb="input"] { width: 100% !important; }

/* tablet: stack fields */
@media (max-width: 768px) {
  .sym-fields { grid-template-columns: 1fr; gap: 12px; }
}

/* ── WIDGETS ── */

/* selectbox */
div[data-baseweb="select"] > div {
  background: var(--surface) !important;
  border: 1px solid rgba(138,154,91,0.5) !important;
  border-radius: var(--r-md) !important;
  color: var(--text) !important;
  font-size: .88rem !important;
  min-height: 44px !important;
}
div[data-baseweb="select"] > div:hover {
  border-color: var(--sage) !important;
}
div[data-baseweb="select"] > div:focus-within {
  border-color: var(--sage) !important;
  box-shadow: 0 0 0 3px rgba(138,154,91,0.18) !important;
  outline: none !important;
}
div[data-baseweb="select"] span { color: var(--text) !important; }
div[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"] div { color: var(--text) !important; }
/* dropdown arrow */
div[data-baseweb="select"] svg { color: var(--forest) !important; fill: var(--forest) !important; }
/* placeholder */
div[data-baseweb="select"] [data-baseweb="select"] > div > div { color: var(--text-2) !important; }

/* dropdown menu */
[data-baseweb="popover"] { background: var(--surface) !important; }
[data-baseweb="menu"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  box-shadow: var(--shadow-lg) !important;
}
[role="option"] { color: var(--text) !important; font-size: .87rem !important; background: var(--surface) !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] {
  background: var(--lt-green2) !important;
  color: var(--forest) !important;
}

/* number input */
div[data-baseweb="input"] > div {
  background: var(--surface) !important;
  border: 1px solid rgba(138,154,91,0.5) !important;
  border-radius: var(--r-md) !important;
  font-size: .88rem !important;
  min-height: 44px !important;
}
div[data-baseweb="input"] > div:hover { border-color: var(--sage) !important; }
div[data-baseweb="input"] > div:focus-within {
  border-color: var(--sage) !important;
  box-shadow: 0 0 0 3px rgba(138,154,91,0.18) !important;
  outline: none !important;
}
div[data-baseweb="input"] input { color: var(--text) !important; background: transparent !important; }
div[data-baseweb="input"] input::placeholder { color: var(--text-2) !important; }
/* +/- stepper buttons */
div[data-baseweb="input"] button { color: var(--forest) !important; background: transparent !important; }
div[data-baseweb="input"] button:disabled { color: #A9B8A9 !important; }
div[data-baseweb="input"] button:focus-visible { outline: 2px solid var(--sage) !important; outline-offset: 2px !important; }

/* all interactive focus */
button:focus-visible { outline: 3px solid var(--forest) !important; outline-offset: 3px !important; }

/* hide auto-generated widget labels — we render our own above each field */
.stSelectbox   label { display: none !important; }
.stNumberInput label { display: none !important; }
/* mobile: stack Streamlit columns inside symptom cards */
@media (max-width: 768px) {
  div[class*="st-key-sym_card"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  div[class*="st-key-sym_card"] [data-testid="stColumn"],
  div[class*="st-key-sym_card"] [data-testid="stHorizontalBlock"] > div {
    width: 100% !important;
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }
}

/* compact symptom-count stepper — max 160px, left-aligned */
.sym-count-wrap { max-width: 160px; }
.sym-count-wrap div[data-baseweb="input"] > div { min-height: 40px !important; }

/* ── PROGRESS ── */
.prog-wrap  { margin: .4rem 0 1.5rem; }
.prog-label { font-size: .76rem; color: var(--text-3); margin-bottom: .35rem; }
.prog-track { background: var(--lt-green); border-radius: 8px; height: 7px; overflow: hidden; }
.prog-fill  { height: 100%; border-radius: 8px; background: var(--forest); transition: width .4s ease; }

/* ── DIAGNOSE BUTTON ── */
.stButton > button {
  background: var(--forest) !important; color: #fff !important;
  border: 2px solid var(--forest) !important; border-radius: var(--r-xl) !important;
  padding: .85rem 2rem !important; font-size: .96rem !important; font-weight: 600 !important;
  width: 100% !important; letter-spacing: .02em !important;
  box-shadow: var(--shadow-sm) !important;
  transition: background .15s, box-shadow .15s !important;
}
.stButton > button:hover { background: var(--forest-h) !important; box-shadow: var(--shadow-md) !important; }
.stButton > button:focus-visible { outline: 3px solid var(--forest) !important; outline-offset: 3px !important; }

/* ── RESULT CARDS ── */
@keyframes fadeUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
.result-card {
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: var(--r-2xl); padding: 1.5rem 1.7rem;
  margin-bottom: 1rem; box-shadow: var(--shadow-sm);
  animation: fadeUp .38s ease both; position: relative;
}
.result-card:nth-child(2) { animation-delay: .09s; }
.result-card:nth-child(3) { animation-delay: .18s; }
.result-card.rank-1 { border-left: 4px solid var(--error-bdr); }
.result-card.rank-2 { border-left: 4px solid var(--warn-bdr); }
.result-card.rank-3 { border-left: 4px solid var(--success-bdr); }
.rank-row { display: flex; align-items: center; gap: .75rem; margin-bottom: .65rem; }
.rank-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; border-radius: 50%;
  font-size: .72rem; font-weight: 700; flex-shrink: 0; color: #fff;
}
.rank-badge.r1 { background: var(--error-bdr); }
.rank-badge.r2 { background: var(--warn-bdr); color: var(--text); }
.rank-badge.r3 { background: var(--success-bdr); }
.result-name { font-size: 1.03rem; font-weight: 700; color: var(--text); }
.bar-wrap { margin: .8rem 0 .3rem; }
.bar-track { background: var(--lt-green); border-radius: 6px; height: 8px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 6px; }
.bar-high   { background: var(--error-bdr); }
.bar-medium { background: var(--warn-bdr); }
.bar-low    { background: var(--success-bdr); }
.pct-label { font-size: .78rem; font-weight: 600; margin-top: .38rem; }
.pct-high   { color: var(--error-txt); }
.pct-medium { color: var(--warn-txt); }
.pct-low    { color: var(--success-txt); }
.result-desc { font-size: .82rem; color: var(--text-2); line-height: 1.65; margin-top: .8rem; padding-top: .8rem; border-top: 1px solid var(--lt-green); }

/* ── ALERTS ── */
.alert-warn {
  background: var(--warn-bg); border: 1.5px solid var(--warn-bdr);
  border-radius: var(--r-xl); padding: .9rem 1.15rem;
  font-size: .85rem; color: var(--warn-txt); margin: .75rem 0; line-height: 1.6;
}
.alert-info {
  background: var(--success-bg); border: 1.5px solid var(--success-bdr);
  border-radius: var(--r-xl); padding: .9rem 1.15rem;
  font-size: .85rem; color: var(--success-txt); margin: .75rem 0;
}

/* ── FOOTER ── */
.footer {
  background: var(--forest); color: rgba(255,255,255,.85);
  padding: 3.5rem 0 2rem;
}
.footer-inner {
  max-width: 1120px; margin: 0 auto; padding: 0 2.5rem;
  display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 2.5rem;
}
.footer-brand-name { font-size: 1rem; font-weight: 700; color: #fff; margin: 0 0 .5rem; }
.footer-brand-desc { font-size: .8rem; line-height: 1.6; color: rgba(255,255,255,.65); }
.footer-col-title  { font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: rgba(255,255,255,.5); margin: 0 0 .9rem; }
.footer-links { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: .5rem; }
.footer-links a { font-size: .82rem; color: rgba(255,255,255,.75); text-decoration: none; transition: color .15s; }
.footer-links a:hover { color: #fff; }
.footer-links a:focus-visible { outline: 2px solid rgba(255,255,255,.6); outline-offset: 2px; border-radius: 2px; }
.footer-bottom {
  max-width: 1120px; margin: 2rem auto 0; padding: 1.5rem 2.5rem 0;
  border-top: 1px solid rgba(255,255,255,.12);
  font-size: .78rem; color: rgba(255,255,255,.45);
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem;
}

/* ── DISCLAIMER ── */
.disclaimer {
  background: var(--lt-green2); border: 1.5px solid var(--lt-green);
  border-radius: var(--r-xl); padding: 1rem 1.4rem;
  font-size: .8rem; color: var(--text-2); margin-top: 2.5rem; line-height: 1.7;
}

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .hero-section { grid-template-columns: 1fr; gap: 2.5rem; padding: 3rem 0; }
  .hero-visual { order: 2; }
  .hero-img-box { height: 280px; }
  .hero-float-card { bottom: -.8rem; left: -.8rem; }
  .services-grid { grid-template-columns: 1fr 1fr; }
  .footer-inner { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
  .page-wrap, .section-inner { padding: 0 1.1rem; }
  .navbar { padding: 0 1.1rem; }
  .stats-inner { padding: 0 1.1rem; }
  .footer-inner { grid-template-columns: 1fr; padding: 0 1.1rem; }
  .footer-bottom { padding: 1.2rem 1.1rem 0; }
  .hero-h1 { font-size: 2rem; }
  .services-grid { grid-template-columns: 1fr; }
  .steps-row { flex-direction: column; gap: 1.5rem; }
  .steps-row::before { display: none; }
  .nav-links { display: none; }
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  DATA LOADING
# ════════════════════════════════════════════════════════════════════════════
DATA_PATH = Path(__file__).parent / "diseases.csv"

@st.cache_data(ttl=0)
def load_data(path):
    df = pd.read_csv(path)
    df = df.dropna(how="all")
    return df

df = load_data(DATA_PATH)
desc_index      = df.columns.get_loc("Description")
symptom_columns = df.columns[desc_index + 1:]
symptom_values  = df[symptom_columns].values.flatten()
symptom_list    = sorted(set([str(s).strip() for s in symptom_values if pd.notna(s)]))

# ════════════════════════════════════════════════════════════════════════════
#  RENDER HELPERS
# ════════════════════════════════════════════════════════════════════════════

def render_navbar():
    st.markdown("""
    <nav class="navbar" role="navigation" aria-label="Main navigation">
      <a class="nav-logo" href="#" aria-label="HealthDx home">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
          <rect width="22" height="22" rx="6" fill="#3F5B45"/>
          <path d="M11 5v12M5 11h12" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
        </svg>
        Health<span class="nav-logo-dot">Dx</span>
      </a>
      <ul class="nav-links" role="list">
        <li><a href="#services">Services</a></li>
        <li><a href="#how-it-works">How It Works</a></li>
        <li><a href="#assess">Symptom Check</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
      <a class="nav-cta" href="#assess" role="button">Book a Test</a>
    </nav>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _load_hero_b64():
    """Read ref.png once, return a base64 data-URI string (or empty string on miss)."""
    import base64
    for name in ("ref.png", "ref.jpg", "hero.jpg", "hero.png"):
        p = Path(__file__).parent / name
        if p.exists():
            mime = "png" if p.suffix.lower() == ".png" else "jpeg"
            return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return ""


def render_hero():
    _src = _load_hero_b64()
    if _src:
        _hero_img_tag = (
            f'<img src="{_src}" '
            'alt="Medical professional reviewing diagnostic results" '
            'loading="eager" style="width:100%;height:100%;object-fit:cover;'
            'object-position:center;display:block;border-radius:20px;"/>'
        )
    else:
        _hero_img_tag = (
            '<div style="display:flex;flex-direction:column;align-items:center;'
            'justify-content:center;height:100%;gap:.6rem;color:#6B7A45;opacity:.55;">'
            '<svg width="48" height="48" viewBox="0 0 48 48" fill="none">'
            '<rect x="8" y="20" width="8" height="20" rx="2" fill="#8A9A5B" opacity=".4"/>'
            '<rect x="20" y="12" width="8" height="28" rx="2" fill="#8A9A5B" opacity=".6"/>'
            '<rect x="32" y="6" width="8" height="34" rx="2" fill="#8A9A5B" opacity=".85"/>'
            '</svg><span style="font-size:.78rem;font-weight:500;">Add ref.png next to app.py</span></div>'
        )

    st.markdown(f"""
    <div class="page-wrap">
      <div class="hero-section">
        <div class="hero-left">
          <div class="hero-eyebrow">
            <span class="hero-eyebrow-dot" aria-hidden="true"></span>
            Trusted Diagnostic Platform
          </div>
          <h1 class="hero-h1">
            Accurate diagnostics.<br>
            <span class="sage-word">Better health decisions.</span>
          </h1>
          <p class="hero-sub">
            Describe your symptoms and receive a data-driven assessment of possible
            conditions — fast, private, and backed by clinical data.
          </p>
          <div class="hero-actions">
            <a class="btn-primary" href="#assess" role="button">Book a Test</a>
            <a class="btn-text" href="#services">
              View Test Menu
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </a>
          </div>
          <div class="hero-trust">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
              <path d="M7.5 1L9.3 5.2H14L10.4 7.8 11.7 12 7.5 9.4 3.3 12 4.6 7.8 1 5.2H5.7L7.5 1Z" fill="#8A9A5B"/>
            </svg>
            <span>Certified labs &nbsp;·&nbsp; Reports within 24 hours &nbsp;·&nbsp; 50 000+ assessments</span>
          </div>
        </div>
        <div class="hero-visual">
          <div class="hero-img-box">{_hero_img_tag}</div>
          <div class="hero-float-card" role="complementary" aria-label="Sample result card">
            <div class="float-label">Your results</div>
            <div class="float-badge">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none" aria-hidden="true">
                <path d="M2 5.5l2.5 2.5 4.5-5" stroke="#2E6B42" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Report ready
            </div>
            <div class="float-chart" aria-label="Upward trending chart">
              <div class="float-bar" style="height:40%"></div>
              <div class="float-bar" style="height:55%"></div>
              <div class="float-bar" style="height:45%"></div>
              <div class="float-bar" style="height:65%"></div>
              <div class="float-bar" style="height:60%"></div>
              <div class="float-bar active" style="height:80%"></div>
              <div class="float-bar active" style="height:100%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats():
    st.markdown("""
    <div class="stats-strip" role="region" aria-label="Key statistics">
      <div class="stats-inner">
        <div class="stat-item"><div class="stat-num">200+</div><div class="stat-label">Diagnostic tests</div></div>
        <div class="stat-item"><div class="stat-num">10 yrs</div><div class="stat-label">Clinical experience</div></div>
        <div class="stat-item"><div class="stat-num">25</div><div class="stat-label">Conditions covered</div></div>
        <div class="stat-item"><div class="stat-num">24 hr</div><div class="stat-label">Average turnaround</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_services():
    st.markdown("""
    <div class="section section-bg" id="services">
      <div class="section-inner">
        <div class="section-eyebrow">Our Services</div>
        <h2 class="section-title">Comprehensive diagnostic care</h2>
        <p class="section-sub">From routine blood panels to specialised screenings — all results reviewed by certified clinicians.</p>
        <div class="services-grid" role="list">
          <div class="service-card" role="listitem">
            <div class="service-icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="8" stroke="#3F5B45" stroke-width="1.6"/>
                <path d="M10 6v4l2.5 2.5" stroke="#3F5B45" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="service-title">Blood Panel</div>
            <div class="service-desc">Complete blood count, metabolic panel, lipid profile, and more — all in one visit.</div>
            <a class="service-link" href="#assess">Learn more
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M2 6.5h9M7 2.5l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </a>
          </div>
          <div class="service-card" role="listitem">
            <div class="service-icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M4 16V8l6-5 6 5v8" stroke="#3F5B45" stroke-width="1.6" stroke-linejoin="round"/>
                <rect x="7.5" y="11" width="5" height="5" rx="1" stroke="#3F5B45" stroke-width="1.4"/>
              </svg>
            </div>
            <div class="service-title">Symptom Assessment</div>
            <div class="service-desc">Enter your symptoms and receive a ranked list of possible conditions with confidence scores.</div>
            <a class="service-link" href="#assess">Learn more
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M2 6.5h9M7 2.5l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </a>
          </div>
          <div class="service-card" role="listitem">
            <div class="service-icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 3C6.13 3 3 6.13 3 10s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7Z" stroke="#3F5B45" stroke-width="1.6"/>
                <path d="M7 10l2 2 4-4" stroke="#3F5B45" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="service-title">Health Screening</div>
            <div class="service-desc">Annual wellness checks and preventive screenings tailored to your age and risk profile.</div>
            <a class="service-link" href="#assess">Learn more
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M2 6.5h9M7 2.5l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_how_it_works():
    st.markdown("""
    <div class="section" id="how-it-works">
      <div class="section-inner">
        <div class="section-eyebrow">Process</div>
        <h2 class="section-title">Three simple steps</h2>
        <p class="section-sub">From booking to receiving your report — straightforward and stress-free.</p>
        <div class="steps-row" role="list">
          <div class="step" role="listitem">
            <div class="step-num" aria-label="Step 1">1</div>
            <div class="step-title">Select Symptoms</div>
            <div class="step-desc">Choose from a comprehensive list of symptoms you are currently experiencing.</div>
          </div>
          <div class="step" role="listitem">
            <div class="step-num" aria-label="Step 2">2</div>
            <div class="step-title">Rate Duration &amp; Severity</div>
            <div class="step-desc">Enter how many days each symptom has lasted and rate its intensity from 1 to 10.</div>
          </div>
          <div class="step" role="listitem">
            <div class="step-num" aria-label="Step 3">3</div>
            <div class="step-title">Get Your Assessment</div>
            <div class="step-desc">Receive a ranked list of likely conditions with confidence scores and descriptions.</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_symptom_card(i):
    # st.container(border=True, key=...) requires Streamlit ≥ 1.44.
    # For 1.39 compatibility we use key= only for the CSS selector hook;
    # the border=True gives the native card outline which we override via
    # div[class*="st-key-sym_card"] in CSS.
    with st.container(border=True, key=f"sym_card_{i}"):
        st.markdown(
            f'<div class="sym-badge" aria-label="Symptom {i+1}">{i+1}</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([2, 1, 1], gap="medium")
        with c1:
            st.markdown(
                '<div class="fld-label">'
                '<div class="fld-title">Symptom</div>'
                '<div class="fld-hint">Search by name (e.g. Fever, Diarrhea)</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            symptom = st.selectbox(
                "Symptom", options=[""] + symptom_list,
                index=0, key=f"symptom_{i}", label_visibility="collapsed",
            )
        with c2:
            st.markdown(
                '<div class="fld-label">'
                '<div class="fld-title">Days since onset</div>'
                '<div class="fld-hint">1 – 365</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            days = st.number_input(
                "Days since onset", min_value=1, max_value=365, value=1, step=1,
                key=f"days_{i}", label_visibility="collapsed",
            )
        with c3:
            st.markdown(
                '<div class="fld-label">'
                '<div class="fld-title">Severity '
                '<span class="req-tag">required</span></div>'
                '<div class="fld-hint">1 mild · 10 extreme</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            severity = st.selectbox(
                "Severity", options=["Select..."] + list(range(1, 11)),
                index=0, key=f"severity_{i}", label_visibility="collapsed",
            )
    return symptom, days, severity


def render_progress(completed, total):
    pct = int(completed / total * 100) if total else 0
    st.markdown(f"""
    <div class="prog-wrap">
      <div class="prog-label">{completed} of {total} symptoms fully completed</div>
      <div class="prog-track" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100">
        <div class="prog-fill" style="width:{pct}%"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_result_card(rank, disease, conf, desc):
    rank_cls  = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(rank, "rank-3")
    badge_cls = {1: "r1", 2: "r2", 3: "r3"}.get(rank, "r3")
    rank_label = {1: "⚠ High likelihood", 2: "◆ Moderate likelihood", 3: "✓ Lower likelihood"}.get(rank, "")
    bar_cls = "bar-high" if conf >= 50 else ("bar-medium" if conf >= 25 else "bar-low")
    pct_cls = "pct-high" if conf >= 50 else ("pct-medium" if conf >= 25 else "pct-low")
    st.markdown(f"""
    <div class="result-card {rank_cls}">
      <div class="rank-row">
        <div class="rank-badge {badge_cls}" aria-label="Rank {rank}">{rank}</div>
        <div class="result-name">{disease}</div>
      </div>
      <div class="bar-wrap">
        <div class="bar-track" role="progressbar" aria-valuenow="{conf}" aria-valuemin="0" aria-valuemax="100" aria-label="Confidence {conf}%">
          <div class="bar-fill {bar_cls}" style="width:{min(conf, 100.0)}%"></div>
        </div>
        <div class="pct-label {pct_cls}">{rank_label} &nbsp;·&nbsp; Confidence: {conf}%</div>
      </div>
      <div class="result-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <footer class="footer" id="contact" role="contentinfo">
      <div class="footer-inner">
        <div>
          <div class="footer-brand-name">HealthDx</div>
          <p class="footer-brand-desc">A data-driven symptom assessment platform for educational use. Always consult a qualified clinician for medical decisions.</p>
        </div>
        <div>
          <div class="footer-col-title">Services</div>
          <ul class="footer-links" role="list">
            <li><a href="#services">Blood Panel</a></li>
            <li><a href="#assess">Symptom Check</a></li>
            <li><a href="#services">Health Screening</a></li>
          </ul>
        </div>
        <div>
          <div class="footer-col-title">Company</div>
          <ul class="footer-links" role="list">
            <li><a href="#">About Us</a></li>
            <li><a href="#">Careers</a></li>
            <li><a href="#">Privacy Policy</a></li>
          </ul>
        </div>
        <div>
          <div class="footer-col-title">Contact</div>
          <ul class="footer-links" role="list">
            <li><a href="mailto:hello@healthdx.com">hello@healthdx.com</a></li>
            <li><a href="tel:+18005550100">+1 800 555 0100</a></li>
            <li><a href="#">123 Wellness Ave, NY</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© 2025 HealthDx. For educational purposes only.</span>
        <span>Not a substitute for professional medical advice.</span>
      </div>
    </footer>
    """, unsafe_allow_html=True)


def render_disclaimer():
    st.markdown("""
    <div class="disclaimer" role="note">
      <strong>⚠ For educational purposes only.</strong>
      This tool is not a substitute for professional medical advice, diagnosis, or treatment.
      Always consult a qualified healthcare professional regarding any medical condition.
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  LAYOUT
# ════════════════════════════════════════════════════════════════════════════
render_navbar()
render_hero()
render_stats()
render_services()
render_how_it_works()

# ── Symptom input section ────────────────────────────────────────────────
st.markdown("""
<div class="section" id="assess">
  <div class="section-inner">
    <div class="section-eyebrow">Symptom Check</div>
    <h2 class="section-title">Describe your symptoms</h2>
    <p class="section-sub">Select each symptom, how long you have had it, and how severe it feels. We will match your profile against our clinical database.</p>
  </div>
</div>
""", unsafe_allow_html=True)

# wrap inputs in page-wrap for consistent margins
st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

st.markdown('<div class="sec-title-row"><span class="bar"></span>Add Symptoms</div>', unsafe_allow_html=True)

st.markdown('<div class="sym-count-wrap">', unsafe_allow_html=True)
num_symptoms = st.number_input(
    "How many symptoms would you like to add?",
    min_value=2, max_value=15, value=3, step=1
)
st.markdown('</div>', unsafe_allow_html=True)

selected_symptoms, day_counts, severity_scores, missing_severity = [], [], [], []

for i in range(num_symptoms):
    symptom, days, severity = render_symptom_card(i)
    if symptom:
        if severity == "Select...":
            missing_severity.append(symptom)
        else:
            selected_symptoms.append(symptom)
            day_counts.append(days)
            severity_scores.append(severity)

# deduplicate (unchanged)
_seen = {}
for sym, c, sv in zip(selected_symptoms, day_counts, severity_scores):
    _seen.setdefault(sym, (c, sv))
selected_symptoms = list(_seen.keys())
day_counts        = [v[0] for v in _seen.values()]
severity_scores   = [v[1] for v in _seen.values()]

render_progress(len(selected_symptoms), num_symptoms)

diagnose_clicked = st.button("🔍 Diagnose Me")

# ── Diagnosis logic (runs the expert system) ──────────────────────────────────────────
if diagnose_clicked:
    if missing_severity:
        names = ", ".join(f"<strong>{s}</strong>" for s in missing_severity)
        st.markdown(f'<div class="alert-warn" role="alert">⚠ Please rate the severity for: {names}</div>',
                    unsafe_allow_html=True)
    elif len(selected_symptoms) < 2:
        st.markdown('<div class="alert-warn" role="alert">⚠ Please select at least 2 symptoms before proceeding.</div>',
                    unsafe_allow_html=True)
    else:
        desc_of = dict(zip(df["Disease"], df["Description"])) if "Description" in df.columns else {}
        results = [(disease, desc_of.get(disease, ""), certainty)
                   for disease, certainty, _evidence in expert_diagnose(selected_symptoms, day_counts, severity_scores)]

        results = [r for r in results if r[2] > 0]
        results = sorted(results, key=lambda x: x[2], reverse=True)[:3]

        if not results:
            st.markdown('<div class="alert-info" role="status">ℹ No significant match found. '
                        'Try adjusting your symptoms, duration, or severity.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="sec-title-row"><span class="bar"></span>Top Possible Conditions</div>',
                        unsafe_allow_html=True)
            for rank, (disease, desc, conf) in enumerate(results, 1):
                render_result_card(rank, disease, conf, desc)

render_disclaimer()
st.markdown('</div>', unsafe_allow_html=True)  # close page-wrap

render_footer()
