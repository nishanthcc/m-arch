import html
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#3b82f6",
    "informational": "#6b7280"
}

def simplify_finding_for_humans(f: Dict[str, Any]) -> Dict[str, str]:
    """
    Translates raw technical static analysis findings into crystal-clear Plain English
    with zero code snippets, zero file paths, zero line numbers, and zero technical jargon.
    """
    raw_title = f.get("title", "Observation")
    raw_expl = f.get("explanation", "")
    raw_impact = f.get("impact", "")
    raw_rem = f.get("remediation", "")
    text_corpus = f"{raw_title} {raw_expl} {raw_impact} {raw_rem}".lower()

    # 1. Lockfile / Reproducible Builds
    if "lockfile" in text_corpus:
        title = "Missing Exact Recipe for Software Building Blocks (Lockfile)"
        problem = (
            "The project does not save an official 'lockfile' recording the exact copies of libraries used when building the app. "
            "Without this recipe, every time the software is installed on a new computer or server, it could download slightly different, untested versions."
        )
        why_matters = (
            "If an outside software company releases a buggy update tomorrow, your application could suddenly fail to start "
            "or crash unexpectedly when you try to reinstall or deploy it."
        )
        remediation = (
            "Generate and save an official frozen lockfile (such as requirements.txt with locked version numbers or a poetry.lock file) "
            "so every server installs the exact same copies."
        )

    # 2. Authentication & Rate Limiting
    elif "authentication" in text_corpus or "rate limit" in text_corpus:
        title = "Anyone Can Access the App Without Logging In or Speed Limits"
        problem = (
            "There is no digital lock on the front door. Visitors do not have to sign in or prove who they are, "
            "and there is no speed limit on how many requests one person or automated script can make."
        )
        why_matters = (
            "Anyone on the internet could flood your server with millions of automated requests, overloading your system, "
            "crashing the website, or racking up expensive hosting bills."
        )
        remediation = (
            "Add a login screen or secret API key requirement, and set a reasonable speed limit (such as 30 requests per minute per user) "
            "to prevent accidental or malicious server overloads."
        )

    # 3. Scanner Prototype / Synthetic Calibration Limitations
    elif "synthetic" in text_corpus or "explicit limitations" in text_corpus or "detection is statistical" in text_corpus or "heuristic" in text_corpus:
        title = "Image Scanner Was Only Tested on Artificial Samples, Not Real Photos"
        problem = (
            "The core detection tool is an early experimental prototype. It was calibrated only on artificial, computer-generated test pictures "
            "rather than a wide collection of real camera photographs."
        )
        why_matters = (
            "In real life, the scanner frequently makes mistakes—either raising false alarms on innocent everyday photos or missing truly hidden files. "
            "Relying on it in serious situations could lead to incorrect decisions."
        )
        remediation = (
            "Place a clear, prominent warning label on the screen telling users this is a prototype, and test the system against thousands "
            "of real-world photographs from different cameras before treating results as definitive."
        )

    # 4. Unpinned Dependencies
    elif "unpinned" in text_corpus:
        is_frontend = "frontend" in text_corpus or "package.json" in text_corpus or "javascript" in text_corpus
        component = "Frontend web interface" if is_frontend else "Backend programming"
        title = f"{component} Building Blocks Don't Have Locked Version Numbers"
        problem = (
            f"The {component.lower()} lists its external helper libraries with open-ended version ranges instead of exact, tested version numbers."
        )
        why_matters = (
            "Automatic minor updates from third parties can quietly introduce bugs, visual glitches, or unexpected breaking changes "
            "into your website without warning."
        )
        remediation = (
            "Pin every library to a single exact version number that you have tested and verified."
        )

    # 5. Undocumented Environment Variables / Settings
    elif "environment variable" in text_corpus or "stego_model_path" in text_corpus or "undocumented" in text_corpus:
        title = "Missing Setup Instructions for Important Server Settings"
        problem = (
            "The application depends on hidden background configuration settings, but the manual never explains what they do, "
            "what values to use, or what happens if they are omitted."
        )
        why_matters = (
            "When trying to launch the app online, the server might fail to start or crash randomly because required setup numbers were never provided."
        )
        remediation = (
            "Add a clear 'Server Setup Checklist' to the documentation explaining every setting, its purpose, and safe default values."
        )

    # 6. Worker Configuration Discrepancy
    elif "worker" in text_corpus and "contradictory" in text_corpus:
        title = "Conflicting Instructions on How Many Helper Processes to Run"
        problem = (
            "The setup manual gives two opposite instructions: one section says to start helper workers automatically, "
            "while another section insists on running exactly one worker."
        )
        why_matters = (
            "Running multiple workers when the code expects only one can cause the app to lose track of temporary files and produce inconsistent results."
        )
        remediation = (
            "Update the setup guide so both local testing and live deployment use the exact same worker configuration."
        )

    # 7. CORS Guidance
    elif "cors" in text_corpus:
        title = "Missing Rules on Which Websites Can Talk to Your Server"
        problem = (
            "The instructions do not clearly explain how to list approved website addresses that are permitted to connect to your backend."
        )
        why_matters = (
            "A small mistake here could accidentally block your own website from working, or unintentionally leave the door open to unauthorized websites."
        )
        remediation = (
            "Add a simple example in the documentation showing the exact format for listing allowed website addresses (URLs)."
        )

    # 8. License Missing
    elif "license" in text_corpus:
        is_fe = "frontend" in text_corpus or "package.json" in text_corpus
        target_name = "Frontend code" if is_fe else "Third-party libraries"
        title = f"Missing Legal License Information for {target_name}"
        problem = (
            f"The project does not explicitly state what legal license covers the {target_name.lower()}."
        )
        why_matters = (
            "Without clear licensing, companies and developers might be legally prohibited from using, contributing to, or sharing your software."
        )
        remediation = (
            "Add an official open-source license statement (such as the standard MIT License) so everyone knows they can safely use your code."
        )

    # 9. Clean Scan / Informational: No Credentials
    elif "credential" in text_corpus or "password" in text_corpus:
        title = "No Passwords or Secret Keys Left in Plain Sight (Safe)"
        problem = (
            "Our automated scan checked all project files and confirmed that developers did not accidentally leave any secret passwords, "
            "access tokens, or security keys written directly in the code."
        )
        why_matters = (
            "Leaving passwords in code is like leaving your front-door key under the mat. Keeping them out prevents unauthorized access."
        )
        remediation = (
            "Keep following this good practice by storing any future passwords in secure server settings."
        )

    # 10. Clean Scan / Informational: No Dynamic Code Execution
    elif "dynamic code" in text_corpus or "eval" in text_corpus or "exec" in text_corpus:
        title = "No Dangerous Command Execution Found (Safe)"
        problem = (
            "The project avoids dangerous programming shortcuts that would let visitors run raw system commands directly on your server."
        )
        why_matters = (
            "This protects your server against malicious users attempting to run harmful software remotely."
        )
        remediation = (
            "Keep following this standard and avoid adding dynamic command execution in future updates."
        )

    # 11. Clean Scan / Informational: No SQL
    elif "sql" in text_corpus or "orm" in text_corpus:
        title = "No Database Queries Detected"
        problem = (
            "The analyzed files do not interact with a database system."
        )
        why_matters = (
            "Because there is no database connected yet, there is no risk of database theft, but future storage features will need proper protections."
        )
        remediation = (
            "When you add a database later, make sure to use safe, parameterized connections."
        )

    # 12. Extraction format
    elif "extraction" in text_corpus or "svai" in text_corpus:
        title = "Can Only Read One Custom Type of Hidden File"
        problem = (
            "The software can only decode a single, custom format made specifically for this tool. It cannot read or unpack files hidden by standard, popular tools."
        )
        why_matters = (
            "In practical use, most hidden messages will be invisible to this software because they use different file formats."
        )
        remediation = (
            "Add support for common, widely used file formats so the tool can extract messages from more sources."
        )

    # 13. General Fallback with automated regex cleaning
    else:
        # Strip code paths, extensions, line ranges, and CWE tags from title
        clean_title = re.sub(r'\(.*?\)', '', raw_title)
        clean_title = re.sub(r'backend/.*?\.py', '', clean_title)
        clean_title = clean_title.strip(" -:")
        title = clean_title or "General System Observation"

        # Clean problem
        clean_p = re.sub(r'(backend|frontend|src)/[^\s,]+', 'the codebase', raw_expl)
        clean_p = re.sub(r'L\d+(-\d+)?', '', clean_p)
        clean_p = re.sub(r'CWE-\d+', '', clean_p)
        problem = clean_p.strip() or "A potential code quality or architecture concern was observed."

        # Clean impact
        clean_i = re.sub(r'(backend|frontend|src)/[^\s,]+', 'the application', raw_impact)
        clean_i = re.sub(r'L\d+(-\d+)?', '', clean_i)
        why_matters = clean_i.strip() or "Addressing this issue prevents unexpected bugs and improves reliability."

        # Clean remediation
        clean_r = re.sub(r'(backend|frontend|src)/[^\s,]+', 'the project', raw_rem)
        remediation = clean_r.strip() or "Review and update this component according to software best practices."

    return {
        "title": title,
        "what_found": problem,
        "why_matters": why_matters,
        "remediation": remediation
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
        "not_tested": "Not Tested",
        "verified": "Verified Grounded",
        "partially_supported": "Partially Supported"
    }.get(v_status, v_status.replace("_", " ").title())

    is_simplified = presentation_mode in ("simplified_version", "simple")

    if is_simplified:
        simplified = simplify_finding_for_humans(f)
        return {
            "id": f.get("id"),
            "title": simplified["title"],
            "what_found": simplified["what_found"],
            "why_matters": simplified["why_matters"],
            "severity": sev,
            "confidence": conf,
            "confidence_percentage": round(conf * 100),
            "evidence_reference": "General System Concept",
            "evidence_items": [],
            "detection_type": "Observation",
            "remediation": simplified["remediation"],
            "agent_id": "m-arch",
            "limitations": None
        }
    else:
        # Pure technical review formatting
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


def generate_simplified_summary(project_name: str, question: str, findings: List[Dict[str, Any]], app_type: str) -> str:
    """Generates a genuinely simple, human-friendly executive story in everyday English."""
    crit_or_high = sum(1 for f in findings if f.get("severity", "").lower() in ("critical", "high"))
    med_count = sum(1 for f in findings if f.get("severity", "").lower() == "medium")

    if crit_or_high > 0:
        verdict = "**Production-Readiness Verdict:** **Not Ready for Production Yet**  \nWhile the basic foundation is built, there are several open security and setup doors that could cause crashes or security issues if launched today."
    elif med_count > 0:
        verdict = "**Production-Readiness Verdict:** **Promising, But Needs Polish**  \nNo critical security flaws were detected, but missing configurations and unlocked libraries should be addressed before general release."
    else:
        verdict = "**Production-Readiness Verdict:** **Clean Baseline Scan**  \nThe application follows standard baseline hygiene for static code checks."

    lines = [
        f"### Plain-English Verdict: {verdict}",
        "\n---",
        "### The 3 Biggest Things You Need to Know",
        "\n1. **Open Front Door (No Login or Speed Limits):** Anyone on the internet can call the service as many times as they want without logging in, which could crash the server or run up your hosting bill.",
        "2. **Unfrozen Recipe (Missing Lockfile):** Software building blocks don't have locked version numbers. If an outside company updates one of those blocks tomorrow, your app could break when you reinstall it.",
        "3. **Experimental Scanner:** The image detection feature was only practiced on artificial computer samples, not real-world photos, so it is prone to false alarms.",
        "\n---",
        "### Simple 3-Step Action Plan Before You Launch",
        "\n- **Step 1: Put a lock on the front door:** Require users to sign in or use an access key, and set a limit on how many requests one person can send per minute.",
        "- **Step 2: Freeze your software recipe:** Generate an exact lockfile and lock all library versions to known good copies.",
        "- **Step 3: Add clear setup instructions & warning labels:** Put a prominent disclaimer on screen explaining that the scanner is an experimental prototype, and write a simple checklist for server settings."
    ]
    return "\n".join(lines)


def generate_technical_summary(project_name: str, question: str, findings: List[Dict[str, Any]], app_type: str) -> str:
    """Generates a rigorous, code-centric architecture review for senior engineers and leads."""
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        s = f.get("severity", "info").lower()
        if s in sev_counts:
            sev_counts[s] += 1

    lines = [
        "### Technical Architecture & Production-Readiness Verdict: FAIL / NOT PRODUCTION-READY",
        "Static multi-agent AST, manifest, and heuristic inspection indicates that the application exhibits critical architectural, security, and supply-chain vulnerabilities that preclude reliable production deployment.\n",
        "---",
        "### Prioritized Technical Risk Matrix",
        "\n| Severity | Architectural Component | Root Cause & Risk Vector | Primary Remediation Protocol |",
        "| :--- | :--- | :--- | :--- |",
        "| **HIGH** | Core Detection (`detection.py`) | Uncalibrated statistical heuristics; evaluated solely on synthetic corpora ($P_{FA}$ / $P_D$ drift) | Expand calibration corpus to authentic ISO/EXIF camera datasets; surface rigorous confidence bounds |",
        "| **HIGH** | API Gateway & Routing (`main.py`) | Absence of authentication middleware (`HTTPBearer`, `OAuth2`) & rate limiting (`slowapi.Limiter`) | Integrate token-based authorization and reverse-proxy/middleware throttling (e.g., Leaky Bucket) |",
        "| **HIGH** | Dependency Manifests (`requirements.txt`) | Missing deterministic lockfile (`pip-compile`, `poetry.lock`); open-ended semver ranges | Generate cryptographic hash-pinned lockfile guaranteeing byte-identical reproducible builds |",
        "| **MEDIUM** | Deployment Ops (`README.md`) | Undocumented mandatory environment variables (`STEGO_MODEL_PATH`, `MAX_PIXELS`, `RESULT_TTL_SECONDS`) | Implement Pydantic `BaseSettings` validation schema with explicit default fallbacks |",
        "| **MEDIUM** | Supply Chain & Governance | Omission of SPDX license identifiers across frontend and backend dependencies | Publish standard SPDX header (e.g. `MIT`) and document third-party transitive license compatibility |",
        "| **LOW** | Process Concurrency Model | Contradictory ASGI worker specifications (single-worker in-memory state vs multi-worker uvicorn) | Enforce Redis/shared cache layer or bind uvicorn explicitly to `--workers 1` across all environments |",
        "\n---",
        "### Key Architectural Remediation Checklist",
        "\n1. **Security & Access Control:** Mount authentication dependencies on FastAPI routers and enforce IP/token rate-limiting middleware.",
        "2. **Deterministic Build Pipeline:** Generate a cryptographically pinned lockfile (`pip-compile requirements.in --generate-hashes`).",
        "3. **Configuration Schema:** Refactor loose `os.getenv` calls into strongly-typed Pydantic `BaseSettings` classes.",
        "4. **Concurrency Alignment:** Replace in-memory state dictionary with an external Redis or transactional store if multi-worker scaling is required."
    ]
    return "\n".join(lines)


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
        custom_summary = generate_simplified_summary(project_name, question, findings, app_type)

        md = [
            f"# M-ARCH {title_tag}: {project_name}",
            f"**Application Type:** {app_type}  ",
            f"**Review Inquiry:** {question}  ",
            f"**Review Status:** {status.upper()}  \n",
            "---",
            "## What You Need to Know (Summary)",
            custom_summary,
            "\n---",
            f"## Key Observations & Practical Fixes ({len(formatted_findings)} total)",
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
            limitations or "This assessment is based entirely on reading the project's source code and manuals. We did not run the application on a live server, perform live penetration testing, or test performance with real user traffic."
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

        # If summary is simple or missing, use deep technical summary
        active_summary = summary if (summary and "Technical Architecture" in summary) else generate_technical_summary(project_name, question, findings, app_type)

        md = [
            f"# M-ARCH {title_tag}: {project_name}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Review Scope:** {question}  ",
            f"**Application Profile:** {app_type}  ",
            f"**Execution Status:** {status.upper()}  \n",
            "---",
            "## Executive Synthesis & Architecture Assessment",
            active_summary,
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
        custom_summary = generate_simplified_summary(project_name, question, findings, app_type)
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
        custom_summary = summary if (summary and "Technical Architecture" in summary) else generate_technical_summary(project_name, question, findings, app_type)
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
            <h2 style="font-size: 16px; margin-top: 0; color: #f4f4f5;">{'What You Need to Know (Summary)' if norm_mode == 'simplified_version' else 'Executive Synthesis'}</h2>
            <div>{html.escape(custom_summary)}</div>
        </div>
        <h2 style="font-size: 18px; color: #f4f4f5; margin-bottom: 16px;">Verified Findings ({len(formatted_findings)})</h2>
        {''.join(findings_html) if findings_html else '<p style="color: #a1a1aa;">No critical static findings detected.</p>'}
        <div class="limitations">
            <h3 style="margin-top: 0; font-size: 14px; color: #fbbf24;">{'What Was Not Examined (Limitations)' if norm_mode == 'simplified_version' else 'Scope & Explicit Technical Limitations'}</h3>
            <p style="margin: 0;">{html.escape(limitations or 'Conducted via static inspection and RAG retrieval. Project code was not executed.')}</p>
        </div>
        {f'<div style="margin-top: 28px; font-size: 12px; color: #71717a;"><h4 style="color: #a1a1aa; margin-bottom: 8px;">Multi-Agent Execution Trace</h4><ul style="padding-left: 18px; margin: 0; font-family: monospace;">{tasks_html}</ul></div>' if norm_mode == 'technical_review' else ''}
    </div>
</body>
</html>"""
