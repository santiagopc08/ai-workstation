import argparse
import sys
from pathlib import Path

# Setup paths for absolute imports inside CLI execution
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent

if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))

def serve(args):
    from orbit_knowledge.config import settings
    
    cli_args = {
        "root": args.root,
        "watcher_enabled": args.watcher,
        "logging_level": args.log_level
    }
    settings.load(cli_args)
    
    from orbit_knowledge.server from orbit_knowledge import mcp
    print(f"Starting ORBIT Knowledge MCP Server, serving root: {settings.ROOT}")
    mcp.run()

def run_benchmark(args):
    # Añadir directorios necesarios
    tests_dir = project_dir / "tests"
    if str(tests_dir) not in sys.path:
         sys.path.insert(0, str(tests_dir))
         
    from tests import benchmark
    benchmark.main()

def run_evaluate(args):
    # Añadir directorios necesarios
    evaluation_dir = project_dir / "evaluation"
    if str(evaluation_dir) not in sys.path:
         sys.path.insert(0, str(evaluation_dir))
         
    from evaluation import runner
    runner.main()

def rebuild(args):
    from orbit_knowledge.indexing.engine import indexer_engine
    print("Rebuilding ORBIT Knowledge index databases from scratch...")
    stats = indexer_engine.index_all(rebuild=True)
    print("Rebuild complete. Database status:")
    print(stats)

def doctor(args):
    from orbit_knowledge.doctor import run_doctor
    run_doctor()

def version(args):
    from __init__ import __version__
    print(f"ORBIT Knowledge Engine v{__version__}")

def main():
    parser = argparse.ArgumentParser(prog="orbit-knowledge", description="ORBIT Knowledge CLI Command Center")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # serve
    serve_parser = subparsers.add_parser("serve", help="Inicia el servidor MCP")
    serve_parser.add_argument("--root", type=str, help="Directorio raíz para la base de conocimiento")
    serve_parser.add_argument("--watcher", action="store_true", help="Habilita monitoreo de cambios en archivos")
    serve_parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "TRACE"], help="Nivel de logs de salida")
    
    # benchmark
    subparsers.add_parser("benchmark", help="Ejecuta pruebas de rendimiento y estrés")
    
    # evaluate
    subparsers.add_parser("evaluate", help="Ejecuta la suite de validación completa de RAG/herramientas")
    
    # rebuild
    subparsers.add_parser("rebuild", help="Fuerza un reindexado de todos los documentos")
    
    # doctor
    subparsers.add_parser("doctor", help="Comprueba el estado del sistema y servicios dependientes")
    
    # version
    subparsers.add_parser("version", help="Muestra la versión de ORBIT Knowledge")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve(args)
    elif args.command == "benchmark":
        run_benchmark(args)
    elif args.command == "evaluate":
        run_evaluate(args)
    elif args.command == "rebuild":
        rebuild(args)
    elif args.command == "doctor":
        doctor(args)
    elif args.command == "version":
        version(args)

if __name__ == "__main__":
    main()
