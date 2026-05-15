"""
report_generator.py
====================
Generates matplotlib + seaborn charts for the Scan Report section.
All charts rendered in-memory (no disk I/O) and returned as base64 PNG strings.

Two modes:
  - generate_copypaste_report(scan_data): 5 charts for full scored scan
  - generate_inbox_report(inbox_data):    4 charts for inbox-only scan
"""

import io
import base64
from datetime import datetime, date
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Shared dark theme ────────────────────────────────────────────────────────
BG       = '#0d0d0d'
CARD_BG  = '#141414'
WHITE    = '#ffffff'
DIM      = 'rgba(255,255,255,0.4)'
GREEN    = '#4caf50'
AMBER    = '#ff9800'
RED      = '#f44336'
BLUE     = '#2196f3'
PURPLE   = '#9c27b0'
TEAL     = '#00bcd4'
ACCENT   = '#e0e0e0'

PALETTE  = [GREEN, BLUE, AMBER, RED, PURPLE, TEAL, '#ff6b6b', '#ffd166', '#06d6a0']

def _apply_dark_theme(fig, ax):
    """Apply the dark aesthetic to any figure/axes."""
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=ACCENT, labelsize=9)
    ax.xaxis.label.set_color(ACCENT)
    ax.yaxis.label.set_color(ACCENT)
    ax.title.set_color(WHITE)
    for spine in ax.spines.values():
        spine.set_edgecolor('#2a2a2a')

def _to_base64(fig) -> str:
    """Render figure to base64 PNG and close it."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return encoded

def _chart(title, caption, image_b64) -> dict:
    return {"title": title, "caption": caption, "image": image_b64}


# ─────────────────────────────────────────────────────────────────────────────
# COPY-PASTE / FILE UPLOAD CHARTS  (full 105-pt scoring)
# ─────────────────────────────────────────────────────────────────────────────

def _chart_score_distribution(ranked: list) -> dict:
    """Horizontal bar chart — one bar per opportunity, coloured by score tier."""
    if not ranked:
        return None

    titles = []
    scores = []
    colors = []
    for opp in ranked[:12]:  # cap at 12 for readability
        raw_title = opp.get('title', 'Untitled')
        titles.append(raw_title[:35] + '…' if len(raw_title) > 35 else raw_title)
        score = opp.get('score_breakdown', {}).get('total', 0) or 0
        scores.append(score)
        if score >= 70:
            colors.append(GREEN)
        elif score >= 40:
            colors.append(AMBER)
        else:
            colors.append(RED)

    # Reverse so highest is at top
    titles = titles[::-1]
    scores = scores[::-1]
    colors = colors[::-1]

    fig, ax = plt.subplots(figsize=(8, max(3, len(titles) * 0.55)))
    _apply_dark_theme(fig, ax)

    bars = ax.barh(titles, scores, color=colors, height=0.6, zorder=3)
    ax.set_xlim(0, 110)
    ax.axvline(x=70, color=GREEN, linestyle='--', alpha=0.4, linewidth=1)
    ax.axvline(x=40, color=AMBER, linestyle='--', alpha=0.4, linewidth=1)

    # Value labels
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'{score:.0f}', va='center', ha='left',
                fontsize=8, color=WHITE, fontweight='bold')

    ax.set_xlabel('Score (out of 105)', fontsize=9, color=ACCENT)
    ax.set_title('Opportunity Score Distribution', fontsize=12, fontweight='bold', pad=12, color=WHITE)
    ax.grid(axis='x', color='#2a2a2a', linewidth=0.5, zorder=0)

    legend = [
        mpatches.Patch(color=GREEN, label='Strong Match (≥70)'),
        mpatches.Patch(color=AMBER, label='Moderate (40–69)'),
        mpatches.Patch(color=RED,   label='Weak (<40)'),
    ]
    ax.legend(handles=legend, loc='lower right', fontsize=8,
              facecolor=CARD_BG, edgecolor='#333', labelcolor=ACCENT)

    fig.tight_layout()
    return _chart(
        'Score Distribution',
        'How each opportunity ranked against your profile out of 105 points. Green = strong match, Amber = moderate, Red = weak.',
        _to_base64(fig)
    )


def _chart_radar_top(ranked: list) -> dict:
    """Radar chart for the top-ranked opportunity — 6 scoring dimensions."""
    if not ranked:
        return None

    top = ranked[0]
    sb = top.get('score_breakdown', {})
    dims = [
        ('Skill\nAlignment', sb.get('skill_alignment', {}).get('score', 0), 55),
        ('Urgency',          sb.get('urgency',         {}).get('score', 0), 15),
        ('Type\nMatch',      sb.get('type_match',      {}).get('score', 0), 15),
        ('Location',         sb.get('location',        {}).get('score', 0), 10),
        ('Financial',        sb.get('financial_bonus', {}).get('score', 0), 5),
        ('Completeness',     sb.get('completeness',    {}).get('score', 0), 5),
    ]
    labels    = [d[0] for d in dims]
    raw       = [d[1] for d in dims]
    maxvals   = [d[2] for d in dims]
    normed    = [r / m if m else 0 for r, m in zip(raw, maxvals)]

    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    normed += normed[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD_BG)

    ax.plot(angles, normed, color=TEAL, linewidth=2)
    ax.fill(angles, normed, color=TEAL, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8, color=ACCENT)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7, color='#555')
    ax.grid(color='#2a2a2a', linewidth=0.5)
    ax.spines['polar'].set_edgecolor('#2a2a2a')

    title = top.get('title', 'Top Opportunity')[:40]
    ax.set_title(f'Fit Profile: {title}', fontsize=11, fontweight='bold', pad=18, color=WHITE)

    fig.tight_layout()
    return _chart(
        'Top Match Radar',
        f'Multi-dimensional fit breakdown for your best-ranked opportunity across all 6 scoring dimensions.',
        _to_base64(fig)
    )


def _chart_score_components(ranked: list) -> dict:
    """Stacked bar chart showing score breakdown for top opportunities."""
    top_opps = ranked[:5]
    if not top_opps:
        return None

    titles = [(opp.get('title', 'Untitled') or 'Untitled')[:20] + '...' for opp in top_opps]
    
    # Extract score components
    components = ['skill_alignment', 'urgency', 'type_match', 'location', 'completeness']
    colors = [BLUE, RED, TEAL, PURPLE, AMBER]
    
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    _apply_dark_theme(fig, ax)

    bottoms = np.zeros(len(top_opps))
    x = np.arange(len(top_opps))
    
    for comp, color in zip(components, colors):
        scores = [opp.get('score_breakdown', {}).get(comp, {}).get('score', 0) for opp in top_opps]
        ax.bar(x, scores, bottom=bottoms, color=color, alpha=0.85, label=comp.replace('_', ' ').title(), zorder=3)
        bottoms += np.array(scores)

    ax.set_xticks(x)
    ax.set_xticklabels(titles, rotation=15, ha='right', fontsize=8, color=ACCENT)
    ax.set_ylabel('Score Points', fontsize=9, color=ACCENT)
    ax.set_title('Top Match Score Components', fontsize=12, fontweight='bold', pad=12, color=WHITE)
    ax.legend(fontsize=8, facecolor=CARD_BG, edgecolor='#333', labelcolor=ACCENT, bbox_to_anchor=(1.01, 1), loc='upper left')
    ax.grid(axis='y', color='#2a2a2a', linewidth=0.5, zorder=0)

    fig.tight_layout()
    return _chart(
        'Score Breakdown Analysis',
        'How the top opportunities accumulated their scores across different matching criteria.',
        _to_base64(fig)
    )


def _chart_type_pie(ranked: list) -> dict:
    """Donut chart of opportunity types."""
    from collections import Counter
    types = [opp.get('type', 'other') or 'other' for opp in ranked]
    counter = Counter(types)
    if not counter:
        return None

    labels = [t.title() for t in counter.keys()]
    sizes  = list(counter.values())
    colors = PALETTE[:len(labels)]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct='%1.0f%%', startangle=140,
        pctdistance=0.78,
        wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2)
    )
    for autotext in autotexts:
        autotext.set_color(WHITE)
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')

    ax.legend(wedges, labels, loc='lower center', fontsize=8,
              facecolor=CARD_BG, edgecolor='#333', labelcolor=ACCENT,
              ncol=2, bbox_to_anchor=(0.5, -0.12))
    ax.set_title('Opportunity Types Found', fontsize=12, fontweight='bold', pad=14, color=WHITE)

    fig.tight_layout()
    return _chart(
        'Opportunity Type Breakdown',
        'Distribution of opportunity categories identified in this scan.',
        _to_base64(fig)
    )


def _chart_deadline_timeline(ranked: list) -> dict:
    """Gantt-style horizontal timeline: today → deadline for each opportunity."""
    today = date.today()
    items = []
    for opp in ranked[:10]:
        deadline_str = opp.get('deadline_iso')
        if not deadline_str:
            continue
        try:
            dl = datetime.fromisoformat(deadline_str.replace('Z', '+00:00')).date()
            days_left = (dl - today).days
            urgency = opp.get('urgency_badge', 'LOW')
            if days_left < 0:
                urgency = 'EXPIRED'
            items.append({
                'title': (opp.get('title', 'Untitled') or 'Untitled')[:30],
                'days': days_left,
                'urgency': urgency,
            })
        except Exception:
            continue

    if not items:
        return None

    items.sort(key=lambda x: x['days'])
    titles = [i['title'] for i in items]
    days   = [i['days'] for i in items]
    colors = [
        '#666666' if d['urgency'] == 'EXPIRED' else
        RED if d['urgency'] in ('CRITICAL', 'HIGH') else 
        AMBER if d['urgency'] == 'MEDIUM' else 
        GREEN
        for d in items
    ]

    fig, ax = plt.subplots(figsize=(8, max(3, len(items) * 0.55)))
    _apply_dark_theme(fig, ax)

    bars = ax.barh(titles, days, color=colors, height=0.55, zorder=3)
    ax.axvline(x=7,  color=RED,   linestyle='--', alpha=0.5, linewidth=1, label='7 days')
    ax.axvline(x=30, color=AMBER, linestyle='--', alpha=0.5, linewidth=1, label='30 days')

    for bar, d in zip(bars, days):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f'{d}d', va='center', ha='left', fontsize=8, color=WHITE, fontweight='bold')

    ax.set_xlabel('Days Until Deadline', fontsize=9, color=ACCENT)
    ax.set_title('Deadline Timeline', fontsize=12, fontweight='bold', pad=12, color=WHITE)
    ax.grid(axis='x', color='#2a2a2a', linewidth=0.5, zorder=0)
    ax.legend(fontsize=8, facecolor=CARD_BG, edgecolor='#333', labelcolor=ACCENT)

    fig.tight_layout()
    return _chart(
        'Deadline Timeline',
        'Days remaining for each opportunity. Red = urgent (< 7 days), Amber = soon (< 30 days), Green = ample time.',
        _to_base64(fig)
    )


def generate_copypaste_report(scan_data: dict) -> list:
    """Generate 5 charts for a copy-paste / file scan result."""
    ranked       = scan_data.get('ranked_opportunities') or scan_data.get('ranked') or []
    user_skills  = scan_data.get('profile', {}).get('skills', []) if scan_data.get('profile') else []

    charts = []
    for fn, args in [
        (_chart_score_distribution, (ranked,)),
        (_chart_radar_top,          (ranked,)),
        (_chart_score_components,   (ranked,)),
        (_chart_type_pie,           (ranked,)),
        (_chart_deadline_timeline,  (ranked,)),
    ]:
        try:
            result = fn(*args)
            if result:
                charts.append(result)
        except Exception as e:
            charts.append({"title": "Chart Error", "caption": str(e), "image": ""})

    return charts


# ─────────────────────────────────────────────────────────────────────────────
# INBOX SCAN CHARTS  (profile-independent — no scores)
# ─────────────────────────────────────────────────────────────────────────────

def _inbox_category_donut(results: dict) -> dict:
    """Donut chart: proportion of email categories."""
    cats = {
        'Opportunities':  len(results.get('opportunities', [])),
        'Meetings':       len(results.get('meetings', [])),
        'Interviews':     len(results.get('interviews', [])),
        'Deadlines':      len(results.get('deadlines', [])),
        'Grants':         len(results.get('grants', [])),
        'Other':          len(results.get('other_important', [])),
    }
    cats = {k: v for k, v in cats.items() if v > 0}
    if not cats:
        return None

    labels = list(cats.keys())
    sizes  = list(cats.values())
    colors = [GREEN, BLUE, AMBER, RED, PURPLE, TEAL][:len(labels)]

    fig, ax = plt.subplots(figsize=(6, 5.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct='%1.0f%%', startangle=90,
        pctdistance=0.78,
        wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2)
    )
    for autotext in autotexts:
        autotext.set_color(WHITE)
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')

    legend_labels = [f'{l} ({s})' for l, s in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, loc='lower center', fontsize=8,
              facecolor=CARD_BG, edgecolor='#333', labelcolor=ACCENT,
              ncol=2, bbox_to_anchor=(0.5, -0.16))
    ax.set_title('Inbox Category Breakdown', fontsize=12, fontweight='bold', pad=14, color=WHITE)

    fig.tight_layout()
    return _chart(
        'Category Distribution',
        'How your scanned inbox breaks down by email category — helping you see what type of communication dominates.',
        _to_base64(fig)
    )


def _inbox_opp_subtypes(results: dict) -> dict:
    """Horizontal bar chart of opportunity sub-types."""
    from collections import Counter
    opps = results.get('opportunities', [])
    if not opps:
        return None

    types = [o.get('type', 'opportunity').replace('_', ' ').title() for o in opps]
    counter = Counter(types)
    labels  = list(counter.keys())
    values  = list(counter.values())

    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.6)))
    _apply_dark_theme(fig, ax)

    bars = ax.barh(labels, values, color=GREEN, height=0.5, alpha=0.85, zorder=3)
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                str(v), va='center', ha='left', fontsize=9, color=WHITE, fontweight='bold')

    ax.set_xlabel('Count', fontsize=9, color=ACCENT)
    ax.set_title('Opportunity Sub-types', fontsize=12, fontweight='bold', pad=12, color=WHITE)
    ax.grid(axis='x', color='#2a2a2a', linewidth=0.5, zorder=0)

    fig.tight_layout()
    return _chart(
        'Opportunity Sub-types',
        'Types of opportunities extracted from your inbox — internships, scholarships, hackathons, and more.',
        _to_base64(fig)
    )


def _inbox_top_senders(results: dict) -> dict:
    """Bar chart of top sender domains."""
    from collections import Counter
    all_items = (
        results.get('opportunities', []) +
        results.get('meetings', []) +
        results.get('interviews', []) +
        results.get('deadlines', []) +
        results.get('grants', [])
    )
    orgs = [item.get('org', '') or '' for item in all_items]
    orgs = [o.strip()[:30] for o in orgs if o.strip()]
    if not orgs:
        return None

    counter = Counter(orgs)
    top = counter.most_common(8)
    labels = [t[0] for t in top]
    values = [t[1] for t in top]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.55)))
    _apply_dark_theme(fig, ax)

    bars = ax.barh(labels[::-1], values[::-1], color=BLUE, height=0.55, alpha=0.85, zorder=3)
    for bar, v in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                str(v), va='center', ha='left', fontsize=9, color=WHITE, fontweight='bold')

    ax.set_xlabel('Emails Found', fontsize=9, color=ACCENT)
    ax.set_title('Top Senders / Organizations', fontsize=12, fontweight='bold', pad=12, color=WHITE)
    ax.grid(axis='x', color='#2a2a2a', linewidth=0.5, zorder=0)

    fig.tight_layout()
    return _chart(
        'Top Senders',
        'Organizations and senders most frequently detected in your scanned inbox.',
        _to_base64(fig)
    )


def _inbox_urgency_spread(results: dict) -> dict:
    """Pie chart of deadline urgency across all categorized items."""
    from collections import Counter
    all_items = (
        results.get('opportunities', []) +
        results.get('deadlines', []) +
        results.get('grants', [])
    )
    urgencies = [item.get('deadline_proximity', 'none') or 'none' for item in all_items]
    label_map = {
        'urgent':   'Urgent (< 7 days)',
        'soon':     'Soon (< 30 days)',
        'upcoming': 'Upcoming',
        'later':    'Later',
        'none':     'No Deadline',
    }
    urgencies = [label_map.get(u, u) for u in urgencies]
    counter = Counter(urgencies)
    if not counter:
        return None

    labels = list(counter.keys())
    sizes  = list(counter.values())
    colors = [RED, AMBER, BLUE, GREEN, '#555555'][:len(labels)]

    fig, ax = plt.subplots(figsize=(6, 5.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct='%1.0f%%', startangle=140,
        pctdistance=0.78,
        wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2)
    )
    for autotext in autotexts:
        autotext.set_color(WHITE)
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')

    legend_labels = [f'{l} ({s})' for l, s in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, loc='lower center', fontsize=8,
              facecolor=CARD_BG, edgecolor='#333', labelcolor=ACCENT,
              ncol=2, bbox_to_anchor=(0.5, -0.16))
    ax.set_title('Deadline Urgency Spread', fontsize=12, fontweight='bold', pad=14, color=WHITE)

    fig.tight_layout()
    return _chart(
        'Urgency Spread',
        'How time-sensitive are the items in your inbox? Red = requires immediate action.',
        _to_base64(fig)
    )


def generate_inbox_report(inbox_results: dict) -> list:
    """Generate 4 charts for an inbox scan result."""
    results = inbox_results.get('results') or inbox_results

    charts = []
    for fn, args in [
        (_inbox_category_donut, (results,)),
        (_inbox_opp_subtypes,   (results,)),
        (_inbox_top_senders,    (results,)),
        (_inbox_urgency_spread, (results,)),
    ]:
        try:
            result = fn(*args)
            if result:
                charts.append(result)
        except Exception as e:
            charts.append({"title": "Chart Error", "caption": str(e), "image": ""})

    return charts
