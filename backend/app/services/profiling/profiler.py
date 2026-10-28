import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Project, Source, SourceSnapshot, ProjectProfile

# Language extension mapping
LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".dockerfile": "Dockerfile",
}

# Known framework signatures for imports/manifests
FRAMEWORK_SIGNATURES = [
    {"name": "FastAPI", "category": "web_api", "patterns": [r"from\s+fastapi\s+import", r"import\s+fastapi"], "manifest_pkg": "fastapi"},
    {"name": "Flask", "category": "web_api", "patterns": [r"from\s+flask\s+import", r"import\s+flask"], "manifest_pkg": "flask"},
    {"name": "Django", "category": "web_framework", "patterns": [r"from\s+django\s+import", r"import\s+django"], "manifest_pkg": "django"},
    {"name": "Streamlit", "category": "web_ui", "patterns": [r"import\s+streamlit", r"from\s+streamlit"], "manifest_pkg": "streamlit"},
    {"name": "PyTorch", "category": "ml_framework", "patterns": [r"import\s+torch", r"from\s+torch"], "manifest_pkg": "torch"},
    {"name": "OpenCV", "category": "computer_vision", "patterns": [r"import\s+cv2"], "manifest_pkg": "opencv-python"},
    {"name": "Ultralytics YOLO", "category": "computer_vision", "patterns": [r"from\s+ultralytics\s+import", r"import\s+ultralytics"], "manifest_pkg": "ultralytics"},
    {"name": "Pandas", "category": "data_analysis", "patterns": [r"import\s+pandas"], "manifest_pkg": "pandas"},
    {"name": "Pillow (PIL)", "category": "imaging", "patterns": [r"from\s+PIL\s+import", r"import\s+PIL"], "manifest_pkg": "pillow"},
    {"name": "Scikit-Learn", "category": "machine_learning", "patterns": [r"import\s+sklearn", r"from\s+sklearn"], "manifest_pkg": "scikit-learn"},
    {"name": "NumPy", "category": "numerical_computing", "patterns": [r"import\s+numpy"], "manifest_pkg": "numpy"},
    {"name": "Next.js", "category": "full_stack", "patterns": [r"from\s+['\"]next/", r"require\(['\"]next"], "manifest_pkg": "next"},
    {"name": "React", "category": "frontend", "patterns": [r"from\s+['\"]react['\"]", r"require\(['\"]react['\"]"], "manifest_pkg": "react"},
    {"name": "Vue", "category": "frontend", "patterns": [r"from\s+['\"]vue['\"]", r"require\(['\"]vue['\"]"], "manifest_pkg": "vue"},
    {"name": "Express", "category": "web_api", "patterns": [r"require\(['\"]express['\"]", r"from\s+['\"]express['\"]"], "manifest_pkg": "express"},
    {"name": "SQLAlchemy", "category": "orm", "patterns": [r"from\s+sqlalchemy\s+import", r"import\s+sqlalchemy"], "manifest_pkg": "sqlalchemy"},
    {"name": "Prisma", "category": "orm", "patterns": [r"from\s+['\"]@prisma/client['\"]"], "manifest_pkg": "@prisma/client"},
    {"name": "Pytest", "category": "testing", "patterns": [r"import\s+pytest", r"def\s+test_"], "manifest_pkg": "pytest"},
    {"name": "Jest", "category": "testing", "patterns": [r"describe\(", r"it\(", r"expect\("], "manifest_pkg": "jest"},
    {"name": "Vitest", "category": "testing", "patterns": [r"from\s+['\"]vitest['\"]"], "manifest_pkg": "vitest"},
    {"name": "Docker", "category": "deployment", "patterns": [r"^FROM\s+"], "manifest_pkg": None},
]

# Database signatures
DB_SIGNATURES = [
    {"name": "SQLite", "patterns": [r"sqlite3", r"sqlite\+aiosqlite", r"\.sqlite3?", r"\.db"], "status": "detected"},
    {"name": "PostgreSQL", "patterns": [r"postgresql", r"psycopg2", r"asyncpg", r"pg_"], "status": "detected"},
    {"name": "MySQL", "patterns": [r"mysql", r"pymysql", r"aiomysql"], "status": "detected"},
    {"name": "MongoDB", "patterns": [r"mongodb", r"pymongo", r"motor", r"mongoose"], "status": "detected"},
    {"name": "Redis", "patterns": [r"redis", r"ioredis", r"aioredis"], "status": "detected"},
]

class ProjectProfilerEngine:
    """
    Deterministic, evidence-based project profiler.
    Analyzes project files to generate structured, traceable metadata.
    """

    def analyze_snapshot(
        self,
        snapshot_id: str,
        project_id: str,
        sources: List[Source],
        snapshot_dir: Path,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive deterministic source profiling across all snapshot files.
        """
        # 1. Language Distribution
        lang_stats: Dict[str, Dict[str, Any]] = {}
        total_lines = 0
        total_bytes = 0

        for s in sources:
            ext = Path(s.file_path).suffix.lower()
            lang = LANGUAGE_EXTENSIONS.get(ext, "Other")
            if ext == "" and Path(s.file_path).name.lower() == "dockerfile":
                lang = "Dockerfile"

            if lang not in lang_stats:
                lang_stats[lang] = {
                    "language": lang,
                    "file_count": 0,
                    "line_count": 0,
                    "byte_count": 0,
                    "sample_files": []
                }
            lang_stats[lang]["file_count"] += 1
            lang_stats[lang]["line_count"] += s.line_count
            lang_stats[lang]["byte_count"] += s.file_size
            total_lines += s.line_count
            total_bytes += s.file_size

            if len(lang_stats[lang]["sample_files"]) < 3:
                lang_stats[lang]["sample_files"].append(s.file_path)

        for lang, st in lang_stats.items():
            st["line_percentage"] = round((st["line_count"] / max(1, total_lines)) * 100, 1)
            st["byte_percentage"] = round((st["byte_count"] / max(1, total_bytes)) * 100, 1)

        # 2. Dependency Manifests & Frameworks
        manifests = []
        frameworks = []
        db_tech = []
        test_frameworks = []
        deployment_configs = []
        routes = []
        entrypoints = []
        modules = []
        services = []
        unsupported = []

        manifest_names = {
            "package.json": "npm",
            "package-lock.json": "npm_lock",
            "requirements.txt": "pip",
            "pyproject.toml": "pep518",
            "pipfile": "pipenv",
            "pipfile.lock": "pipenv_lock",
            "cargo.toml": "cargo",
            "cargo.lock": "cargo_lock",
            "go.mod": "go_modules",
            "go.sum": "go_lock",
            "pom.xml": "maven",
        }

        # Scan files for patterns and structures
        for s in sources:
            file_name = Path(s.file_path).name.lower()
            rel_path = s.file_path
            disk_path = Path(s.storage_path) if getattr(s, "storage_path", None) else (snapshot_dir / s.file_path)
            content = ""
            lines: List[str] = []
            if disk_path.exists():
                try:
                    content = disk_path.read_text(encoding="utf-8", errors="replace")
                    lines = content.splitlines()
                except Exception:
                    pass

            # Detect Manifests
            if file_name in manifest_names:
                m_type = manifest_names[file_name]
                lock_present = any(Path(x.file_path).name.lower() in ("package-lock.json", "yarn.lock", "poetry.lock", "uv.lock", "cargo.lock", "pipfile.lock", "go.sum") for x in sources)
                manifests.append({
                    "file_path": rel_path,
                    "manifest_type": m_type,
                    "line_count": s.line_count,
                    "status": "detected",
                    "lockfile_present": lock_present,
                    "evidence": {"file_path": rel_path, "line_start": 1, "line_end": min(len(lines), 30)}
                })

                # Parse package.json for frameworks
                if file_name == "package.json" and content:
                    try:
                        p_data = json.loads(content)
                        all_deps = {**p_data.get("dependencies", {}), **p_data.get("devDependencies", {})}
                        for pkg, ver in all_deps.items():
                            for sig in FRAMEWORK_SIGNATURES:
                                if sig["manifest_pkg"] and sig["manifest_pkg"] == pkg:
                                    frameworks.append({
                                        "name": sig["name"],
                                        "version": str(ver),
                                        "category": sig["category"],
                                        "status": "detected",
                                        "evidence": {"file_path": rel_path, "excerpt": f'"{pkg}": "{ver}"'}
                                    })
                    except Exception:
                        pass

                # Parse requirements.txt / pyproject.toml for python packages
                if file_name in ("requirements.txt", "pyproject.toml") and lines:
                    for idx, line in enumerate(lines, 1):
                        line_strip = line.strip().lower()
                        for sig in FRAMEWORK_SIGNATURES:
                            if sig["manifest_pkg"] and (line_strip.startswith(sig["manifest_pkg"] + "=") or line_strip.startswith(sig["manifest_pkg"] + ">") or line_strip.startswith(sig["manifest_pkg"] + "<") or line_strip == sig["manifest_pkg"]):
                                frameworks.append({
                                    "name": sig["name"],
                                    "version": line.strip(),
                                    "category": sig["category"],
                                    "status": "detected",
                                    "evidence": {"file_path": rel_path, "line": idx, "excerpt": line.strip()}
                                })

            # Detect Entrypoints
            if file_name in ("main.py", "app.py", "index.ts", "server.ts", "index.js", "server.js", "manage.py", "main.go"):
                entrypoints.append({
                    "file_path": rel_path,
                    "file_name": file_name,
                    "status": "detected",
                    "evidence": {"file_path": rel_path, "line": 1, "excerpt": f"Standard application entrypoint: {file_name}"}
                })

            # Detect Services / Controllers / Handlers
            path_parts = Path(rel_path).parts
            if any(p in ("services", "controllers", "handlers", "routes", "api") for p in path_parts):
                services.append({
                    "name": Path(rel_path).stem,
                    "file_path": rel_path,
                    "category": "service_module",
                    "status": "detected",
                    "evidence": {"file_path": rel_path, "line": 1}
                })

            # Detect Route Declarations (FastAPI / Express / Flask)
            if lines and (s.file_type in ("code", "py", "ts", "js", "go") or rel_path.endswith((".py", ".ts", ".js", ".go", ".tsx", ".jsx"))):
                for idx, line in enumerate(lines, 1):
                    # FastAPI / Flask: @app.get('/path') or @router.post('/path')
                    route_m = re.search(r"@(app|router|api)\.(get|post|put|delete|patch|options)\s*\(\s*['\"]([^'\"]+)['\"]", line)
                    if route_m:
                        routes.append({
                            "method": route_m.group(2).upper(),
                            "path": route_m.group(3),
                            "handler_file": rel_path,
                            "line": idx,
                            "status": "detected",
                            "evidence": {"file_path": rel_path, "line": idx, "excerpt": line.strip()}
                        })

                    # Express: app.get('/path', ...)
                    exp_m = re.search(r"\b(app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", line)
                    if exp_m:
                        routes.append({
                            "method": exp_m.group(2).upper(),
                            "path": exp_m.group(3),
                            "handler_file": rel_path,
                            "line": idx,
                            "status": "detected",
                            "evidence": {"file_path": rel_path, "line": idx, "excerpt": line.strip()}
                        })

            # Detect Database Usage
            if content:
                for db in DB_SIGNATURES:
                    for pat in db["patterns"]:
                        if re.search(pat, content, re.IGNORECASE):
                            if not any(d["name"] == db["name"] for d in db_tech):
                                db_tech.append({
                                    "name": db["name"],
                                    "status": "detected",
                                    "evidence": {"file_path": rel_path, "pattern_matched": pat}
                                })
                            break

            # Detect Testing Frameworks
            if "test" in rel_path.lower() or "spec" in rel_path.lower():
                fw = "Pytest/Unittest" if rel_path.endswith(".py") else ("Jest/Vitest" if rel_path.endswith((".ts", ".tsx", ".js")) else "Custom")
                if not any(tf["framework"] == fw for tf in test_frameworks):
                    test_frameworks.append({
                        "framework": fw,
                        "status": "detected",
                        "test_directories": ["tests" if "tests" in rel_path else Path(rel_path).parent.as_posix()],
                        "evidence": {"file_path": rel_path, "line": 1}
                    })

            # Detect Deployment / CI Configurations
            if file_name in ("dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"):
                deployment_configs.append({
                    "type": "Docker Containerization",
                    "file_path": rel_path,
                    "status": "detected",
                    "evidence": {"file_path": rel_path, "line": 1}
                })
            elif ".github/workflows" in rel_path or ".gitlab-ci.yml" in rel_path:
                deployment_configs.append({
                    "type": "CI/CD Automation",
                    "file_path": rel_path,
                    "status": "detected",
                    "evidence": {"file_path": rel_path, "line": 1}
                })

        # Deduplicate frameworks
        unique_frameworks = []
        seen_fws = set()
        for fw in frameworks:
            if fw["name"] not in seen_fws:
                seen_fws.add(fw["name"])
                unique_frameworks.append(fw)

        # 3. Determine Application Type & Likely Purpose
        primary_lang = max(lang_stats.values(), key=lambda x: x["line_count"])["language"] if lang_stats else "Unknown"
        has_routes = len(routes) > 0 or any(f["name"] in ("FastAPI", "Express", "Flask", "Django") for f in unique_frameworks)
        has_frontend = any(f["name"] in ("React", "Vue", "Next.js") for f in unique_frameworks)
        has_ml = any(f["name"] in ("PyTorch", "Ultralytics YOLO", "OpenCV", "Scikit-Learn") for f in unique_frameworks)
        has_streamlit = any(f["name"] == "Streamlit" for f in unique_frameworks)
        has_tests = len(test_frameworks) > 0

        if has_streamlit and has_ml:
            app_type = "Interactive Computer Vision & Machine Learning Application (Streamlit)"
            app_status = "detected"
        elif has_streamlit:
            app_type = "Data Dashboard / Streamlit Application"
            app_status = "detected"
        elif has_ml:
            app_type = "Machine Learning / Computer Vision System"
            app_status = "detected"
        elif has_frontend and has_routes:
            app_type = "Full-Stack Web Application"
            app_status = "detected"
        elif has_routes:
            app_type = "Web API / Microservice"
            app_status = "detected"
        elif has_frontend:
            app_type = "Frontend Web Application"
            app_status = "detected"
        elif any(f["name"] in ("Pytest", "Jest") for f in unique_frameworks) and not has_routes:
            app_type = "Software Library / Core Utility"
            app_status = "inferred"
        else:
            app_type = f"{primary_lang} Application"
            app_status = "inferred"

        # Likely Purpose extraction from README, entrypoint docstrings, or user context
        likely_purpose = "Standard software project."
        purpose_origin = "unknown"

        if user_context and user_context.get("purpose"):
            likely_purpose = user_context["purpose"]
            purpose_origin = "user_supplied"
        else:
            found_readme = False
            for s in sources:
                if Path(s.file_path).name.lower() == "readme.md":
                    disk_path = Path(s.storage_path) if getattr(s, "storage_path", None) else (snapshot_dir / s.file_path)
                    if disk_path.exists():
                        try:
                            rm_text = disk_path.read_text(encoding="utf-8", errors="replace").strip()
                            lines = [ln.strip() for ln in rm_text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                            if lines:
                                likely_purpose = lines[0][:250]
                                purpose_origin = "detected from README.md"
                                found_readme = True
                        except Exception:
                            pass
                    break

            if not found_readme:
                for ep in entrypoints:
                    ep_source = next((s for s in sources if s.file_path == ep["file_path"]), None)
                    if ep_source:
                        disk_path = Path(ep_source.storage_path) if getattr(ep_source, "storage_path", None) else (snapshot_dir / ep_source.file_path)
                        if disk_path.exists():
                            try:
                                ep_lines = disk_path.read_text(encoding="utf-8", errors="replace").splitlines()
                                doc_lines = []
                                in_doc = False
                                for line in ep_lines[:35]:
                                    sline = line.strip()
                                    if sline.startswith('"""') or sline.startswith("'''"):
                                        if not in_doc:
                                            in_doc = True
                                            doc_lines.append(sline.strip("\"'"))
                                        else:
                                            in_doc = False
                                            doc_lines.append(sline.strip("\"'"))
                                            break
                                    elif in_doc:
                                        doc_lines.append(sline)
                                if doc_lines and any(doc_lines):
                                    likely_purpose = " ".join([d for d in doc_lines if d])[:250]
                                    purpose_origin = f"detected from docstring in {ep['file_path']}"
                                    break
                            except Exception:
                                pass

                if purpose_origin == "unknown":
                    if has_streamlit and has_ml:
                        likely_purpose = "Interactive Streamlit web application for machine learning and computer vision inference."
                        purpose_origin = "inferred from source imports and entrypoint"
                    elif has_routes:
                        likely_purpose = f"Backend web service with REST/API routes built using {primary_lang}."
                        purpose_origin = "inferred from source routes and entrypoint"
                    else:
                        likely_purpose = f"Source code repository implemented in {primary_lang}."
                        purpose_origin = "inferred from file inventory"

        # 4. Construct Architecture & Dependency Graph
        # Nodes: System components with evidence grounding
        graph_nodes = []
        graph_edges = []

        # App Node
        app_node_id = "node_app"
        graph_nodes.append({
            "id": app_node_id,
            "label": f"{app_type} ({primary_lang})",
            "type": "application",
            "status": app_status,
            "details": f"{len(sources)} source files, {total_lines} lines of code",
            "evidence": {"file_path": entrypoints[0]["file_path"] if entrypoints else (sources[0].file_path if sources else "root")}
        })

        # Framework Nodes
        for idx, fw in enumerate(unique_frameworks):
            fw_node_id = f"node_fw_{idx}"
            graph_nodes.append({
                "id": fw_node_id,
                "label": f"{fw['name']} {fw.get('version', '')}".strip(),
                "type": "framework",
                "status": fw.get("status", "detected"),
                "details": f"Category: {fw.get('category')}",
                "evidence": fw.get("evidence", {})
            })
            graph_edges.append({
                "id": f"edge_app_{fw_node_id}",
                "source": app_node_id,
                "target": fw_node_id,
                "relationship": "powered_by",
                "status": "detected",
                "label": "framework dependency"
            })

        # Database Node
        for idx, db in enumerate(db_tech):
            db_node_id = f"node_db_{idx}"
            graph_nodes.append({
                "id": db_node_id,
                "label": f"{db['name']} Persistence",
                "type": "database",
                "status": db.get("status", "detected"),
                "details": "Data storage layer",
                "evidence": db.get("evidence", {})
            })
            graph_edges.append({
                "id": f"edge_app_{db_node_id}",
                "source": app_node_id,
                "target": db_node_id,
                "relationship": "queries_database",
                "status": "detected",
                "label": "data persistence"
            })

        # Service / Module Nodes
        for idx, s in enumerate(services[:6]):
            srv_id = f"node_srv_{idx}"
            graph_nodes.append({
                "id": srv_id,
                "label": s["name"],
                "type": "service",
                "status": "detected",
                "details": s["file_path"],
                "evidence": s.get("evidence", {})
            })
            graph_edges.append({
                "id": f"edge_app_{srv_id}",
                "source": app_node_id,
                "target": srv_id,
                "relationship": "orchestrates_service",
                "status": "detected",
                "label": "internal module"
            })

        # Route Group Node
        if routes:
            routes_node_id = "node_routes"
            sample_routes = ", ".join(f"{r['method']} {r['path']}" for r in routes[:3])
            graph_nodes.append({
                "id": routes_node_id,
                "label": f"API Gateway ({len(routes)} routes)",
                "type": "routes",
                "status": "detected",
                "details": f"Endpoints: {sample_routes}...",
                "evidence": routes[0].get("evidence", {})
            })
            graph_edges.append({
                "id": f"edge_app_{routes_node_id}",
                "source": app_node_id,
                "target": routes_node_id,
                "relationship": "exposes_routes",
                "status": "detected",
                "label": "HTTP API endpoints"
            })

        # Test Suite Node
        if test_frameworks:
            test_node_id = "node_tests"
            graph_nodes.append({
                "id": test_node_id,
                "label": f"Automated Tests ({test_frameworks[0]['framework']})",
                "type": "testing",
                "status": "detected",
                "details": f"Test suite present across {len([s for s in sources if 'test' in s.file_path.lower()])} test files",
                "evidence": test_frameworks[0].get("evidence", {})
            })
            graph_edges.append({
                "id": f"edge_app_{test_node_id}",
                "source": app_node_id,
                "target": test_node_id,
                "relationship": "verified_by",
                "status": "detected",
                "label": "quality assurance"
            })

        # Deployment Node
        if deployment_configs:
            dep_node_id = "node_deploy"
            graph_nodes.append({
                "id": dep_node_id,
                "label": deployment_configs[0]["type"],
                "type": "deployment",
                "status": "detected",
                "details": deployment_configs[0]["file_path"],
                "evidence": deployment_configs[0].get("evidence", {})
            })
            graph_edges.append({
                "id": f"edge_app_{dep_node_id}",
                "source": app_node_id,
                "target": dep_node_id,
                "relationship": "packaged_with",
                "status": "detected",
                "label": "container / CI"
            })

        architecture_graph = {
            "nodes": graph_nodes,
            "edges": graph_edges
        }

        # 5. Build Result Profile
        profile_data = {
            "project_id": project_id,
            "snapshot_id": snapshot_id,
            "languages": lang_stats,
            "frameworks": unique_frameworks,
            "application_type": app_type,
            "app_type_status": app_status,
            "likely_purpose": likely_purpose,
            "purpose_origin": purpose_origin,
            "entrypoints": entrypoints,
            "modules": modules,
            "services": services,
            "routes": routes,
            "database_technologies": db_tech,
            "dependency_manifests": manifests,
            "test_frameworks": test_frameworks,
            "deployment_config": deployment_configs,
            "architecture_graph": architecture_graph,
            "unsupported_technologies": unsupported,
            "user_context": user_context or {}
        }

        return profile_data

    async def save_or_update_profile(
        self,
        session: AsyncSession,
        project_id: str,
        snapshot_id: str,
        profile_data: Dict[str, Any]
    ) -> ProjectProfile:
        """Persists profile record linked to snapshot and project."""
        stmt = select(ProjectProfile).where(
            ProjectProfile.project_id == project_id,
            ProjectProfile.snapshot_id == snapshot_id
        )
        res = await session.execute(stmt)
        profile = res.scalar_one_or_none()

        if not profile:
            profile = ProjectProfile(
                project_id=project_id,
                snapshot_id=snapshot_id
            )
            session.add(profile)

        profile.languages = profile_data.get("languages", {})
        profile.frameworks = profile_data.get("frameworks", [])
        profile.application_type = profile_data.get("application_type", "Unknown")
        profile.app_type_status = profile_data.get("app_type_status", "inferred")
        profile.likely_purpose = profile_data.get("likely_purpose")
        profile.entrypoints = profile_data.get("entrypoints", [])
        profile.modules = profile_data.get("modules", [])
        profile.services = profile_data.get("services", [])
        profile.routes = profile_data.get("routes", [])
        profile.database_technologies = profile_data.get("database_technologies", [])
        profile.dependency_manifests = profile_data.get("dependency_manifests", [])
        profile.test_frameworks = profile_data.get("test_frameworks", [])
        profile.deployment_config = profile_data.get("deployment_config", [])
        profile.architecture_graph = profile_data.get("architecture_graph", {})
        profile.unsupported_technologies = profile_data.get("unsupported_technologies", [])
        profile.user_context = profile_data.get("user_context", {})

        await session.commit()
        await session.refresh(profile)
        return profile

project_profiler = ProjectProfilerEngine()
