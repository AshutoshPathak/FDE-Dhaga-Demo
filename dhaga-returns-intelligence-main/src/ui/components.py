from __future__ import annotations
from pathlib import Path
import pandas as pd

def render_header(api_key: str | None, fast_model: str, strong_model: str, threshold: float) -> str:
    live = bool(api_key)
    mode_badge = (
        '<span class="pill-current"><span class="badge-dot live-dot"></span>Live Gemini 2.5</span>'
        if live else
        '<span class="pill-current" style="color:#fbbf24;background:rgba(245,158,11,0.12);border-color:rgba(245,158,11,0.3);"><span class="badge-dot demo-dot"></span>Demo Preview</span>'
    )
    return f"""
    <nav id="navbar-header">
      <div class="nav-left">
        <div class="nav-logo-box">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
        </div>
        <div class="nav-brand-title">Dhaga Returns Intelligence</div>
      </div>
      <div class="nav-links">
        <span class="nav-link-item active">Overview</span>
        <span class="nav-link-item">Returns Explorer</span>
        <span class="nav-link-item">Review Queue</span>
        <span class="nav-link-item">Category Insights</span>
        <span class="nav-link-item">Telemetry</span>
      </div>
      <div class="nav-right">
        {mode_badge}
        <button class="btn-nav-outline">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        </button>
        <span class="btn-nav-outline">⭐ Threshold: {int(threshold * 100)}%</span>
      </div>
    </nav>
    """

def render_hero_section() -> str:
    return """
    <div class="hero-container">
      <div class="hero-breadcrumb">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
        <span>Back to Operations</span>
      </div>
      <h1 class="hero-title">Updates &amp; Return Intelligence</h1>
      <div class="hero-pill-row">
        <span class="pill-current">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          Current: v2.5 Flash-Lite
        </span>
        <span class="pill-glow-action">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
          Gemini Two-Stage Pipeline
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
        </span>
      </div>
      <p class="hero-description">
        Track the evolution of Dhaga &amp; Co. fashion return drivers with detailed classification notes, automated defect localization, and SKU-level operational actions.
      </p>
    </div>
    """

def render_default_file_summary() -> str:
    return '<div class="metadata-ribbon-dark"><div class="meta-pill-dark"><span>Ready for dataset. Upload returns CSV or load sample data above.</span></div></div>'

def render_file_summary(path: str, df: pd.DataFrame, msg: str) -> str:
    total = len(df)
    skus = df['sku'].nunique() if 'sku' in df.columns else 0
    cats = df['category'].nunique() if 'category' in df.columns else 0
    other_cnt = int((df['return_reason_selected'] == 'Other').sum()) if 'return_reason_selected' in df.columns else 0
    other_pct = round((other_cnt / total * 100), 1) if total else 0
    filename = Path(path).name
    return f"""
    <div class="metadata-ribbon-dark">
      <div class="meta-pill-dark file-tag">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>{filename}</span>
      </div>
      <div class="meta-pill-dark"><span>Records:</span> <b>{total}</b></div>
      <div class="meta-pill-dark"><span>SKUs:</span> <b>{skus}</b></div>
      <div class="meta-pill-dark"><span>Categories:</span> <b>{cats}</b></div>
      <div class="meta-pill-dark alert-tag"><span>Tagged "Other":</span> <b>{other_cnt}</b> ({other_pct}%)</div>
      <div class="meta-pill-dark status-tag">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span>{msg}</span>
      </div>
    </div>
    """

def render_default_metrics() -> str:
    return render_metrics({"total": "—", "originally_other": "—", "auto_pct": "—", "needs_review": "—"})

def render_metrics(m: dict, threshold: float = 0.80) -> str:
    pct_display = f"{m['auto_pct']}%" if m['auto_pct'] != "—" else "—"
    return f"""
    <div class="dark-kpi-grid">
      <div class="dark-kpi-card">
        <div class="kpi-header-dark">
          <span class="kpi-label-dark">Returns Analysed</span>
          <div class="kpi-icon-dark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
          </div>
        </div>
        <div class="kpi-num-dark">{m['total']}</div>
        <div class="kpi-sub-dark">Total batch volume processed</div>
      </div>

      <div class="dark-kpi-card">
        <div class="kpi-header-dark">
          <span class="kpi-label-dark">Originally Tagged “Other”</span>
          <div class="kpi-icon-dark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>
          </div>
        </div>
        <div class="kpi-num-dark">{m['originally_other']}</div>
        <div class="kpi-sub-dark">Unstructured comments resolved</div>
      </div>

      <div class="dark-kpi-card">
        <div class="kpi-header-dark">
          <span class="kpi-label-dark">Auto-Classified Rate</span>
          <div class="kpi-icon-dark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
        </div>
        <div class="kpi-num-dark">{pct_display}</div>
        <div class="kpi-sub-dark">High confidence (≥ {int(threshold*100)}%)</div>
      </div>

      <div class="dark-kpi-card">
        <div class="kpi-header-dark">
          <span class="kpi-label-dark">Needs Category Review</span>
          <div class="kpi-icon-dark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          </div>
        </div>
        <div class="kpi-num-dark">{m['needs_review']}</div>
        <div class="kpi-sub-dark">Flagged for human triage queue</div>
      </div>
    </div>
    """

def render_reason_bars(reasons_df: pd.DataFrame) -> str:
    if reasons_df.empty:
        return ""
    
    items_html = []
    for _, row in reasons_df.head(6).iterrows():
        reason = str(row["Reason"])
        count = int(row["Returns"])
        pct = float(row["Percent"])
        
        items_html.append(f"""
        <div class="bar-row-dark">
          <div class="bar-labels-dark">
            <span class="name">{reason}</span>
            <span class="stat"><b>{count}</b> ({pct}%)</span>
          </div>
          <div class="track-dark">
            <div class="fill-dark" style="width: {min(pct, 100)}%;"></div>
          </div>
        </div>
        """)

    return f"""
    <div class="dark-breakdown-card">
      <div class="breakdown-title-dark">Taxonomy Reason Distribution</div>
      {''.join(items_html)}
    </div>
    """

def render_default_release_cards() -> str:
    return """
    <div class="release-card" style="text-align:center;padding:48px 20px;">
      <div style="font-size:32px;margin-bottom:12px;">⚡</div>
      <div style="font-size:18px;font-weight:750;color:#ffffff;margin-bottom:6px;">No Analysis Run Yet</div>
      <div style="font-size:14px;color:#94a3b8;max-width:420px;margin:0 auto;">Click "Load Sample Dataset" and then "Run Returns Analysis" to generate the structured defect intelligence cards.</div>
    </div>
    """

def render_release_cards(ps: pd.DataFrame, result_df: pd.DataFrame | None = None) -> str:
    if ps.empty:
        return render_default_release_cards()
    
    cards_html = []
    
    # Card 1: Top SKU (Version 1.4.4 Style)
    top1 = ps.iloc[0]
    sku1 = top1['sku']
    
    body_pills1 = []
    if result_df is not None and not result_df.empty and 'ai_body_area' in result_df.columns:
        subset = result_df[(result_df['sku'] == sku1) & (result_df['ai_body_area'].notna())]
        counts = subset['ai_body_area'].value_counts()
        counts = counts[counts.index != "NA"].head(3)
        body_text = ", ".join([f"{k} ({v})" for k, v in counts.items()]) if not counts.empty else "Upper Torso & Armhole"
    else:
        body_text = "Shoulders (58%), Arms (26%), Chest (16%)"

    card1 = f"""
    <div class="release-card">
      <div class="release-card-top">
        <div class="release-icon-box">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
        </div>
        <div class="release-meta-main">
          <div class="release-version-row">
            <span class="release-version-title">{sku1} · {top1['product_name']}</span>
            <span class="tag-badge-green">LATEST</span>
            <span class="tag-badge-muted">CRITICAL DEFECT</span>
          </div>
          <h3 class="release-headline-purple">{top1['top_issue']} Overhaul &amp; Sizing Spec Revision Required</h3>
          <div class="release-date-row">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            <span>Batch: 2026-10 · {top1['returns']} Returns · {top1['fit_pct']}% Fit Defect Rate</span>
          </div>
        </div>
        <div class="release-chevron">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </div>
      </div>

      <div class="subfeature-grid">
        <div class="subfeature-item">
          <div class="subfeature-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
          </div>
          <div class="subfeature-text">
            <div class="item-title">Anatomical Defect Area</div>
            <p class="item-desc">{body_text}. Severe restriction noticed during shoulder &amp; arm movement.</p>
          </div>
        </div>

        <div class="subfeature-item">
          <div class="subfeature-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
          </div>
          <div class="subfeature-text">
            <div class="item-title">Primary Defect Driver</div>
            <p class="item-desc">Dominant customer complaint: <b>{top1['top_issue']}</b>. Pattern confirmed across sizes M and L.</p>
          </div>
        </div>

        <div class="subfeature-item">
          <div class="subfeature-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          </div>
          <div class="subfeature-text">
            <div class="item-title">Recommended Action</div>
            <p class="item-desc">Halt re-orders; revise grading chart with vendor. Advisory: recommend sizing up on product page.</p>
          </div>
        </div>
      </div>
    </div>
    """
    cards_html.append(card1)

    # Card 2: Second SKU (Version 1.4.3 Style)
    if len(ps) > 1:
        top2 = ps.iloc[1]
        sku2 = top2['sku']
        card2 = f"""
        <div class="release-card">
          <div class="release-card-top">
            <div class="release-icon-box">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </div>
            <div class="release-meta-main">
              <div class="release-version-row">
                <span class="release-version-title">{sku2} · {top2['product_name']}</span>
                <span class="tag-badge-purple">PREVIOUS</span>
                <span class="tag-badge-muted">FEATURE ISSUE</span>
              </div>
              <h3 class="release-headline-purple">{top2['top_issue']} Measurement Correction &amp; Alignment</h3>
              <div class="release-date-row">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <span>Batch: 2026-09 · {top2['returns']} Returns · {top2['fit_pct']}% Fit Defect Rate</span>
              </div>
            </div>
            <div class="release-chevron">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
          </div>

          <div class="subfeature-grid" style="grid-template-columns: repeat(2, 1fr);">
            <div class="subfeature-item">
              <div class="subfeature-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
              </div>
              <div class="subfeature-text">
                <div class="item-title">Defect Pattern Description</div>
                <p class="item-desc">Product measures tighter than standard sizing guide. Returns clustered around {top2['top_issue']}.</p>
              </div>
            </div>

            <div class="subfeature-item">
              <div class="subfeature-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
              </div>
              <div class="subfeature-text">
                <div class="item-title">Quality Assurance Directive</div>
                <p class="item-desc">Trigger physical garment audit in next replenishment cycle. Calibrate vendor QA tolerance.</p>
              </div>
            </div>
          </div>
        </div>
        """
        cards_html.append(card2)

    return "\n".join(cards_html)

def render_default_insight() -> str:
    return '<div class="briefing-dark-card"><p style="color:#94a3b8;margin:0;font-size:13.5px;">Run an analysis to generate an automated executive briefing and product-level action plan.</p></div>'

def render_executive_insight(insight: dict) -> str:
    return f"""
    <div class="briefing-dark-card">
      <div class="briefing-pill-purple">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
        <span>STRATEGIC EXECUTIVE BRIEFING</span>
      </div>
      <h3 class="briefing-title-dark">{insight.get('headline', 'Strategic Recommendation')}</h3>
      <div class="briefing-callout-action">
        <div class="callout-heading">RECOMMENDED OPERATIONAL ACTION</div>
        <p class="callout-body">{insight.get('recommended_action', 'Review flagged products.')}</p>
      </div>
      <div class="briefing-callout-evidence">
        <div class="callout-heading" style="color:#94a3b8;">ROOT CAUSE EVIDENCE</div>
        <p class="callout-body" style="color:#cbd5e1;font-weight:450;font-size:13px;">{insight.get('evidence', 'Calculated from customer return comments.')}</p>
      </div>
    </div>
    """

def render_tab_banner(icon: str, title: str, desc: str, extra_class: str = "") -> str:
    return f"""
    <div class="tab-intro-banner {extra_class}" style="background:#111827;border:1px solid #1e293b;border-radius:12px;padding:14px 18px;margin-bottom:18px;">
      <div style="font-size:24px;flex-shrink:0;">{icon}</div>
      <div>
        <div style="font-size:14px;font-weight:750;color:#ffffff;margin-bottom:2px;">{title}</div>
        <div style="font-size:12.5px;color:#94a3b8;line-height:1.4;">{desc}</div>
      </div>
    </div>
    """
