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

def format_finding_item(f: Dict[str, Any], presentation_mode: str = "developer") -> Dict[str, Any]:
    """Ensures finding contains standard canonical fields across all presentation views."""
    sev = f.get("severity", "info").lower()
    conf = float(f.get("confidence", 0.8))
    ev_items = f.get("evidence_items", [])
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

    return {
        "id": f.get("id"),
        "title": f.get("title", "Observation"),
        "what_found": f.get("explanation", ""),
        "why_matters": f.get("impact", "Impact requires engineering review."),
        "severity": sev,
        "confidence": conf,
        "confidence_percentage": round(conf * 100),
        "evidence_reference": line_ref,
        "evidence_items": ev_items,
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
    mode: str = "developer",
    profile: Optional[Dict[str, Any]] = None
) -> str:
    """Generates structured Markdown report for the chosen presentation mode."""
    formatted_findings = [format_finding_item(f, mode) for f in findings]
    app_type = profile.get("application_type", "Software Application") if profile else "Software Application"

    if mode == "simple":
        md = [
            f"# M-ARCH Project Plain-Language Review: {project_name}",
            f"**Application Type:** {app_type}  ",
            f"**Review Inquiry:** {question}  ",
            f"**Status:** {status.upper()}  \n",
            "---",
            "## What You Need to Know (Summary)",
            summary or "No critical static defects detected.",
            "\n---",
            f"## Key Action Items ({len(formatted_findings)} total)",
        ]
        if not formatted_findings:
            md.append("No critical issues found. Your project appears to follow standard hygiene for static checks.")
        else:
            for idx, f in enumerate(formatted_findings, 1):
                md.append(f"### {idx}. {f['title']} [{f['severity'].upper()}]")
                md.append(f"- **What was found:** {f['what_found']}")
                md.append(f"- **Why it matters:** {f['why_matters']}")
                md.append(f"- **Where:** `{f['evidence_reference']}` ({f['detection_type']})")
                md.append(f"- **What to do next:** {f['remediation']}\n")
        md.extend([
            "---",
            "## What Was Not Examined (Limitations)",
            limitations or "This was an automated static analysis. Live security testing, user authentication flows, and server load tests were not run."
        ])
        return "\n".join(md)

    elif mode == "executive":
        sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in formatted_findings:
            sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1

        md = [
            f"# M-ARCH Executive Architecture & Hygiene Brief: {project_name}",
            f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d')} | **Project Profile:** {app_type} | **Status:** {status.upper()}\n",
            "---",
            "## Executive Overview",
            summary or "Review completed without ungrounded assertions.",
            "\n### Risk Breakdown by Severity",
            f"- **Critical Risks:** {sev_counts['critical']}",
            f"- **High Risks:** {sev_counts['high']}",
            f"- **Medium Risks:** {sev_counts['medium']}",
            f"- **Low / Informational:** {sev_counts['low']}\n",
            "---",
            "## High-Priority Findings & Remediation Roadmaps",
        ]
        priority_findings = [f for f in formatted_findings if f["severity"] in ("critical", "high")] or formatted_findings[:5]
        if not priority_findings:
            md.append("No critical static findings detected.")
        else:
            for idx, f in enumerate(priority_findings, 1):
                md.append(f"### {idx}. [{f['severity'].upper()}] {f['title']}")
                md.append(f"- **Impact:** {f['why_matters']}")
                md.append(f"- **Remediation Strategy:** {f['remediation']}")
                md.append(f"- **Location:** `{f['evidence_reference']}`\n")
        md.extend([
            "---",
            "## Scope & Static Analysis Boundaries",
            limitations or "Conducted via static inspection and RAG retrieval. Project code was not executed."
        ])
        return "\n".join(md)

    elif mode == "professional":
        md = [
            f"# M-ARCH Formal Architecture Review & Audit: {project_name}",
            f"**Audit Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Scope Inquiry:** {question}  ",
            f"**Application Classification:** {app_type}  ",
            f"**Verification Outcome:** {status.upper()}  \n",
            "---",
            "## 1. Executive Summary & Synthesis",
            summary or "No critical static defects detected.",
            "\n---",
            "## 2. Evidence-Backed Findings Matrix",
        ]
        if not formatted_findings:
            md.append("No critical static findings detected during automated multi-agent inspection.")
        else:
            for idx, f in enumerate(formatted_findings, 1):
                md.append(f"### 2.{idx} [{f['severity'].upper()}] {f['title']}")
                md.append(f"- **Responsible Agent:** `{f['agent_id']}` | **Verification Type:** `{f['detection_type']}` | **Confidence:** `{f['confidence_percentage']}%`")
                md.append(f"- **Finding Specification:** {f['what_found']}")
                md.append(f"- **Risk & Impact:** {f['why_matters']}")
                md.append(f"- **Recommended Remediation:** {f['remediation']}")
                if f["evidence_items"]:
                    md.append("#### Cited Evidence Excerpts:")
                    for ev in f["evidence_items"]:
                        l_range = f"L{ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else "Global"
                        md.append(f"- Source: `{ev.get('display_path')}` ({l_range}) [Method: `{ev.get('retrieval_method', 'hybrid')}`]")
                        md.append("```text\n" + (ev.get("excerpt") or "").strip() + "\n```")
                md.append("")
        md.extend([
            "---",
            "## 3. Scope, Coverage & Technical Limitations",
            limitations or "Static code inspection only. Project was not built or executed in runtime containers.",
            "\n---",
            "## 4. Multi-Agent Audit Traceability",
        ])
        for t in tasks:
            md.append(f"- **{t.get('task_name', t.get('agent_id'))}**: Status `{t.get('status')}` | Time `{t.get('execution_time_seconds', 0.0)}s` | Provider `{t.get('provider_used')}` / `{t.get('model_used')}`")
        return "\n".join(md)

    else:
        # Developer Review Mode (Default)
        md = [
            f"# M-ARCH Project Engineering Review: {project_name}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Inquiry:** {question}  ",
            f"**Application Profile:** {app_type}  ",
            f"**Execution Status:** {status.upper()}  \n",
            "---",
            "## Executive Summary",
            summary or "No summary provided.",
            "\n---",
            "## Findings & Evidence Grounding",
        ]
        if not formatted_findings:
            md.append("No critical static findings detected.")
        else:
            for idx, f in enumerate(formatted_findings, 1):
                md.append(f"### {idx}. [{f['severity'].upper()}] {f['title']}")
                md.append(f"- **Agent:** `{f['agent_id']}` | **Status:** `{f['detection_type']}` | **Confidence:** `{f['confidence_percentage']}%`")
                md.append(f"- **Explanation:** {f['what_found']}")
                md.append(f"- **Impact:** {f['why_matters']}")
                md.append(f"- **Remediation:** {f['remediation']}")
                if f["evidence_items"]:
                    md.append("#### Supporting Evidence:")
                    for ev in f["evidence_items"]:
                        l_range = f"L{ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else "Global"
                        md.append(f"- **Source:** `{ev.get('display_path')}` ({l_range}) [Method: `{ev.get('retrieval_method', 'hybrid')}`]")
                        md.append("```text\n" + (ev.get("excerpt") or "").strip() + "\n```")
                md.append("")
        md.extend([
            "---",
            "## Scope & Technical Limitations",
            limitations or "Static analysis conducted. Project code was not executed.",
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
    mode: str = "developer",
    profile: Optional[Dict[str, Any]] = None
) -> str:
    """Generates structured printable HTML report for the chosen presentation mode."""
    formatted_findings = [format_finding_item(f, mode) for f in findings]
    app_type = profile.get("application_type", "Software Application") if profile else "Software Application"

    findings_html = []
    for idx, f in enumerate(formatted_findings, 1):
        sev_color = SEVERITY_COLORS.get(f["severity"], "#6b7280")
        ev_html = []
        for ev in f.get("evidence_items", []):
            line_str = f"Lines {ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else ""
            ev_html.append(f"""
                <div style="background: #18181b; padding: 10px 14px; border-radius: 6px; margin-top: 8px; font-family: monospace; font-size: 12px; color: #e5e7eb; border: 1px solid #27272a;">
                    <div style="color: #9ca3af; margin-bottom: 4px;">Source: <strong>{html.escape(ev.get('display_path', ''))}</strong> {line_str}</div>
                    <pre style="margin: 0; white-space: pre-wrap; font-family: inherit;">{html.escape(ev.get('excerpt', ''))}</pre>
                </div>
            """)

        findings_html.append(f"""
            <div style="border: 1px solid #27272a; border-radius: 8px; padding: 18px; margin-bottom: 16px; background: #121214;">
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #fafafa;">{idx}. {html.escape(f['title'])}</h3>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span style="background: {sev_color}22; color: {sev_color}; border: 1px solid {sev_color}44; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">{f['severity']}</span>
                        <span style="font-size: 11px; color: #a1a1aa; background: #27272a; padding: 2px 6px; border-radius: 4px;">{f['detection_type']}</span>
                    </div>
                </div>
                <p style="margin: 0 0 10px 0; font-size: 13px; color: #d4d4d8; line-height: 1.5;">{html.escape(f['what_found'])}</p>
                <div style="background: #1c1c1f; padding: 10px 14px; border-radius: 6px; font-size: 12px; margin-bottom: 10px;">
                    <div style="margin-bottom: 4px;"><strong style="color: #fafafa;">Why it matters:</strong> <span style="color: #a1a1aa;">{html.escape(f['why_matters'])}</span></div>
                    <div><strong style="color: #fafafa;">Remediation:</strong> <span style="color: #10b981;">{html.escape(f['remediation'])}</span></div>
                </div>
                {''.join(ev_html)}
            </div>
        """)

    tasks_html = "".join([
        f"<li style='margin-bottom: 6px;'><strong>{html.escape(t.get('task_name', t.get('agent_id')))}</strong>: {t.get('status')} ({t.get('execution_time_seconds', 0.0)}s) via {t.get('provider_used')} / {t.get('model_used')}</li>"
        for t in tasks
    ])

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>M-ARCH Review Report - {html.escape(project_name)}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #09090b; color: #f4f4f5; margin: 0; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 6px; color: #ffffff; }}
        .meta {{ font-size: 12px; color: #a1a1aa; margin-bottom: 24px; }}
        .summary-card {{ background: #121214; border: 1px solid #27272a; border-radius: 8px; padding: 20px; margin-bottom: 28px; line-height: 1.6; font-size: 14px; }}
        .limitations {{ background: #1c1917; border: 1px solid #44403c; border-radius: 8px; padding: 16px; margin-top: 28px; font-size: 13px; color: #e7e5e4; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>M-ARCH Engineering Review: {html.escape(project_name)}</h1>
        <div class="meta">
            Scope: <strong>{html.escape(question)}</strong> | Profile: <strong>{html.escape(app_type)}</strong> | Mode: <strong>{html.escape(mode.upper())}</strong> | Status: <strong>{html.escape(status.upper())}</strong>
        </div>
        <div class="summary-card">
            <h2 style="font-size: 16px; margin-top: 0; color: #fafafa;">Executive Synthesis</h2>
            <div>{html.escape(summary or 'No critical static findings detected.')}</div>
        </div>
        <h2 style="font-size: 18px; color: #fafafa; margin-bottom: 16px;">Verified Grounded Findings ({len(formatted_findings)})</h2>
        {''.join(findings_html) if findings_html else '<p style="color: #a1a1aa;">No critical static findings detected.</p>'}
        <div class="limitations">
            <h3 style="margin-top: 0; font-size: 14px; color: #fbbf24;">Scope & Technical Limitations</h3>
            <p style="margin: 0;">{html.escape(limitations or 'Conducted via static inspection and RAG retrieval. Project code was not executed.')}</p>
        </div>
        <div style="margin-top: 28px; font-size: 12px; color: #71717a;">
            <h4 style="color: #a1a1aa; margin-bottom: 8px;">Multi-Agent Execution Trace</h4>
            <ul style="padding-left: 18px; margin: 0;">{tasks_html}</ul>
        </div>
    </div>
</body>
</html>"""
