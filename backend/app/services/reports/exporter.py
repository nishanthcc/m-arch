from typing import Dict, Any, List
from datetime import datetime

def generate_markdown_report(
    project_name: str,
    question: str,
    status: str,
    summary: str,
    limitations: str,
    findings: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]]
) -> str:
    """Generates a comprehensive technical Markdown report."""
    md = [
        f"# M-ARCH Project Engineering Review: {project_name}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Review Inquiry:** {question}  ",
        f"**Execution Status:** {status.upper()}  \n",
        "---",
        "## Executive Summary",
        summary or "No summary provided.",
        "\n---",
        "## Findings & Evidence Grounding",
    ]

    if not findings:
        md.append("_No findings recorded for this review._")
    else:
        for idx, f in enumerate(findings, 1):
            severity = f.get("severity", "info").upper()
            title = f.get("title", "Observation")
            category = f.get("category", "General")
            agent_id = f.get("agent_id", "Agent")
            verification = f.get("verification_status", "static_analysis")
            confidence = f.get("confidence", 0.8)

            md.append(f"### {idx}. [{severity}] {title}")
            md.append(f"- **Category:** {category} | **Agent:** `{agent_id}` | **Verification:** `{verification}` | **Confidence:** `{confidence}`")
            md.append(f"- **Explanation:** {f.get('explanation')}")
            md.append(f"- **Impact:** {f.get('impact')}")
            md.append(f"- **Remediation:** {f.get('remediation')}")

            evidence_items = f.get("evidence_items", [])
            if evidence_items:
                md.append("#### Supporting Evidence:")
                for ev in evidence_items:
                    line_str = f"L{ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else "Global"
                    md.append(f"- **Source:** `{ev.get('display_path')}` ({line_str}) [Method: `{ev.get('retrieval_method')}`]")
                    excerpt = ev.get('excerpt', '').strip()
                    md.append("```text\n" + excerpt + "\n```")
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
    tasks: List[Dict[str, Any]]
) -> str:
    """Generates an Apple HIG-styled printable HTML technical review."""
    findings_html = []
    for idx, f in enumerate(findings, 1):
        sev = f.get("severity", "info").lower()
        badge_color = {
            "critical": "#ef4444",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#3b82f6",
            "informational": "#6b7280"
        }.get(sev, "#6b7280")

        evidence_html = []
        for ev in f.get("evidence_items", []):
            line_str = f"Lines {ev.get('line_start')}-{ev.get('line_end')}" if ev.get('line_start') else ""
            evidence_html.append(f"""
                <div style="background: #1e1e1e; padding: 12px; border-radius: 6px; margin-top: 8px; font-family: monospace; font-size: 13px; color: #e5e7eb; overflow-x: auto;">
                    <div style="color: #9ca3af; margin-bottom: 6px;">Source: <strong>{ev.get('display_path')}</strong> {line_str}</div>
                    <pre style="margin: 0; white-space: pre-wrap;">{ev.get('excerpt', '')}</pre>
                </div>
            """)

        findings_html.append(f"""
            <div style="border: 1px solid #27272a; border-radius: 8px; padding: 18px; margin-bottom: 16px; background: #18181b;">
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 17px; font-weight: 600; color: #fafafa;">{idx}. {f.get('title')}</h3>
                    <span style="background: {badge_color}; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase;">{sev}</span>
                </div>
                <div style="font-size: 12px; color: #a1a1aa; margin-bottom: 12px; font-family: monospace;">
                    Agent: {f.get('agent_id')} | Category: {f.get('category')} | Status: {f.get('verification_status')} | Confidence: {f.get('confidence')}
                </div>
                <p style="color: #d4d4d8; font-size: 14px; line-height: 1.5; margin: 0 0 10px 0;">{f.get('explanation')}</p>
                <div style="font-size: 13px; color: #e4e4e7; margin-bottom: 6px;"><strong>Impact:</strong> {f.get('impact')}</div>
                <div style="font-size: 13px; color: #e4e4e7; margin-bottom: 12px;"><strong>Remediation:</strong> {f.get('remediation')}</div>
                {''.join(evidence_html)}
            </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>M-ARCH Technical Review: {project_name}</title>
    <style>
        body {{
            background: #09090b;
            color: #f4f4f5;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; letter-spacing: -0.5px; }}
        .meta {{ font-size: 13px; color: #a1a1aa; font-family: monospace; margin-bottom: 24px; }}
        .card {{ background: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
        h2 {{ font-size: 20px; border-bottom: 1px solid #27272a; padding-bottom: 8px; margin-top: 32px; }}
        @media print {{
            body {{ background: #fff; color: #000; padding: 20px; }}
            .card {{ border-color: #ddd; background: #fff; color: #000; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>M-ARCH Engineering Review</h1>
        <div class="meta">
            Project: {project_name} | Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Status: {status.upper()}
        </div>

        <div class="card">
            <h3 style="margin-top: 0; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; color: #a1a1aa;">Inquiry</h3>
            <p style="font-size: 16px; margin: 0; font-weight: 500;">{question}</p>
        </div>

        <h2>Executive Summary</h2>
        <div class="card" style="font-size: 15px; line-height: 1.6;">
            {summary.replace(chr(10), '<br>') if summary else "No summary provided."}
        </div>

        <h2>Findings & Evidence Grounding ({len(findings)})</h2>
        {''.join(findings_html) if findings_html else '<p style="color: #a1a1aa;">No findings recorded.</p>'}

        <h2>Scope & Limitations</h2>
        <div class="card" style="font-size: 14px; color: #d4d4d8;">
            {limitations.replace(chr(10), '<br>') if limitations else "Static inspection only. No project code was executed."}
        </div>
    </div>
</body>
</html>
"""
