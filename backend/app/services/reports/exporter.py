import html
from typing import Dict, Any, List, Optional
from datetime import datetime

SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#3b82f6",
    "informational": "#6b7280"
}

def format_finding_item(f: Dict[str, Any], presentation_mode: str = "technical_review") -> Dict[str, Any]:
    """Ensures finding contains standard canonical fields across all presentation views."""
    sev = f.get("severity", "info").lower()
    conf = float(f.get("confidence", 0.8))
    ev_items = f.get("evidence_items", []) or f.get("evidence", []) or []
    primary_ev = ev_items[0] if ev_items else {}
    path = primary_ev.get("display_path", "Unknown file")
    l_start = primary_ev.get("line_start")
    l_end = primary_ev.get("line_end") or l_start
    line_ref = f"{path}:L{l_start}-{l_end}" if l_start else path

    v_status = f.get("verification_status", "static_analysis")
    status_label = {
        "static_analysis": "Statically Detected",
        "inference": "Inferred Risk",
        "runtime_confirmed": "Runtime Confirmed",
        "manual_review_required": "Manual Review Required",
        "not_tested": "Not Tested"
    }.get(v_status, v_status.replace("_", " ").title())

    is_simplified = presentation_mode in ("simplified_version", "simple")

    return {
        "id": f.get("id"),
        "title": f.get("title", "Observation"),
        "what_found": f.get("explanation", ""),
        "why_matters": f.get("impact", "Impact requires engineering review."),
        "severity": sev,
        "confidence": conf,
        "confidence_percentage": round(conf * 100),
        "evidence_reference": "General System Concept" if is_simplified else line_ref,
        "evidence_items": [] if is_simplified else ev_items,
        "detection_type": status_label,
        "remediation": f.get("remediation", "Review and remediate according to best practices."),
        "agent_id": f.get("agent_id", "specialist"),
        "limitations": f.get("limitations")
    }

def generate_markdown_report(
    project_name: str,
    question: str,
    status: str,
    summary: str,
    limitations: str,
    findings: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    mode: str = "technical_review",
    profile: Optional[Dict[str, Any]] = None
) -> str:
    """Generates structured Markdown report strictly adhering to the selected Persona Mode."""
    norm_mode = "simplified_version" if mode in ("simplified_version", "simple") else "technical_review"
    formatted_findings = [format_finding_item(f, norm_mode) for f in findings]
    app_type = profile.get("application_type", "Software Application") if profile else "Software Application"

    if norm_mode == "simplified_version":
        title_tag = "Simplified Plain-Language Review"
        md = [
            f"# M-ARCH {title_tag}: {project_name}",
            f"**Application Type:** {app_type}  ",
            f"**Review Inquiry:** {question}  ",
            f"**Review Status:** {status.upper()}  \n",
            "---",
            "## What You Need to Know (Summary)",
            summary or "No critical issues detected. The project follows standard software hygiene.",
            "\n---",
            f"## Key Observations & Recommendations ({len(formatted_findings)} total)",
        ]
        if not formatted_findings:
            md.append("No critical issues found. Your project appears to follow standard hygiene for static checks.")
        else:
            for idx, f in enumerate(formatted_findings, 1):
                md.append(f"### {idx}. {f['title']} [{f['severity'].upper()}]")
                md.append(f"- **What is the problem?** {f['what_found']}")
                md.append(f"- **Why does it matter?** {f['why_matters']}")
                md.append(f"- **How do we fix it?** {f['remediation']}\n")
        md.extend([
            "---",
            "## What Was Not Examined (Limitations)",
            limitations or "This assessment is based on automated static inspection. Live system performance, server environments, and live user logins were not tested."
        ])
        return "\n".join(md)

    else:
        # Technical Review Mode (Strict Root Cause, Line Numbers & Explicit Remediation)
        if mode == "professional":
            title_tag = "Formal Architecture Review & Audit"
        elif mode == "executive":
            title_tag = "Executive Architecture & Hygiene Brief"
        else:
            title_tag = "Technical Architecture & Engineering Review"

        md = [
            f"# M-ARCH {title_tag}: {project_name}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Review Scope:** {question}  ",
            f"**Application Profile:** {app_type}  ",
            f"**Execution Status:** {status.upper()}  \n",
            "---",
            "## Executive Synthesis",
            summary or "Static analysis completed without ungrounded assertions.",
            "\n---",
            f"## Verified Technical Findings ({len(formatted_findings)} total)",
        ]
        if not formatted_findings:
            md.append("No critical static findings detected during automated multi-agent inspection.")
        else:
            for idx, f in enumerate(formatted_findings, 1):
                md.append(f"### {idx}. [{f['severity'].upper()}] {f['title']}")
                md.append(f"- **Responsible Agent:** `{f['agent_id']}` | **Verification Type:** `{f['detection_type']}` | **Confidence:** `{f['confidence_percentage']}%`")
                md.append(f"- **Issue Identified:** {f['what_found']}")
                md.append(f"- **Technical Root Cause:** {f['why_matters']}")
                md.append(f"- **Specific Remediation Steps:** {f['remediation']}")
                md.append(f"- **Location & Evidence Grounding:** `{f['evidence_reference']}`")
                if f["evidence_items"]:
                    md.append("#### Cited Source Excerpts:")
                    for ev in f["evidence_items"]:
                        l_range = f"L{ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else "Global"
                        md.append(f"- Source: `{ev.get('display_path')}` ({l_range}) [Method: `{ev.get('retrieval_method', 'hybrid')}`]")
                        md.append("```text\n" + (ev.get("excerpt") or "").strip() + "\n```")
                md.append("")
        md.extend([
            "---",
            "## Scope & Explicit Technical Limitations",
            limitations or "Static analysis conducted. Project was evaluated strictly via static code inspection and RAG retrieval over snapshot sources. Code was not dynamically executed.",
            "\n---",
            "## Multi-Agent Execution Trace",
        ])
        for t in tasks:
            md.append(f"- **{t.get('task_name', t.get('agent_id'))}**: Status `{t.get('status')}` | Time `{t.get('execution_time_seconds', 0.0)}s` | Provider `{t.get('provider_used')}` / `{t.get('model_used')}`")
        return "\n".join(md)

def generate_html_report(
    project_name: str,
    question: str,
    status: str,
    summary: str,
    limitations: str,
    findings: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    mode: str = "technical_review",
    profile: Optional[Dict[str, Any]] = None
) -> str:
    """Generates structured printable HTML report for the chosen presentation mode."""
    norm_mode = "simplified_version" if mode in ("simplified_version", "simple") else "technical_review"
    formatted_findings = [format_finding_item(f, norm_mode) for f in findings]
    app_type = profile.get("application_type", "Software Application") if profile else "Software Application"

    findings_html = []
    if norm_mode == "simplified_version":
        for idx, f in enumerate(formatted_findings, 1):
            sev_color = SEVERITY_COLORS.get(f["severity"], "#6b7280")
            findings_html.append(f"""
                <div style="border: 1px solid #2e2e2e; border-radius: 8px; padding: 18px; margin-bottom: 16px; background: #222222;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;">
                        <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #f4f4f5; font-family: 'Space Grotesk', sans-serif;">{idx}. {html.escape(f['title'])}</h3>
                        <span style="background: {sev_color}22; color: {sev_color}; border: 1px solid {sev_color}44; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">{f['severity']}</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #f4f4f5; font-size: 13px;">What is the problem?</strong>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #a1a1aa; line-height: 1.5;">{html.escape(f['what_found'])}</p>
                    </div>
                    <div style="margin-bottom: 10px; background: #161616; padding: 10px 14px; border-radius: 6px; border: 1px solid #2e2e2e;">
                        <strong style="color: #f4f4f5; font-size: 13px;">Why does it matter?</strong>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #a1a1aa; line-height: 1.5;">{html.escape(f['why_matters'])}</p>
                    </div>
                    <div style="background: #161616; padding: 10px 14px; border-radius: 6px; border: 1px solid #2e2e2e;">
                        <strong style="color: #10b981; font-size: 13px;">How do we fix it?</strong>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #d4d4d8; line-height: 1.5;">{html.escape(f['remediation'])}</p>
                    </div>
                </div>
            """)
    else:
        for idx, f in enumerate(formatted_findings, 1):
            sev_color = SEVERITY_COLORS.get(f["severity"], "#6b7280")
            ev_html = []
            for ev in f.get("evidence_items", []):
                line_str = f"Lines {ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else ""
                ev_html.append(f"""
                    <div style="background: #161616; padding: 10px 14px; border-radius: 6px; margin-top: 8px; font-family: 'Space Mono', monospace; font-size: 12px; color: #e5e7eb; border: 1px solid #2e2e2e;">
                        <div style="color: #9ca3af; margin-bottom: 4px;">Source: <strong>{html.escape(ev.get('display_path', ''))}</strong> {line_str}</div>
                        <pre style="margin: 0; white-space: pre-wrap; font-family: inherit;">{html.escape(ev.get('excerpt', ''))}</pre>
                    </div>
                """)

            findings_html.append(f"""
                <div style="border: 1px solid #2e2e2e; border-radius: 8px; padding: 18px; margin-bottom: 16px; background: #222222;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;">
                        <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #f4f4f5; font-family: 'Space Grotesk', sans-serif;">{idx}. [{f['severity'].upper()}] {html.escape(f['title'])}</h3>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span style="background: {sev_color}22; color: {sev_color}; border: 1px solid {sev_color}44; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">{f['severity']}</span>
                            <span style="font-size: 11px; color: #a1a1aa; background: #161616; border: 1px solid #2e2e2e; padding: 2px 6px; border-radius: 4px;">{f['detection_type']}</span>
                        </div>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #f4f4f5; font-size: 13px;">Issue Identified:</strong>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #d4d4d8; line-height: 1.5;">{html.escape(f['what_found'])}</p>
                    </div>
                    <div style="background: #161616; padding: 10px 14px; border-radius: 6px; font-size: 12px; margin-bottom: 10px; border: 1px solid #2e2e2e;">
                        <div style="margin-bottom: 6px;"><strong style="color: #f4f4f5;">Technical Root Cause:</strong> <span style="color: #a1a1aa;">{html.escape(f['why_matters'])}</span></div>
                        <div style="margin-bottom: 6px;"><strong style="color: #10b981;">Specific Remediation Steps:</strong> <span style="color: #d4d4d8;">{html.escape(f['remediation'])}</span></div>
                        <div style="font-family: 'Space Mono', monospace; color: #71717a; font-size: 11px;">Location: {html.escape(f['evidence_reference'])} (Confidence: {f['confidence_percentage']}%)</div>
                    </div>
                    {''.join(ev_html)}
                </div>
            """)

    tasks_html = "".join([
        f"<li style='margin-bottom: 6px;'><strong>{html.escape(t.get('task_name', t.get('agent_id')))}</strong>: {t.get('status')} ({t.get('execution_time_seconds', 0.0)}s) via {t.get('provider_used')} / {t.get('model_used')}</li>"
        for t in tasks
    ])

    title_header = "Simplified System Review" if norm_mode == "simplified_version" else "Technical Architecture & Security Review"

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>M-ARCH Review Report - {html.escape(project_name)}</title>
    <style>
        body {{ font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #161616; color: #f4f4f5; margin: 0; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 6px; color: #ffffff; }}
        .meta {{ font-size: 12px; color: #a1a1aa; margin-bottom: 24px; font-family: 'Space Mono', monospace; }}
        .summary-card {{ background: #222222; border: 1px solid #2e2e2e; border-radius: 8px; padding: 20px; margin-bottom: 28px; line-height: 1.6; font-size: 14px; }}
        .limitations {{ background: #222222; border: 1px solid #dc262644; border-radius: 8px; padding: 16px; margin-top: 28px; font-size: 13px; color: #e7e5e4; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>M-ARCH {title_header}: {html.escape(project_name)}</h1>
        <div class="meta">
            Scope: <strong>{html.escape(question)}</strong> | Profile: <strong>{html.escape(app_type)}</strong> | Mode: <strong>{html.escape(norm_mode.upper())}</strong> | Status: <strong>{html.escape(status.upper())}</strong>
        </div>
        <div class="summary-card">
            <h2 style="font-size: 16px; margin-top: 0; color: #f4f4f5;">{'Executive Overview' if norm_mode == 'simplified_version' else 'Executive Synthesis'}</h2>
            <div>{html.escape(summary or 'No critical static findings detected.')}</div>
        </div>
        <h2 style="font-size: 18px; color: #f4f4f5; margin-bottom: 16px;">Verified Findings ({len(formatted_findings)})</h2>
        {''.join(findings_html) if findings_html else '<p style="color: #a1a1aa;">No critical static findings detected.</p>'}
        <div class="limitations">
            <h3 style="margin-top: 0; font-size: 14px; color: #fbbf24;">{'What Was Not Examined' if norm_mode == 'simplified_version' else 'Scope & Explicit Technical Limitations'}</h3>
            <p style="margin: 0;">{html.escape(limitations or 'Conducted via static inspection and RAG retrieval. Project code was not executed.')}</p>
        </div>
        {f'<div style="margin-top: 28px; font-size: 12px; color: #71717a;"><h4 style="color: #a1a1aa; margin-bottom: 8px;">Multi-Agent Execution Trace</h4><ul style="padding-left: 18px; margin: 0; font-family: monospace;">{tasks_html}</ul></div>' if norm_mode == 'technical_review' else ''}
    </div>
</body>
</html>"""
