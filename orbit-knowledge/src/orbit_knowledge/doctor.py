import sys
import os
import sqlite3
import socket
from pathlib import Path
from orbit_knowledge.config import settings

def check_connection(host: str, port: int) -> bool:
    """Verifica si un puerto TCP está abierto en la máquina local."""
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False

def run_doctor() -> bool:
    """Ejecuta los diagnósticos de salud del sistema."""
    print("==================================================")
    print("          ORBIT KNOWLEDGE DOCTOR DIAGNOSTICS      ")
    print("==================================================")
    
    issues_found = []
    report = []

    # 1. Python Version Check (Requerido >= 3.10)
    py_version = sys.version_info
    py_ok = py_version.major == 3 and py_version.minor >= 10
    status_py = "OK" if py_ok else "WARNING"
    report.append(f"- **Python Version:** {sys.version} ({status_py})")
    if not py_ok:
        issues_found.append("Python version is below 3.10. Issues may occur.")

    # 2. SQLite WAL Check
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()
        sqlite_ok = True
    except Exception:
        sqlite_ok = False
    status_sqlite = "OK" if sqlite_ok else "ERROR"
    report.append(f"- **SQLite WAL Mode Support:** {'Supported (OK)' if sqlite_ok else 'Unsupported (ERROR)'}")
    if not sqlite_ok:
        issues_found.append("SQLite WAL mode is not supported by your python environment.")

    # 3. Knowledge Root Directory existence & permissions
    root_path = Path(settings.ROOT)
    root_exists = root_path.exists()
    r_ok = False
    w_ok = False
    if root_exists:
        r_ok = os.access(root_path, os.R_OK)
        w_ok = os.access(root_path, os.W_OK)
    
    report.append(f"- **Knowledge Root:** `{root_path}`")
    report.append(f"  - Exists: {'YES (OK)' if root_exists else 'NO (ERROR)'}")
    report.append(f"  - Read Permission: {'GRANTED (OK)' if r_ok else 'DENIED (ERROR)'}")
    report.append(f"  - Write Permission: {'GRANTED (OK)' if w_ok else 'DENIED (ERROR)'}")
    
    if not root_exists:
        issues_found.append(f"Knowledge root path '{root_path}' does not exist.")
    elif not r_ok or not w_ok:
        issues_found.append(f"Insufficient permissions on Knowledge root path '{root_path}'.")

    # 4. Cache System Check
    try:
        from orbit_knowledge.cache.lru import LRUCache
        c = LRUCache(5)
        c.set("ping", "pong")
        cache_ok = c.get("ping") == "pong"
    except Exception:
        cache_ok = False
    report.append(f"- **LRU Cache System:** {'Functional (OK)' if cache_ok else 'FAILED (ERROR)'}")
    if not cache_ok:
        issues_found.append("LRU Cache class is broken or missing.")

    # 5. File Watcher config
    report.append(f"- **Background Watcher:** {'Enabled (OK)' if settings.WATCHER_ENABLED else 'Disabled (Standard)'}")

    # 6. Connectivity checks (Open WebUI, ChromaDB, LM Studio)
    # LM Studio default 1234
    lm_ok = check_connection("localhost", 1234)
    # ChromaDB default 8000
    chroma_ok = check_connection("localhost", 8000)
    # Open WebUI default 8080 or 3000
    webui_ok = check_connection("localhost", 8080) or check_connection("localhost", 3000)

    report.append("- **External Connections:**")
    report.append(f"  - LM Studio (Port 1234): {'REACHABLE (OK)' if lm_ok else 'UNREACHABLE (Warning)'}")
    report.append(f"  - ChromaDB (Port 8000): {'REACHABLE (OK)' if chroma_ok else 'UNREACHABLE (Warning)'}")
    report.append(f"  - Open WebUI (Port 8080/3000): {'REACHABLE (OK)' if webui_ok else 'UNREACHABLE (Warning)'}")

    # Escribir reporte
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "doctor_report.md"
    
    md_content = f"""# ORBIT Doctor Diagnostics Report

## Resumen del Sistema
{chr(10).join(report)}

## Problemas Críticos Encontrados
{chr(10).join([f"- [ ] {issue}" for issue in issues_found]) if issues_found else "No se encontraron problemas críticos. ¡El sistema está funcionando al 100%!"}
"""
    try:
        report_file.write_text(md_content, encoding="utf-8")
        print(f"\nReporte de diagnóstico guardado en: {report_file.resolve()}")
    except Exception as e:
        print(f"\nError guardando el reporte en disco: {e}")

    print("\n--------------------------------------------------")
    if issues_found:
        print(f"DIAGNOSTICS FAILED: {len(issues_found)} issues detected.")
        return False
    else:
        print("DIAGNOSTICS PASSED: System is healthy and ready.")
        return True
