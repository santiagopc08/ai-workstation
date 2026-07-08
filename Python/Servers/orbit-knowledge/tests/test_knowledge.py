# ruff: noqa: E402
import sys
import shutil
import unittest
import threading
import time
from pathlib import Path

# Agregar la raíz del proyecto y el paquete a sys.path
project_dir = Path(__file__).resolve().parents[1]
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

knowledge_dir = project_dir / "knowledge"
if str(knowledge_dir) not in sys.path:
    sys.path.insert(0, str(knowledge_dir))

# Configurar entorno de pruebas temporal antes de importar
import config
TEST_TEMP_DIR = project_dir / "tests" / "temp_knowledge_v2"
config.settings.ROOT = TEST_TEMP_DIR / "knowledge_root"
config.settings.WATCHER_ENABLED = True
config.settings.WATCHER_INTERVAL_SECONDS = 0.5
config.settings.WORKERS = 2
config.settings.EMBEDDING_PROVIDER = "mock"

# Importación de modelos y utilidades
from indexing.storage import SQLiteStorageBackend
from indexing.hashes import compute_sha256
from indexing.metadata import (
    extract_markdown_metadata_extended,
    extract_python_metadata_extended,
    extract_json_metadata_extended,
    extract_docker_metadata_extended,
    extract_yaml_metadata_generic
)
from indexing.chunker import chunk_document
from indexing.embeddings import get_embedding_provider, MockEmbeddingProvider
from indexing.events import event_bus, DocumentCreated, DocumentUpdated, DocumentDeleted, IndexFinished
from indexing.queue import job_queue, IndexingJob
from indexing.watcher import PollingWatcher
from indexing.builder import IndexBuilder
from search import ranking, content, filename, semantic
from services import project_service, knowledge_service

class TestOrbitIndexerV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.proj_root = config.settings.ROOT
        cls.proj_dir = cls.proj_root / "Projects" / "ORBIT"
        
        cls.md_path = cls.proj_dir / "README.md"
        cls.py_path = cls.proj_dir / "app.py"
        cls.json_path = cls.proj_dir / "meta.json"
        cls.compose_path = cls.proj_dir / "compose.yaml"
        cls.yaml_path = cls.proj_dir / "config.yaml"

    @classmethod
    def tearDownClass(cls) -> None:
        if TEST_TEMP_DIR.exists():
            shutil.rmtree(TEST_TEMP_DIR)

    def setUp(self) -> None:
        # Re-crear directorios limpios
        if TEST_TEMP_DIR.exists():
            shutil.rmtree(TEST_TEMP_DIR)
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.proj_dir.mkdir(parents=True, exist_ok=True)

        # 1. Crear documento Markdown con estructura de H2/H3
        self.md_path.write_text(
            "# ORBIT Project\n"
            "Intro paragraph.\n"
            "## Architecture\n"
            "First H2 text block goes here.\n"
            "### Database\n"
            "Uses SQLite in `.orbit` directory.\n"
            "### Embeddings\n"
            "Allows Ollama, LM Studio or OpenAI.\n"
            "| Option | Port |\n"
            "|---|---|\n"
            "| LMStudio | 1234 |\n"
            "| Ollama | 11434 |\n"
            "Check [link](http://localhost) and ![img](logo.png)",
            encoding="utf-8"
        )
        
        # 2. Crear archivo Python
        self.py_path.write_text(
            "\"\"\"App docstring\"\"\"\n"
            "import os\n"
            "import sys\n\n"
            "@decorator_one\n"
            "class Engine:\n"
            "    def init(self):\n"
            "        pass\n\n"
            "@decorator_two\n"
            "def run_engine():\n"
            "    pass",
            encoding="utf-8"
        )
        
        # 3. Crear archivo JSON
        self.json_path.write_text('{"name": "orbit", "version": "2.0", "active": true}', encoding="utf-8")
        
        # 4. Crear Docker Compose
        self.compose_path.write_text(
            "services:\n"
            "  web:\n"
            "    image: python:3.14-alpine\n"
            "    ports:\n"
            "      - \"8000:8000\"\n"
            "    volumes:\n"
            "      - .:/app\n",
            encoding="utf-8"
        )

        # 5. Crear YAML genérico con anclas
        self.yaml_path.write_text(
            "defaults: &defaults\n"
            "  adapter: sqlite3\n"
            "  timeout: 5000\n"
            "development:\n"
            "  <<: *defaults\n",
            encoding="utf-8"
        )

        # Inicializar el almacenamiento limpio
        self.storage = SQLiteStorageBackend()
        self.builder = IndexBuilder(self.storage)
        self.builder.rebuild_all()

    def test_sqlite_storage(self) -> None:
        """Prueba que el almacenamiento guarde y recupere documentos y chunks."""
        # 1. Recuperar documento
        doc = self.storage.get_document("Projects/ORBIT/README.md")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.project, "Projects/ORBIT")
        self.assertIn("markdown", doc.tags)
        
        # 2. Recuperar chunks
        chunks = self.storage.get_chunks_for_document("Projects/ORBIT/README.md")
        self.assertTrue(len(chunks) > 0)
        
        # 3. Eliminar documento y cascada
        self.storage.delete_document("Projects/ORBIT/README.md")
        self.assertIsNone(self.storage.get_document("Projects/ORBIT/README.md"))
        self.assertEqual(len(self.storage.get_chunks_for_document("Projects/ORBIT/README.md")), 0)

    def test_hashing(self) -> None:
        """Prueba de SHA256."""
        h = compute_sha256(self.md_path)
        self.assertTrue(len(h) == 64)

    def test_metadata_extended(self) -> None:
        """Prueba de los extractores de metadatos extendidos."""
        # 1. Markdown
        meta_md = extract_markdown_metadata_extended(self.md_path.read_text("utf-8"))
        self.assertEqual(meta_md["title"], "ORBIT Project")
        self.assertIn("H2: Architecture", meta_md["headings"])
        self.assertIn("H3: Database", meta_md["headings"])
        self.assertEqual(meta_md["tables_count"], 1)
        self.assertTrue(meta_md["word_count"] > 10)
        
        # 2. Python
        meta_py = extract_python_metadata_extended(self.py_path.read_text("utf-8"))
        self.assertEqual(meta_py["docstring"], "App docstring")
        self.assertIn("Engine", meta_py["classes"])
        self.assertIn("run_engine", meta_py["functions"])
        self.assertIn("decorator_one", meta_py["decorators"])
        self.assertIn("decorator_two", meta_py["decorators"])
        
        # 3. JSON
        meta_json = extract_json_metadata_extended(self.json_path.read_text("utf-8"))
        self.assertEqual(meta_json["schema"]["active"], "bool")
        
        # 4. Docker Compose
        meta_docker = extract_docker_metadata_extended(self.compose_path.read_text("utf-8"))
        self.assertIn("web", meta_docker["services"])
        self.assertIn("python:3.14-alpine", meta_docker["images"])
        self.assertIn("8000:8000", meta_docker["ports"])
        
        # 5. YAML genérico
        meta_yaml = extract_yaml_metadata_generic(self.yaml_path.read_text("utf-8"))
        self.assertIn("defaults", meta_yaml["root_keys"])
        self.assertIn("defaults", meta_yaml["anchors"])

    def test_semantic_chunker(self) -> None:
        """Prueba del fraccionamiento semántico por H2/H3 y AST."""
        # 1. Markdown H2/H3 chunking
        chunks_md = chunk_document("Projects/ORBIT/README.md", "Projects/ORBIT", self.md_path.read_text("utf-8"), chunk_size=100)
        self.assertTrue(len(chunks_md) > 1)
        self.assertEqual(chunks_md[0].section, "Intro")
        
        # 2. Python Class/Function chunking
        chunks_py = chunk_document("Projects/ORBIT/app.py", "Projects/ORBIT", self.py_path.read_text("utf-8"), chunk_size=200)
        self.assertTrue(len(chunks_py) >= 2)
        self.assertIn("class Engine", chunks_py[0].title)

    def test_embedding_adapters(self) -> None:
        """Prueba la fábrica de proveedores y la generación de vectores deterministas (mock)."""
        provider = get_embedding_provider()
        self.assertIsInstance(provider, MockEmbeddingProvider)
        
        v1 = provider.generate_embedding("hello orbit")
        v2 = provider.generate_embedding("hello orbit")
        v3 = provider.generate_embedding("different query")
        
        # Debe ser determinista
        self.assertEqual(v1, v2)
        self.assertNotEqual(v1, v3)
        self.assertEqual(len(v1), 384)

    def test_event_bus(self) -> None:
        """Prueba el correcto funcionamiento del pub-sub de eventos."""
        events_received = []
        def listener(evt):
            events_received.append(evt)
            
        event_bus.subscribe(IndexFinished, listener)
        event_bus.publish(IndexFinished(stats={"ok": True}))
        self.assertEqual(len(events_received), 1)
        self.assertTrue(events_received[0].stats["ok"])

    def test_job_queue_and_workers(self) -> None:
        """Prueba la cola de trabajos concurrente."""
        jobs_processed = []
        lock = threading.Lock()
        
        def cb(job):
            with lock:
                jobs_processed.append(job)
                
        queue = job_queue
        queue.worker_callback = cb
        queue.start()
        try:
            queue.add_job(IndexingJob("index", "dummy_path"))
            time.sleep(0.5)
            with lock:
                self.assertEqual(len(jobs_processed), 1)
                self.assertEqual(jobs_processed[0].path, "dummy_path")
        finally:
            queue.stop()

    def test_watcher_polling(self) -> None:
        """Prueba el PollingWatcher detectando CREATE, MODIFIED, DELETE y enviando eventos."""
        events = []
        lock = threading.Lock()
        
        def on_created(evt):
            with lock:
                events.append("created")
        def on_updated(evt):
            with lock:
                events.append("updated")
        def on_deleted(evt):
            with lock:
                events.append("deleted")
                
        event_bus.subscribe(DocumentCreated, on_created)
        event_bus.subscribe(DocumentUpdated, on_updated)
        event_bus.subscribe(DocumentDeleted, on_deleted)
        
        watcher = PollingWatcher(self.storage)
        watcher.start()
        try:
            # CREATE
            new_file = self.proj_dir / "new_event_file.txt"
            new_file.write_text("Hello event", encoding="utf-8")
            time.sleep(1.2)
            with lock:
                self.assertIn("created", events)
                
            # MODIFIED
            new_file.write_text("Hello event updated", encoding="utf-8")
            time.sleep(1.2)
            with lock:
                self.assertIn("updated", events)
                
            # DELETE
            new_file.unlink()
            time.sleep(1.2)
            with lock:
                self.assertIn("deleted", events)
        finally:
            watcher.stop()

    def test_ranking_bm25_and_hybrid(self) -> None:
        """Prueba los algoritmos BM25 y cálculo de ranking híbrido."""
        # 1. BM25
        corpus = [
            "This is the first document about orbit and sqlite databases",
            "Embeddings are local using ollama or voyage",
            "Docker compose setup python Alpine container"
        ]
        bm = ranking.BM25(corpus)
        score1 = bm.score(["orbit", "sqlite"], 0)
        score2 = bm.score(["orbit", "sqlite"], 1)
        self.assertTrue(score1 > score2)
        self.assertEqual(score2, 0.0)
        
        # 2. Hybrid Score
        time_modified = time.time() - 3600.0 # 1 hora atrás
        score_hybrid = ranking.calculate_hybrid_score(12.5, 0.8, time_modified, 0.1)
        self.assertTrue(0.01 <= score_hybrid <= 0.99)

    def test_search_and_ranking_sqlite(self) -> None:
        """Prueba búsquedas léxicas, semánticas y la integración híbrida con SQLite."""
        # 1. Filename search
        files = filename.search_files("app.py")
        self.assertEqual(files, ["Projects/ORBIT/app.py"])
        
        # 2. Cosine similarity semantic search
        sem_res = semantic.semantic_search("Embeddings")
        self.assertTrue(len(sem_res) > 0)
        
        # 3. Hybrid search
        res = content.search_content("Architecture")
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0].file, "Projects/ORBIT/README.md")

    def test_services_sqlite(self) -> None:
        """Prueba los servicios de proyectos y conocimiento sobre SQLite."""
        # 1. Proyectos
        projs = project_service.list_projects()
        self.assertEqual(projs, ["Projects/ORBIT"])
        
        docs = project_service.project_documents("Projects/ORBIT")
        self.assertEqual(len(docs), 5)
        
        summary = project_service.project_summary("Projects/ORBIT")
        self.assertIn("Resumen del Proyecto: Projects/ORBIT", summary)
        
        meta = project_service.project_metadata("Projects/ORBIT")
        self.assertEqual(meta["files_count"], 5)
        self.assertIn(".yaml", meta["extensions_used"])
        
        # 2. Conocimiento
        found = knowledge_service.find_document("README")
        self.assertEqual(found, ["Projects/ORBIT/README.md"])
        
        doc_sum = knowledge_service.summarize_document("Projects/ORBIT/README.md")
        self.assertIn("Resumen de ORBIT Project", doc_sum)
        
        related = knowledge_service.related_documents("Projects/ORBIT/README.md")
        self.assertTrue(len(related) >= 0)

    def test_auto_tagger(self) -> None:
        """Prueba del etiquetador automático basado en reglas."""
        from tagging.tagger import auto_tag
        tags_py = auto_tag("my_module.py", "def test(): import fastmcp")
        self.assertIn("python", tags_py)
        self.assertIn("fastmcp", tags_py)

        tags_docker = auto_tag("compose.yaml", "image: postgres\nports: 5432")
        self.assertIn("docker", tags_docker)
        self.assertIn("database", tags_docker)

    def test_simhash_fingerprints(self) -> None:
        """Prueba de SimHash y detección de duplicados cercanos."""
        from fingerprints.simhash import SimHash, hamming_distance, are_near_duplicates
        text1 = "Este es un documento de prueba extenso redactado para verificar el correcto funcionamiento de SimHash en ORBIT. " * 5
        text2 = "Este es un documento de prueba extenso redactado para verificar el correcto funcionamiento de SimHash en ORBIT v2. " * 5
        text3 = "Un contenido completamente diferente y sin ninguna relacion con el resto de los textos de la prueba del indexador." * 5


        sh1 = SimHash(text1).fingerprint
        sh2 = SimHash(text2).fingerprint
        sh3 = SimHash(text3).fingerprint

        self.assertEqual(len(sh1), 64)
        self.assertEqual(len(sh2), 64)

        dist12 = hamming_distance(sh1, sh2)
        dist13 = hamming_distance(sh1, sh3)

        self.assertTrue(dist12 < dist13)
        self.assertTrue(are_near_duplicates(text1, text2))
        self.assertFalse(are_near_duplicates(text1, text3))

    def test_query_planner(self) -> None:
        """Prueba del Planificador de Consultas (Query Planner)."""
        from planner.query_planner import plan_query
        
        p1 = plan_query("read README.md")
        self.assertEqual(p1.strategy, "READ_FILE")

        p2 = plan_query("como estan las relaciones de arquitectura y dependencias?")
        self.assertEqual(p2.strategy, "GRAPH")

        p3 = plan_query("class MyClass")
        self.assertEqual(p3.strategy, "BM25")

        p4 = plan_query("que tecnologias se usan en el proyecto orbit y como se comunican entre si?")
        self.assertEqual(p4.strategy, "MULTI_STAGE")

        p5 = plan_query("ChromaDB vector database setup")
        self.assertEqual(p5.strategy, "HYBRID")

    def test_advanced_ranking_engine(self) -> None:
        """Prueba de la fórmula de clasificación avanzada paramétrica."""
        from ranking.engine import calculate_advanced_score
        
        # Caso base muy relevante
        score_high = calculate_advanced_score(
            bm25_score=14.0,
            vector_score=0.9,
            graph_distance=1.0,
            modified_time=time.time(),
            is_exact_match=True,
            tag_matches_count=3,
            project_boost=0.1
        )

        # Caso poco relevante
        score_low = calculate_advanced_score(
            bm25_score=1.0,
            vector_score=0.1,
            graph_distance=5.0,
            modified_time=time.time() - 3600 * 24 * 60, # 60 dias viejo
            is_exact_match=False,
            tag_matches_count=0,
            project_boost=0.0
        )

        self.assertTrue(score_high > score_low)
        self.assertTrue(0.01 <= score_high <= 0.99)
        self.assertTrue(0.01 <= score_low <= 0.99)

    def test_knowledge_graph_nav(self) -> None:
        """Prueba la construcción del grafo y navegación de distancia."""
        from graph.engine import KnowledgeGraphEngine
        
        graph_eng = KnowledgeGraphEngine(self.storage)
        # Limpiar
        with self.storage._get_connection(self.storage.index_db) as conn:
            conn.execute("DELETE FROM nodes")
            conn.execute("DELETE FROM edges")
            conn.commit()

        # Insertar algunos nodos y relaciones de prueba
        self.storage.save_node("doc:app.py", "Document", "app.py", {})
        self.storage.save_node("tech:python", "Technology", "python", {})
        self.storage.save_node("docker_service:web", "DockerService", "web", {})
        
        self.storage.save_edge("doc:app.py", "tech:python", "USES")
        self.storage.save_edge("doc:app.py", "docker_service:web", "DEPENDS_ON")

        # Calcular distancias
        d1 = graph_eng.calculate_graph_distance("app.py", "python")
        d2 = graph_eng.calculate_graph_distance("app.py", "web")
        d3 = graph_eng.calculate_graph_distance("app.py", "nonexistent")

        self.assertEqual(d1, 1.0)
        self.assertEqual(d2, 1.0)
        self.assertEqual(d3, -1.0)

    def test_mcp_registrations(self) -> None:

        """Verifica que las nuevas herramientas y recursos MCP se registren en FastMCP."""
        from fastmcp import FastMCP
        from knowledge.mcp.tools import register_tools
        from knowledge.mcp.resources import register_resources
        from knowledge.mcp.prompts import register_prompts
        import asyncio
        
        dummy = FastMCP("DummyTest")
        register_tools(dummy)
        register_resources(dummy)
        register_prompts(dummy)
        
        tools = [t.name for t in asyncio.run(dummy.list_tools())]
        prompts = [p.name for p in asyncio.run(dummy.list_prompts())]
        
        self.assertIn("list_projects", tools)
        self.assertIn("project_summary", tools)
        self.assertIn("summarize_document", tools)
        self.assertIn("build_index", tools)
        self.assertIn("SummarizeProject", prompts)

if __name__ == "__main__":
    unittest.main()
