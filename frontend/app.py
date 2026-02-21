"""
LifeVault — Streamlit Frontend (Premium Edition)
==================================================
A stunning, modern UI for the LifeVault personal memory assistant.

Features:
    - Glassmorphism dark theme with animated gradients
    - Chat-style search input
    - 3-column masonry-style results grid
    - Match percentage with animated bars
    - Timeline analytics (Plotly)
    - "Surprise Me" random memory mode
    - Live stats with animated counters
    - Micro-animations and hover effects

Run with:
    streamlit run frontend/app.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ── Project root in path ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# ── API Configuration ───────────────────────────────────────────────────────
API_BASE = os.getenv("LIFEVAULT_API_URL", "http://127.0.0.1:8000")

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="LifeVault — Your AI Memory Vault",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# PREMIUM CSS — Bento Dark + Organic Motion
# =============================================================================

st.markdown("""
<style>
    /* ── Fonts ──────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=DM+Mono:wght@400;500&display=swap');

    /* ── Design Tokens ──────────────────────────────────────────────────── */
    :root {
        --void:         #050508;
        --surface-0:    #0c0c12;
        --surface-1:    #12121c;
        --surface-2:    #1a1a28;
        --surface-3:    #222233;
        --rim:          rgba(255,255,255,0.055);
        --rim-bright:   rgba(255,255,255,0.12);

        --iris:         #6d5acd;
        --iris-glow:    rgba(109,90,205,0.35);
        --iris-subtle:  rgba(109,90,205,0.12);
        --teal:         #2dd4bf;
        --teal-glow:    rgba(45,212,191,0.25);
        --rose:         #f472b6;
        --amber:        #fbbf24;
        --emerald:      #34d399;

        --text-1:       #e8e8f0;
        --text-2:       rgba(232,232,240,0.6);
        --text-3:       rgba(232,232,240,0.35);

        --radius-sm:    10px;
        --radius-md:    16px;
        --radius-lg:    22px;
        --radius-xl:    30px;

        --font-display: 'Syne', sans-serif;
        --font-body:    'DM Sans', sans-serif;
        --font-mono:    'DM Mono', monospace;
    }

    /* ── Global Reset ───────────────────────────────────────────────────── */
    * { box-sizing: border-box; }

    html, body, .stApp {
        font-family: var(--font-body) !important;
        background: var(--void) !important;
        color: var(--text-1) !important;
    }

    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* ── Grain Overlay ──────────────────────────────────────────────────── */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
        pointer-events: none;
        z-index: 9999;
        opacity: 0.4;
    }

    /* ── Ambient Light Blobs ─────────────────────────────────────────────── */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse 70% 55% at 15% 25%, rgba(109,90,205,0.07) 0%, transparent 60%),
            radial-gradient(ellipse 50% 40% at 85% 15%, rgba(45,212,191,0.05) 0%, transparent 55%),
            radial-gradient(ellipse 45% 50% at 55% 88%, rgba(244,114,182,0.04) 0%, transparent 55%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── HERO ───────────────────────────────────────────────────────────── */
    .hero-container {
        position: relative;
        border-radius: var(--radius-xl);
        padding: 3rem 2.5rem 2.5rem;
        margin-bottom: 2rem;
        overflow: hidden;
        background: var(--surface-1);
        border: 1px solid var(--rim);
        isolation: isolate;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        inset: 0;
        background:
            radial-gradient(ellipse 90% 60% at 50% 0%, rgba(109,90,205,0.18) 0%, transparent 65%),
            radial-gradient(ellipse 60% 40% at 0% 100%, rgba(45,212,191,0.07) 0%, transparent 50%),
            radial-gradient(ellipse 40% 60% at 100% 60%, rgba(244,114,182,0.05) 0%, transparent 50%);
        z-index: -1;
    }
    .hero-container::after {
        content: '';
        position: absolute;
        top: 0;
        left: 15%;
        right: 15%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(109,90,205,0.6), rgba(45,212,191,0.4), transparent);
    }

    .hero-icon {
        display: block;
        text-align: center;
        font-size: 3.5rem;
        margin-bottom: 0.75rem;
        animation: levitate 4s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(109,90,205,0.5));
    }
    @keyframes levitate {
        0%, 100% { transform: translateY(0) rotate(-2deg); }
        50%       { transform: translateY(-10px) rotate(2deg); }
    }

    .hero-title {
        font-family: var(--font-display) !important;
        font-size: clamp(2.5rem, 5vw, 3.8rem) !important;
        font-weight: 800 !important;
        text-align: center;
        letter-spacing: -1.5px;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        background: linear-gradient(140deg,
            #c4b5fd 0%,
            #818cf8 20%,
            #a5f3fc 50%,
            #c084fc 75%,
            #f9a8d4 100%);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: flow 6s ease infinite;
    }
    @keyframes flow {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .hero-subtitle {
        text-align: center;
        color: var(--text-2);
        font-size: 1.05rem;
        font-weight: 300;
        margin-top: 0.8rem;
        letter-spacing: 0.5px;
    }

    .hero-badge {
        display: inline-block;
        border: 1px solid rgba(109,90,205,0.3);
        background: rgba(109,90,205,0.1);
        border-radius: 100px;
        padding: 0.35rem 1.1rem;
        font-size: 0.68rem;
        color: var(--teal);
        letter-spacing: 2.5px;
        text-transform: uppercase;
        font-weight: 600;
        font-family: var(--font-mono);
        margin-top: 1.2rem;
        backdrop-filter: blur(10px);
    }

    /* ── SIDEBAR ────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--surface-0) !important;
        border-right: 1px solid var(--rim) !important;
    }

    .sidebar-logo {
        text-align: center;
        padding: 0.5rem 0 1.2rem;
    }
    .sidebar-logo-icon {
        font-size: 2.2rem;
        display: block;
        filter: drop-shadow(0 0 12px rgba(109,90,205,0.6));
        animation: levitate 4s ease-in-out infinite;
    }
    .sidebar-logo-name {
        font-family: var(--font-display);
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #c4b5fd, #a5f3fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 0.4rem;
    }
    .sidebar-logo-sub {
        font-family: var(--font-mono);
        font-size: 0.58rem;
        color: var(--text-3);
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-top: 0.25rem;
    }

    .sidebar-section {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        font-weight: 500;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.9rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--rim);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Stat cards in sidebar */
    .vault-stat-big {
        background: var(--surface-2);
        border: 1px solid var(--rim);
        border-radius: var(--radius-md);
        padding: 1.3rem 1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: border-color 0.3s ease, transform 0.3s ease;
        margin-bottom: 0.7rem;
    }
    .vault-stat-big::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(109,90,205,0.5), transparent);
    }
    .vault-stat-big:hover {
        border-color: rgba(109,90,205,0.25);
        transform: translateY(-2px);
    }
    .stat-glyph {
        font-size: 1.6rem;
        margin-bottom: 0.35rem;
        line-height: 1;
    }
    .stat-num {
        font-family: var(--font-display);
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1;
        background: linear-gradient(135deg, #c4b5fd, #a5f3fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-lbl {
        font-family: var(--font-mono);
        font-size: 0.6rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--text-3);
        margin-top: 0.25rem;
    }
    .stat-pair {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.6rem;
    }
    .vault-stat-sm {
        background: var(--surface-2);
        border: 1px solid var(--rim);
        border-radius: var(--radius-sm);
        padding: 0.9rem 0.7rem;
        text-align: center;
        transition: border-color 0.3s;
    }
    .vault-stat-sm:hover { border-color: rgba(109,90,205,0.2); }
    .stat-sm-num {
        font-family: var(--font-display);
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-1);
        line-height: 1;
    }
    .stat-sm-lbl {
        font-family: var(--font-mono);
        font-size: 0.58rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-3);
        margin-top: 0.2rem;
    }

    /* Offline warning */
    .backend-offline {
        text-align: center;
        color: var(--text-3);
        font-size: 0.78rem;
        padding: 1.2rem;
        background: var(--surface-1);
        border: 1px solid rgba(251,191,36,0.15);
        border-radius: var(--radius-sm);
        font-family: var(--font-mono);
    }

    /* Divider */
    .premium-divider {
        height: 1px;
        background: var(--rim);
        margin: 1.3rem 0;
        border: none;
    }

    /* Sidebar footer */
    .sidebar-footer {
        text-align: center;
        padding: 1rem 0 0.5rem;
    }
    .sidebar-footer-title {
        font-family: var(--font-mono);
        font-size: 0.58rem;
        color: var(--text-3);
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .sidebar-footer-ver {
        font-family: var(--font-mono);
        font-size: 0.52rem;
        color: rgba(232,232,240,0.15);
        margin-top: 0.3rem;
    }

    /* ── TABS ────────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem !important;
        background: var(--surface-1) !important;
        border: 1px solid var(--rim) !important;
        border-radius: var(--radius-md) !important;
        padding: 0.35rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: var(--font-body) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--text-2) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.6rem 1.3rem !important;
        transition: all 0.25s ease !important;
        border: 1px solid transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-1) !important;
        background: var(--surface-2) !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--surface-3) !important;
        color: var(--text-1) !important;
        border-color: var(--rim-bright) !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05) !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* ── CHAT INPUT ─────────────────────────────────────────────────────── */
    .stChatInput > div {
        background: var(--surface-1) !important;
        border: 1px solid var(--rim-bright) !important;
        border-radius: var(--radius-lg) !important;
        transition: border-color 0.3s, box-shadow 0.3s !important;
    }
    .stChatInput > div:focus-within {
        border-color: rgba(109,90,205,0.45) !important;
        box-shadow: 0 0 0 3px rgba(109,90,205,0.08), 0 4px 20px rgba(0,0,0,0.2) !important;
    }
    .stChatInput textarea {
        font-family: var(--font-body) !important;
        color: var(--text-1) !important;
        font-size: 0.95rem !important;
    }
    .stChatInput textarea::placeholder { color: var(--text-3) !important; }

    /* ── QUERY INFO BOX ─────────────────────────────────────────────────── */
    .query-info {
        background: var(--surface-1);
        border: 1px solid var(--rim);
        border-left: 2px solid var(--iris);
        border-radius: var(--radius-md);
        padding: 1rem 1.4rem;
        margin: 1.2rem 0 1.8rem;
        position: relative;
        overflow: hidden;
    }
    .query-info::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(109,90,205,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .query-text {
        font-family: var(--font-display);
        color: var(--text-1);
        font-size: 1rem;
        font-weight: 600;
    }
    .query-refined {
        color: var(--teal);
        font-size: 0.78rem;
        margin-top: 0.35rem;
        font-style: italic;
        font-family: var(--font-body);
    }
    .query-count {
        color: var(--text-3);
        font-size: 0.72rem;
        font-family: var(--font-mono);
        margin-top: 0.4rem;
        letter-spacing: 0.5px;
    }

    /* ── RESULT CARDS ───────────────────────────────────────────────────── */
    .result-card {
        background: var(--surface-1);
        border: 1px solid var(--rim);
        border-radius: var(--radius-lg);
        padding: 1.3rem;
        margin-bottom: 1.3rem;
        transition: border-color 0.35s ease, transform 0.35s ease, box-shadow 0.35s ease;
        position: relative;
        overflow: hidden;
        isolation: isolate;
    }
    .result-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(109,90,205,0.3), transparent);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .result-card:hover {
        border-color: rgba(109,90,205,0.3);
        transform: translateY(-5px);
        box-shadow: 0 20px 50px rgba(0,0,0,0.4), 0 0 40px rgba(109,90,205,0.05);
    }
    .result-card:hover::before { opacity: 1; }

    /* Card inner glow on hover */
    .result-card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(109,90,205,0.04) 0%, transparent 65%);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.35s;
        z-index: -1;
    }
    .result-card:hover::after { opacity: 1; }

    /* Score badge */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.28rem 0.85rem;
        border-radius: 100px;
        font-family: var(--font-mono);
        font-size: 0.73rem;
        font-weight: 500;
        margin-bottom: 0.9rem;
        letter-spacing: 0.3px;
    }
    .score-high {
        background: rgba(52,211,153,0.08);
        border: 1px solid rgba(52,211,153,0.22);
        color: var(--emerald);
    }
    .score-mid {
        background: rgba(251,191,36,0.08);
        border: 1px solid rgba(251,191,36,0.22);
        color: var(--amber);
    }
    .score-low {
        background: rgba(248,113,113,0.08);
        border: 1px solid rgba(248,113,113,0.18);
        color: #f87171;
    }

    /* Doc icon */
    .doc-icon-container {
        background: var(--surface-2);
        border: 1px solid var(--rim);
        border-radius: var(--radius-md);
        padding: 1.6rem 1rem;
        text-align: center;
        margin-bottom: 0.6rem;
        transition: border-color 0.3s;
    }
    .result-card:hover .doc-icon-container {
        border-color: rgba(109,90,205,0.2);
    }
    .doc-icon { font-size: 3rem; line-height: 1; }
    .doc-ext {
        font-family: var(--font-mono);
        font-size: 0.65rem;
        color: var(--text-3);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 0.4rem;
    }

    /* File name */
    .result-filename {
        font-family: var(--font-display);
        font-weight: 600;
        font-size: 0.88rem;
        color: var(--text-1);
        margin-bottom: 0.5rem;
        line-height: 1.4;
        word-break: break-word;
    }

    /* Progress bar override */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--iris), var(--teal)) !important;
        border-radius: 10px !important;
        height: 5px !important;
    }
    .stProgress > div > div > div {
        height: 5px !important;
        background: var(--surface-3) !important;
        border-radius: 10px !important;
    }

    /* Tags */
    .tags-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-top: 0.65rem;
    }
    .result-tag {
        background: rgba(109,90,205,0.1);
        color: #c4b5fd;
        border: 1px solid rgba(109,90,205,0.2);
        border-radius: 100px;
        padding: 0.2rem 0.65rem;
        font-size: 0.63rem;
        font-family: var(--font-mono);
        letter-spacing: 0.3px;
        transition: background 0.2s, border-color 0.2s;
        cursor: default;
    }
    .result-tag:hover {
        background: rgba(109,90,205,0.2);
        border-color: rgba(109,90,205,0.4);
    }

    /* Text preview */
    .text-preview {
        background: var(--surface-2);
        border: 1px solid var(--rim);
        border-radius: var(--radius-sm);
        padding: 0.75rem 0.9rem;
        font-size: 0.73rem;
        color: var(--text-2);
        max-height: 90px;
        overflow: hidden;
        line-height: 1.65;
        font-family: var(--font-body);
        margin-top: 0.6rem;
        position: relative;
    }
    .text-preview::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 30px;
        background: linear-gradient(transparent, var(--surface-2));
    }

    /* Meta row */
    .result-meta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-3);
        font-size: 0.7rem;
        font-family: var(--font-mono);
        margin-top: 0.7rem;
    }
    .meta-dot {
        width: 3px;
        height: 3px;
        background: var(--text-3);
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* GPS */
    .gps-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(52,211,153,0.07);
        border: 1px solid rgba(52,211,153,0.15);
        color: var(--emerald);
        border-radius: 100px;
        padding: 0.15rem 0.55rem;
        font-size: 0.63rem;
        font-family: var(--font-mono);
        margin-top: 0.4rem;
    }

    /* ── SURPRISE CARD ─────────────────────────────────────────────────── */
    .surprise-card {
        background: var(--surface-1);
        border: 1px solid rgba(244,114,182,0.18);
        border-radius: var(--radius-xl);
        padding: 3rem 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        margin-bottom: 2rem;
        isolation: isolate;
    }
    .surprise-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse 70% 50% at 50% 0%, rgba(244,114,182,0.07) 0%, transparent 65%);
        z-index: -1;
    }
    .surprise-card::after {
        content: '';
        position: absolute;
        top: -1px;
        left: 20%; right: 20%;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--rose), transparent);
    }
    .surprise-emoji {
        font-size: 4rem;
        animation: levitate 2s ease-in-out infinite;
        display: block;
        filter: drop-shadow(0 0 15px rgba(244,114,182,0.4));
    }

    /* ── EMPTY STATE ───────────────────────────────────────────────────── */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--text-3);
    }
    .empty-icon {
        font-size: 4.5rem;
        margin-bottom: 1.2rem;
        display: block;
        opacity: 0.45;
    }
    .empty-text {
        font-family: var(--font-display);
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-2);
        margin-bottom: 0.5rem;
    }
    .empty-hint {
        font-size: 0.82rem;
        color: var(--text-3);
        font-family: var(--font-body);
        max-width: 300px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* ── BUTTONS ───────────────────────────────────────────────────────── */
    .stButton > button {
        font-family: var(--font-body) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.3px !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6d5acd, #5b21b6) !important;
        border: 1px solid rgba(109,90,205,0.4) !important;
        color: #fff !important;
        box-shadow: 0 4px 14px rgba(109,90,205,0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(109,90,205,0.35) !important;
        background: linear-gradient(135deg, #7c6ade, #6d28d9) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* ── SELECTBOX / SLIDER ────────────────────────────────────────────── */
    .stSelectbox label, .stSlider label {
        font-family: var(--font-body) !important;
        font-size: 0.82rem !important;
        color: var(--text-2) !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        background: var(--surface-2) !important;
        border-color: var(--rim-bright) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-1) !important;
        font-family: var(--font-body) !important;
    }
    .stSelectbox [data-baseweb="select"] > div:hover {
        border-color: rgba(109,90,205,0.35) !important;
    }
    .stSlider > div > div > div {
        background: linear-gradient(90deg, var(--iris), var(--teal)) !important;
    }

    /* ── IMAGE BORDER RADIUS ───────────────────────────────────────────── */
    .result-card img, .stImage img {
        border-radius: var(--radius-md) !important;
    }

    /* ── PLOTLY CHARTS ─────────────────────────────────────────────────── */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }

    /* ── ANIMATIONS ────────────────────────────────────────────────────── */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .animate-in {
        animation: fadeUp 0.4s ease both;
    }
    .animate-in:nth-child(2)  { animation-delay: 0.06s; }
    .animate-in:nth-child(3)  { animation-delay: 0.12s; }
    .animate-in:nth-child(4)  { animation-delay: 0.18s; }
    .animate-in:nth-child(5)  { animation-delay: 0.24s; }
    .animate-in:nth-child(6)  { animation-delay: 0.30s; }

    /* ── SIDEBAR LABEL OVERRIDES ───────────────────────────────────────── */
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label {
        color: var(--text-2) !important;
        font-size: 0.78rem !important;
        font-family: var(--font-body) !important;
    }

    /* ── SCROLLBAR ─────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--void); }
    ::-webkit-scrollbar-thumb {
        background: var(--surface-3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(109,90,205,0.4); }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# VAULT SPLASH SCREEN (Pure CSS — no JS required)
# =============================================================================

st.markdown("""
<style>
    /* ── Splash Overlay ─────────────────────────────────────────────── */
    .vault-splash {
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #050508;
        animation: splashVanish 0.01s linear 3.8s forwards;
    }

    @keyframes splashVanish {
        to { visibility: hidden; z-index: -1; }
    }

    /* Fade-out layer */
    .splash-fade {
        position: absolute;
        inset: 0;
        background: transparent;
        opacity: 1;
        animation: fadeAway 0.7s ease 3.0s forwards;
        pointer-events: none;
        z-index: 100;
    }
    @keyframes fadeAway {
        to { opacity: 0; }
    }

    /* ── Vault Doors ──────────────────────────────────────────────── */
    .v-doors { position: absolute; inset: 0; overflow: hidden; }

    .v-door {
        position: absolute;
        top: 0;
        width: 50%;
        height: 100%;
    }

    .v-door--l {
        left: 0;
        background:
            linear-gradient(135deg, #0e0e1e 0%, #141428 50%, #1a1a34 100%);
        border-right: 1px solid rgba(109,90,205,0.12);
        box-shadow: inset -40px 0 80px rgba(0,0,0,0.6);
        animation: doorL 1.1s cubic-bezier(0.7, 0, 0.3, 1) 1.9s forwards;
    }
    .v-door--r {
        right: 0;
        background:
            linear-gradient(225deg, #0e0e1e 0%, #141428 50%, #1a1a34 100%);
        border-left: 1px solid rgba(109,90,205,0.12);
        box-shadow: inset 40px 0 80px rgba(0,0,0,0.6);
        animation: doorR 1.1s cubic-bezier(0.7, 0, 0.3, 1) 1.9s forwards;
    }

    @keyframes doorL {
        to { transform: translateX(-110%); }
    }
    @keyframes doorR {
        to { transform: translateX(110%); }
    }

    /* Door bolts */
    .v-bolts {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        display: flex;
        flex-direction: column;
        gap: 22px;
    }
    .v-door--l .v-bolts { right: 24px; }
    .v-door--r .v-bolts { left: 24px; }

    .v-bolt {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: rgba(109,90,205,0.18);
        box-shadow: 0 0 4px rgba(109,90,205,0.1);
    }

    /* Door panel inset */
    .v-panel {
        position: absolute;
        top: 12%;
        height: 76%;
        width: 50%;
        border: 1px solid rgba(255,255,255,0.025);
        border-radius: 6px;
        background: rgba(255,255,255,0.008);
    }
    .v-door--l .v-panel { right: 44px; }
    .v-door--r .v-panel { left: 44px; }

    /* ── Center Lock ──────────────────────────────────────────────── */
    .v-lock {
        position: relative;
        z-index: 50;
        display: flex;
        flex-direction: column;
        align-items: center;
        animation: lockShrink 0.35s ease 1.75s forwards;
    }
    @keyframes lockShrink {
        to { opacity: 0; transform: scale(0.7); }
    }

    /* Spinning dial */
    .v-dial {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        border: 2.5px solid rgba(109,90,205,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle, #0f0f20 0%, #0a0a14 100%);
        box-shadow:
            0 0 50px rgba(109,90,205,0.12),
            0 0 100px rgba(109,90,205,0.04),
            inset 0 0 40px rgba(0,0,0,0.5);
        animation: spin 1.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        position: relative;
    }

    @keyframes spin {
        0%   { transform: rotate(0deg);   }
        20%  { transform: rotate(240deg); }
        40%  { transform: rotate(100deg); }
        60%  { transform: rotate(310deg); }
        80%  { transform: rotate(200deg); }
        100% { transform: rotate(360deg); }
    }

    /* Dial ticks via conic gradient */
    .v-ticks {
        position: absolute;
        inset: 5px;
        border-radius: 50%;
        border: 1px solid rgba(109,90,205,0.08);
        background: conic-gradient(
            from 0deg,
            transparent 0deg,   rgba(109,90,205,0.18) 2deg, transparent 4deg,
            transparent 30deg,  rgba(109,90,205,0.18) 32deg, transparent 34deg,
            transparent 60deg,  rgba(109,90,205,0.18) 62deg, transparent 64deg,
            transparent 90deg,  rgba(109,90,205,0.18) 92deg, transparent 94deg,
            transparent 120deg, rgba(109,90,205,0.18) 122deg, transparent 124deg,
            transparent 150deg, rgba(109,90,205,0.18) 152deg, transparent 154deg,
            transparent 180deg, rgba(109,90,205,0.18) 182deg, transparent 184deg,
            transparent 210deg, rgba(109,90,205,0.18) 212deg, transparent 214deg,
            transparent 240deg, rgba(109,90,205,0.18) 242deg, transparent 244deg,
            transparent 270deg, rgba(109,90,205,0.18) 272deg, transparent 274deg,
            transparent 300deg, rgba(109,90,205,0.18) 302deg, transparent 304deg,
            transparent 330deg, rgba(109,90,205,0.18) 332deg, transparent 334deg
        );
        pointer-events: none;
    }

    /* Dial pointer at top */
    .v-pointer {
        position: absolute;
        top: -3px;
        left: 50%;
        transform: translateX(-50%);
        width: 3px;
        height: 16px;
        background: #2dd4bf;
        border-radius: 2px;
        box-shadow: 0 0 10px rgba(45,212,191,0.7);
    }

    /* Brain emblem */
    .v-brain {
        font-size: 3rem;
        z-index: 2;
        filter: drop-shadow(0 0 18px rgba(109,90,205,0.55));
        animation: pulse 1.2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50%      { transform: scale(1.1); }
    }

    /* Status text */
    .v-status {
        margin-top: 1.4rem;
        font-family: 'DM Mono', var(--font-mono, monospace);
        font-size: 0.7rem;
        letter-spacing: 3.5px;
        text-transform: uppercase;
        color: rgba(109,90,205,0.55);
        animation: blink 0.7s ease-in-out infinite alternate;
    }
    @keyframes blink {
        from { opacity: 0.4; }
        to   { opacity: 1; }
    }

    /* ── Light burst when doors open ──────────────────────────────── */
    .v-burst {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: radial-gradient(circle,
            rgba(109,90,205,0.3) 0%,
            rgba(45,212,191,0.12) 35%,
            transparent 65%
        );
        transform: translate(-50%, -50%);
        animation: burst 0.9s ease-out 1.9s forwards;
        z-index: 20;
        pointer-events: none;
    }
    @keyframes burst {
        0%   { width: 0; height: 0; opacity: 1; }
        50%  { opacity: 0.5; }
        100% { width: 280vmax; height: 280vmax; opacity: 0; }
    }

    /* ── Center light seam ────────────────────────────────────────── */
    .v-seam {
        position: absolute;
        top: 0;
        left: 50%;
        width: 1px;
        height: 100%;
        transform: translateX(-50%);
        background: linear-gradient(180deg,
            transparent 5%,
            rgba(109,90,205,0.35) 25%,
            rgba(45,212,191,0.25) 50%,
            rgba(109,90,205,0.35) 75%,
            transparent 95%
        );
        z-index: 15;
        opacity: 0;
        animation: seamGlow 0.25s ease 1.8s forwards, seamSpread 0.9s ease 1.9s forwards;
    }
    @keyframes seamGlow { to { opacity: 1; } }
    @keyframes seamSpread {
        0%   { width: 1px; opacity: 1; }
        40%  { width: 20px; opacity: 0.7; }
        100% { width: 100vw; opacity: 0; }
    }

    /* ── Spark particles ──────────────────────────────────────────── */
    .v-sparks {
        position: absolute;
        top: 50%; left: 50%;
        z-index: 30;
        pointer-events: none;
    }
    .v-sp {
        position: absolute;
        width: 3px; height: 3px;
        border-radius: 50%;
        background: #2dd4bf;
        box-shadow: 0 0 5px rgba(45,212,191,0.8);
        opacity: 0;
    }
    .v-sp:nth-child(1)  { animation: fly 0.65s ease-out 1.92s forwards; --tx:-110px; --ty:-70px; }
    .v-sp:nth-child(2)  { animation: fly 0.65s ease-out 1.96s forwards; --tx:95px;  --ty:-90px;  background:#c4b5fd; box-shadow:0 0 5px rgba(196,181,253,0.8); }
    .v-sp:nth-child(3)  { animation: fly 0.65s ease-out 2.00s forwards; --tx:-75px; --ty:100px; }
    .v-sp:nth-child(4)  { animation: fly 0.65s ease-out 1.98s forwards; --tx:120px; --ty:60px;   background:#f472b6; box-shadow:0 0 5px rgba(244,114,182,0.8); }
    .v-sp:nth-child(5)  { animation: fly 0.65s ease-out 1.94s forwards; --tx:-140px;--ty:15px;   background:#c4b5fd; box-shadow:0 0 5px rgba(196,181,253,0.8); }
    .v-sp:nth-child(6)  { animation: fly 0.65s ease-out 2.02s forwards; --tx:50px;  --ty:-120px; }
    .v-sp:nth-child(7)  { animation: fly 0.65s ease-out 1.97s forwards; --tx:-35px; --ty:130px;  background:#fbbf24; box-shadow:0 0 5px rgba(251,191,36,0.8); }
    .v-sp:nth-child(8)  { animation: fly 0.65s ease-out 2.01s forwards; --tx:130px; --ty:-25px;  background:#f472b6; box-shadow:0 0 5px rgba(244,114,182,0.8); }
    .v-sp:nth-child(9)  { animation: fly 0.65s ease-out 1.95s forwards; --tx:-60px; --ty:-120px; background:#fbbf24; box-shadow:0 0 5px rgba(251,191,36,0.8); }
    .v-sp:nth-child(10) { animation: fly 0.65s ease-out 2.03s forwards; --tx:80px;  --ty:110px; }

    @keyframes fly {
        0%   { opacity: 1; transform: translate(0,0) scale(1.2); }
        100% { opacity: 0; transform: translate(var(--tx), var(--ty)) scale(0); }
    }
</style>
""", unsafe_allow_html=True)

# Splash screen HTML — no HTML comments (Streamlit renders them as text)
st.markdown('<div class="vault-splash">'
    '<div class="splash-fade"></div>'
    '<div class="v-doors">'
        '<div class="v-door v-door--l"><div class="v-panel"></div><div class="v-bolts">'
            '<div class="v-bolt"></div><div class="v-bolt"></div><div class="v-bolt"></div>'
            '<div class="v-bolt"></div><div class="v-bolt"></div><div class="v-bolt"></div>'
            '<div class="v-bolt"></div></div></div>'
        '<div class="v-door v-door--r"><div class="v-panel"></div><div class="v-bolts">'
            '<div class="v-bolt"></div><div class="v-bolt"></div><div class="v-bolt"></div>'
            '<div class="v-bolt"></div><div class="v-bolt"></div><div class="v-bolt"></div>'
            '<div class="v-bolt"></div></div></div>'
    '</div>'
    '<div class="v-seam"></div>'
    '<div class="v-burst"></div>'
    '<div class="v-sparks">'
        '<div class="v-sp"></div><div class="v-sp"></div><div class="v-sp"></div>'
        '<div class="v-sp"></div><div class="v-sp"></div><div class="v-sp"></div>'
        '<div class="v-sp"></div><div class="v-sp"></div><div class="v-sp"></div>'
        '<div class="v-sp"></div>'
    '</div>'
    '<div class="v-lock">'
        '<div class="v-dial"><div class="v-ticks"></div><div class="v-pointer"></div>'
            '<span class="v-brain">\U0001f9e0</span></div>'
        '<div class="v-status">Unlocking Vault&#8230;</div>'
    '</div>'
'</div>', unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def api_get(endpoint: str) -> Dict[str, Any]:
    """Make a GET request to the backend API."""
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {}
    except Exception as e:
        return {}


def api_post(endpoint: str, data: Dict) -> Dict[str, Any]:
    """Make a POST request to the backend API."""
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {}
    except Exception as e:
        return {}


def format_file_size(size_bytes) -> str:
    """Format bytes into human-readable size."""
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "—"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_score_class(score: float) -> str:
    """Return CSS class based on match score."""
    if score >= 60:
        return "score-high"
    elif score >= 30:
        return "score-mid"
    return "score-low"


def get_score_icon(score: float) -> str:
    """Return emoji based on match score."""
    if score >= 60:
        return "🟢"
    elif score >= 30:
        return "🟡"
    return "🔴"


def render_result_card(result: Dict, col):
    """Render a single search result as a premium styled card."""
    meta = result.get("metadata", {})
    score = result.get("match_percentage", 0)
    file_path = meta.get("file_path", "")
    file_name = meta.get("file_name", "Unknown")
    file_type = meta.get("file_type", "document")
    file_ext = meta.get("file_extension", "")
    auto_tags = meta.get("auto_tags", "")
    text_preview = result.get("text_preview", "")

    with col:
        st.markdown(f'<div class="result-card animate-in">', unsafe_allow_html=True)

        # Score badge
        score_class = get_score_class(score)
        score_icon = get_score_icon(score)
        st.markdown(
            f'<span class="score-badge {score_class}">{score_icon} {score}% match</span>',
            unsafe_allow_html=True,
        )

        # Thumbnail or document icon
        if file_type == "image" and file_path and Path(file_path).exists():
            try:
                st.image(file_path, use_container_width=True)
            except Exception:
                st.markdown(
                    '<div class="doc-icon-container"><div class="doc-icon">🖼️</div><div class="doc-ext">image</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            icons = {".pdf": "📄", ".txt": "📝", ".docx": "📃", ".md": "📑"}
            icon = icons.get(file_ext, "📁")
            ext_label = file_ext.replace(".", "").upper() if file_ext else "FILE"
            st.markdown(
                f'<div class="doc-icon-container"><div class="doc-icon">{icon}</div><div class="doc-ext">{ext_label}</div></div>',
                unsafe_allow_html=True,
            )

        # File name
        st.markdown(f'<div class="result-filename">{file_name}</div>', unsafe_allow_html=True)

        # Progress bar
        st.progress(min(score / 100, 1.0))

        # Tags
        if auto_tags:
            tags_html = '<div class="tags-container">'
            for tag in auto_tags.split(",")[:5]:
                tags_html += f'<span class="result-tag">{tag.strip()}</span>'
            tags_html += '</div>'
            st.markdown(tags_html, unsafe_allow_html=True)

        # Text preview for documents
        if text_preview and file_type == "document":
            preview = text_preview[:180] + "..." if len(text_preview) > 180 else text_preview
            st.markdown(f'<div class="text-preview">{preview}</div>', unsafe_allow_html=True)

        # Metadata line
        size_str = format_file_size(meta.get("file_size_bytes", 0))
        modified = str(meta.get("modified_date", ""))[:10]
        st.markdown(
            f'<div class="result-meta">'
            f'<span>📏 {size_str}</span>'
            f'<span class="meta-dot"></span>'
            f'<span>📅 {modified}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # GPS info
        if meta.get("gps_latitude"):
            st.markdown(
                f'<div class="gps-badge">📍 {meta["gps_latitude"]}, {meta["gps_longitude"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        <span class="sidebar-logo-icon">🧠</span>
        <div class="sidebar-logo-name">LifeVault</div>
        <div class="sidebar-logo-sub">Memory Engine</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

    # Search Settings
    st.markdown('<div class="sidebar-section">⚙️ Search Settings</div>', unsafe_allow_html=True)

    search_type = st.selectbox(
        "Search scope",
        ["all", "images", "documents"],
        format_func=lambda x: {
            "all": "🔍  All Files",
            "images": "🖼️  Images Only",
            "documents": "📄  Documents Only",
        }[x],
        label_visibility="collapsed",
    )

    top_k = st.slider("Max results", min_value=3, max_value=30, value=9, step=3)

    st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

    # Vault Stats
    stats = api_get("/api/stats")
    if stats:
        st.markdown('<div class="sidebar-section">📊 Vault Stats</div>', unsafe_allow_html=True)

        total = stats.get('total_files', 0)
        images = stats.get('total_images', 0)
        docs = stats.get('total_documents', 0)

        st.markdown(f"""
        <div class="vault-stat-big">
            <div class="stat-glyph">💎</div>
            <div class="stat-num">{total}</div>
            <div class="stat-lbl">Total Memories</div>
        </div>
        <div class="stat-pair">
            <div class="vault-stat-sm">
                <div style="font-size:1.2rem; line-height:1;">🖼️</div>
                <div class="stat-sm-num">{images}</div>
                <div class="stat-sm-lbl">Images</div>
            </div>
            <div class="vault-stat-sm">
                <div style="font-size:1.2rem; line-height:1;">📄</div>
                <div class="stat-sm-num">{docs}</div>
                <div class="stat-sm-lbl">Docs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="backend-offline">⚠️ Backend offline</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

    # Surprise Me
    st.markdown('<div class="sidebar-section">🎲 Random Memory</div>', unsafe_allow_html=True)
    if st.button("✨  Surprise Me!", use_container_width=True, type="primary"):
        st.session_state["surprise_mode"] = True

    st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="sidebar-footer">
        <div class="sidebar-footer-title">VIT–SanDisk Hackathon 2026</div>
        <div class="sidebar-footer-ver">v1.0.0 · All data stored locally</div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN CONTENT
# =============================================================================

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <span class="hero-icon">🧠</span>
    <h1 class="hero-title">LifeVault</h1>
    <div class="hero-subtitle">Your AI-Powered Personal Memory Vault</div>
    <div style="text-align: center;">
        <span class="hero-badge">🔐 100% On-Device · Private · Intelligent</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_search, tab_timeline, tab_explore = st.tabs([
    "🔍  Search Memories",
    "📈  Timeline Analytics",
    "🗂️  Explore Vault",
])


# =============================================================================
# TAB 1: SEARCH
# =============================================================================

with tab_search:
    # ── Surprise Me ──────────────────────────────────────────────────────────
    if st.session_state.get("surprise_mode"):
        st.session_state["surprise_mode"] = False
        surprise_data = api_get("/api/surprise")
        if surprise_data and "memory" in surprise_data:
            memory = surprise_data["memory"]
            st.markdown('<div class="surprise-card animate-in">', unsafe_allow_html=True)
            st.markdown('<span class="surprise-emoji">🎲</span>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-family: var(--font-display); font-size: 1.35rem; font-weight: 700; '
                'color: var(--text-1); margin: 0.6rem 0 0.4rem;">A Random Memory From Your Vault</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="premium-divider"></div>', unsafe_allow_html=True)

            file_path = memory.get("file_path", "")
            file_name = memory.get("file_name", "Unknown")
            file_type = memory.get("file_type", "")

            col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
            with col_s2:
                if file_type == "image" and file_path and Path(file_path).exists():
                    st.image(file_path, caption=file_name, use_container_width=True)
                else:
                    st.markdown(f"### 📄 {file_name}")
                    if memory.get("_document_preview"):
                        st.markdown(f"> {memory['_document_preview'][:500]}")

                tags = memory.get("auto_tags", "")
                if tags:
                    tags_html = '<div class="tags-container" style="justify-content: center;">'
                    for t in tags.split(",")[:5]:
                        tags_html += f'<span class="result-tag">{t.strip()}</span>'
                    tags_html += '</div>'
                    st.markdown(tags_html, unsafe_allow_html=True)

                st.markdown(
                    f'<div class="result-meta" style="justify-content: center; margin-top: 1rem;">'
                    f'<span>📅 {memory.get("modified_date", "N/A")[:10]}</span>'
                    f'<span class="meta-dot"></span>'
                    f'<span>📏 {format_file_size(memory.get("file_size_bytes", 0))}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="empty-state">'
                '<span class="empty-icon">📭</span>'
                '<div class="empty-text">No memories yet!</div>'
                '<div class="empty-hint">Add some files to your vault folder to get started.</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ── Search Input ─────────────────────────────────────────────────────────
    query = st.chat_input(
        "Search your memories… e.g. 'sunset photos', 'cooking recipes', 'notes from workshop'"
    )

    if query:
        with st.spinner("🔍 Searching your memories..."):
            response = api_post("/api/search", {
                "query": query,
                "top_k": top_k,
                "search_type": search_type,
            })

        if response and response.get("results"):
            results = response["results"]
            refined = response.get("refined_query", query)
            intent = response.get("intent", {})

            # Query info
            info_html = f'<div class="query-info animate-in">'
            info_html += f'<div class="query-text">🔍 &quot;{query}&quot;</div>'
            if refined and refined != query:
                info_html += f'<div class="query-refined">🤖 Gemini refined → &quot;{refined}&quot;</div>'
            if intent.get("tags"):
                tags_str = ", ".join(intent["tags"])
                info_html += f'<div class="query-refined">🏷️ Tags: {tags_str}</div>'
            info_html += f'<div class="query-count">Found {len(results)} matching memories</div>'
            info_html += '</div>'
            st.markdown(info_html, unsafe_allow_html=True)

            # 3-column grid
            cols = st.columns(3)
            for i, result in enumerate(results):
                render_result_card(result, cols[i % 3])

        elif response is not None:
            st.markdown(
                '<div class="empty-state animate-in">'
                '<span class="empty-icon">🔍</span>'
                '<div class="empty-text">No results found</div>'
                '<div class="empty-hint">Try a different query or broaden your search.</div>'
                '</div>',
                unsafe_allow_html=True,
            )


# =============================================================================
# TAB 2: TIMELINE ANALYTICS
# =============================================================================

with tab_timeline:
    all_files_data = api_get("/api/all-files")
    if all_files_data and all_files_data.get("files"):
        files_data = all_files_data["files"]

        timeline_data = []
        for f in files_data:
            mod_date = f.get("modified_date", "")
            if mod_date and len(mod_date) >= 10:
                try:
                    dt = datetime.fromisoformat(mod_date[:19])
                    timeline_data.append({
                        "date": dt,
                        "file_name": f.get("file_name", "Unknown"),
                        "file_type": f.get("file_type", "other"),
                        "file_size": f.get("file_size_bytes", 0),
                    })
                except Exception:
                    pass

        if timeline_data:
            df = pd.DataFrame(timeline_data)

            st.markdown(
                '<div class="query-info">'
                '<div class="query-text">📈 Memory Timeline</div>'
                '<div class="query-count">Visualize when your memories were created</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            # Histogram
            fig_hist = px.histogram(
                df, x="date", color="file_type",
                labels={"date": "", "count": "Files", "file_type": "Type"},
                color_discrete_map={"image": "#6d5acd", "document": "#2dd4bf"},
                barmode="stack",
            )
            fig_hist.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="rgba(232,232,240,0.45)", family="DM Sans"),
                title=dict(
                    text="Files Over Time",
                    font=dict(size=15, color="rgba(232,232,240,0.6)", family="Syne"),
                ),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="rgba(232,232,240,0.45)")),
                xaxis=dict(gridcolor="rgba(255,255,255,0.03)", showline=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.03)", showline=False),
                margin=dict(l=20, r=20, t=50, b=20),
                bargap=0.15,
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            col_c1, col_c2 = st.columns(2)

            with col_c1:
                type_counts = df["file_type"].value_counts()
                fig_pie = go.Figure(data=[go.Pie(
                    labels=type_counts.index,
                    values=type_counts.values,
                    hole=0.6,
                    marker=dict(colors=["#6d5acd", "#2dd4bf", "#f472b6"]),
                    textfont=dict(color="rgba(232,232,240,0.7)", size=11, family="DM Mono"),
                    textinfo="label+percent",
                )])
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="rgba(232,232,240,0.45)", family="DM Sans"),
                    title=dict(text="File Types", font=dict(size=13, color="rgba(232,232,240,0.55)", family="Syne")),
                    legend=dict(bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_c2:
                try:
                    size_by_type = df.groupby("file_type")["file_size"].sum().reset_index()
                    size_by_type.columns = ["Type", "Size"]
                    size_by_type["Size_MB"] = size_by_type["Size"] / (1024 * 1024)
                    fig_bar = go.Figure(data=[go.Bar(
                        x=size_by_type["Type"],
                        y=size_by_type["Size_MB"],
                        marker=dict(color=["#6d5acd", "#2dd4bf"], cornerradius=8),
                        text=size_by_type["Size_MB"].apply(lambda x: f"{x:.1f} MB"),
                        textposition="outside",
                        textfont=dict(color="rgba(232,232,240,0.5)", size=11, family="DM Mono"),
                    )])
                    fig_bar.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="rgba(232,232,240,0.45)", family="DM Sans"),
                        title=dict(text="Storage Usage", font=dict(size=13, color="rgba(232,232,240,0.55)", family="Syne")),
                        xaxis=dict(gridcolor="rgba(255,255,255,0.03)", showline=False),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.03)", showline=False, title="MB"),
                        margin=dict(l=20, r=20, t=50, b=20),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                except Exception:
                    st.info("Not enough data for storage chart.")
        else:
            st.markdown(
                '<div class="empty-state">'
                '<span class="empty-icon">📈</span>'
                '<div class="empty-text">No timeline data yet</div>'
                '<div class="empty-hint">Add more files to see trends over time.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="empty-state">'
            '<span class="empty-icon">📈</span>'
            '<div class="empty-text">No files indexed yet</div>'
            '<div class="empty-hint">Add files to your vault folder to see the timeline.</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# =============================================================================
# TAB 3: EXPLORE ALL
# =============================================================================

with tab_explore:
    all_files_ex = api_get("/api/all-files")
    if all_files_ex and all_files_ex.get("files"):
        files = all_files_ex["files"]

        st.markdown(
            '<div class="query-info">'
            f'<div class="query-text">🗂️ Your Memory Vault</div>'
            f'<div class="query-count">{len(files)} files indexed and searchable</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            type_filter = st.selectbox(
                "Filter",
                ["All", "image", "document"],
                format_func=lambda x: {
                    "All": "🔍 All Types",
                    "image": "🖼️ Images",
                    "document": "📄 Documents",
                }[x],
                key="explore_filter",
            )
        with col_f2:
            sort_by = st.selectbox(
                "Sort",
                ["Modified Date", "File Name", "File Size"],
                format_func=lambda x: {
                    "Modified Date": "📅 Modified Date",
                    "File Name": "🔤 File Name",
                    "File Size": "📏 File Size",
                }[x],
                key="explore_sort",
            )

        if type_filter != "All":
            files = [f for f in files if f.get("file_type") == type_filter]

        if sort_by == "Modified Date":
            files.sort(key=lambda x: x.get("modified_date", ""), reverse=True)
        elif sort_by == "File Name":
            files.sort(key=lambda x: x.get("file_name", "").lower())
        elif sort_by == "File Size":
            files.sort(key=lambda x: int(x.get("file_size_bytes", 0) or 0), reverse=True)

        cols = st.columns(3)
        for i, file_meta in enumerate(files):
            col = cols[i % 3]
            with col:
                st.markdown('<div class="result-card animate-in">', unsafe_allow_html=True)

                file_path = file_meta.get("file_path", "")
                file_name = file_meta.get("file_name", "Unknown")
                file_type = file_meta.get("file_type", "")
                file_ext = file_meta.get("file_extension", "")

                if file_type == "image" and file_path and Path(file_path).exists():
                    try:
                        st.image(file_path, use_container_width=True)
                    except Exception:
                        st.markdown(
                            '<div class="doc-icon-container"><div class="doc-icon">🖼️</div></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    icons = {".pdf": "📄", ".txt": "📝", ".docx": "📃", ".md": "📑"}
                    icon = icons.get(file_ext, "📁")
                    ext_label = file_ext.replace(".", "").upper() if file_ext else "FILE"
                    st.markdown(
                        f'<div class="doc-icon-container"><div class="doc-icon">{icon}</div>'
                        f'<div class="doc-ext">{ext_label}</div></div>',
                        unsafe_allow_html=True,
                    )

                st.markdown(f'<div class="result-filename">{file_name}</div>', unsafe_allow_html=True)

                tags = file_meta.get("auto_tags", "")
                if tags:
                    tags_html = '<div class="tags-container">'
                    for t in tags.split(",")[:4]:
                        tags_html += f'<span class="result-tag">{t.strip()}</span>'
                    tags_html += '</div>'
                    st.markdown(tags_html, unsafe_allow_html=True)

                if file_meta.get("_document_preview"):
                    preview = file_meta["_document_preview"][:120] + "..."
                    st.markdown(f'<div class="text-preview">{preview}</div>', unsafe_allow_html=True)

                size_str = format_file_size(file_meta.get("file_size_bytes", 0))
                modified = str(file_meta.get("modified_date", ""))[:10]
                st.markdown(
                    f'<div class="result-meta">'
                    f'<span>📏 {size_str}</span>'
                    f'<span class="meta-dot"></span>'
                    f'<span>📅 {modified}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="empty-state">'
            '<span class="empty-icon">🗂️</span>'
            '<div class="empty-text">Your vault is empty</div>'
            '<div class="empty-hint">Drop files into the sample_files folder and they\'ll appear here.</div>'
            '</div>',
            unsafe_allow_html=True,
        )