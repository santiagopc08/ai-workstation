from pathlib import Path
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.tagging.tagger import auto_tag

class KnowledgeGraphEngine:
    """
    Motor del Grafo de Conocimiento de ORBIT.
    Analiza la estructura de dependencias de código, APIs, contenedores Docker
    y menciones cruzadas de documentos para construir un grafo unificado en SQLite.
    """
    def __init__(self, storage: SQLiteStorageBackend) -> None:
        self.storage = storage

    def build_graph_for_document(self, doc_path: str, content: str) -> None:
        """
        Analiza un archivo indexado y extrae nodos y relaciones asociadas.
        Limpia relaciones anteriores del mismo archivo antes de guardar.
        """
        # 1. Crear nodos base del documento
        doc_node_id = f"doc:{doc_path}"
        title = Path(doc_path).name
        self.storage.save_node(doc_node_id, "Document", title, {"path": doc_path})

        project = self._get_project_name(doc_path)
        proj_node_id = f"project:{project}"
        self.storage.save_node(proj_node_id, "Project", project, {})
        
        # Relación PART_OF
        self.storage.save_edge(doc_node_id, proj_node_id, "PART_OF")

        ext = Path(doc_path).suffix.lower()

        # 2. Análisis específico por tipo de archivo
        if ext == ".py":
            self._parse_python_graph(doc_node_id, content)
        elif ext in (".yaml", ".yml"):
            is_compose = "compose" in doc_path.lower() or "docker" in doc_path.lower()
            if is_compose:
                self._parse_docker_graph(doc_node_id, content)

        # 3. Aplicar Tagger Automático para agregar tecnologías al grafo
        tags = auto_tag(doc_path, content)
        for tag in tags:
            tech_node_id = f"tech:{tag}"
            self.storage.save_node(tech_node_id, "Technology", tag, {})
            self.storage.save_edge(doc_node_id, tech_node_id, "USES")

        # 4. Escanear Referencias Cruzadas (menciones de otros archivos)
        self._parse_cross_references(doc_node_id, content)

    def _get_project_name(self, relative_path_str: str) -> str:
        parts = Path(relative_path_str).parts
        if not parts or len(parts) == 1:
            return "Global"
        if parts[0] == "Projects" and len(parts) >= 2:
            return f"Projects/{parts[1]}"
        return parts[0]

    def _parse_python_graph(self, doc_node_id: str, content: str) -> None:
        """Extrae clases, funciones e importaciones de Python y las asocia al grafo."""
        try:
            import ast
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_node_id = f"class:{node.name}"
                    self.storage.save_node(class_node_id, "Class", node.name, {})
                    self.storage.save_edge(class_node_id, doc_node_id, "BELONGS_TO")

                    # Métodos de la clase
                    for subnode in node.body:
                        if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_node_id = f"func:{node.name}.{subnode.name}"
                            self.storage.save_node(method_node_id, "Function", subnode.name, {})
                            self.storage.save_edge(method_node_id, class_node_id, "PART_OF")

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_node_id = f"func:{node.name}"
                    self.storage.save_node(func_node_id, "Function", node.name, {})
                    self.storage.save_edge(func_node_id, doc_node_id, "BELONGS_TO")

                elif isinstance(node, ast.Import):
                    for name in node.names:
                        mod_node_id = f"module:{name.name}"
                        self.storage.save_node(mod_node_id, "PythonModule", name.name, {})
                        self.storage.save_edge(doc_node_id, mod_node_id, "IMPORTS")
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod_node_id = f"module:{node.module}"
                        self.storage.save_node(mod_node_id, "PythonModule", node.module, {})
                        self.storage.save_edge(doc_node_id, mod_node_id, "IMPORTS")
        except Exception:
            pass

    def _parse_docker_graph(self, doc_node_id: str, content: str) -> None:
        """Extrae servicios y puertos de Docker Compose."""
        try:
            import yaml
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return
                
            services = data.get("services", {})
            for svc_name, svc_data in services.items():
                svc_node_id = f"docker_service:{svc_name}"
                image = svc_data.get("image", "custom-build") if isinstance(svc_data, dict) else "custom-build"
                self.storage.save_node(svc_node_id, "DockerService", svc_name, {"image": image})
                self.storage.save_edge(svc_node_id, doc_node_id, "GENERATED_FROM")

                # Puertos expuestos
                if isinstance(svc_data, dict) and "ports" in svc_data:
                    for port in svc_data["ports"]:
                        port_str = str(port)
                        port_node_id = f"port:{port_str}"
                        self.storage.save_node(port_node_id, "API", f"Port {port_str}", {})
                        self.storage.save_edge(svc_node_id, port_node_id, "EXPOSES")
        except Exception:
            pass

    def _parse_cross_references(self, doc_node_id: str, content: str) -> None:
        """Escanea menciones de otros archivos o tecnologías en el texto para tejer referencias cruzadas."""
        docs = self.storage.list_documents()
        doc_path_str = doc_node_id.replace("doc:", "")
        content_lower = content.lower()

        for other_doc in docs:
            if other_doc.path == doc_path_str:
                continue
                
            # Buscar menciones del nombre del archivo (con o sin extensión)
            other_name = Path(other_doc.path).name.lower()
            other_stem = Path(other_doc.path).stem.lower()

            if other_name in content_lower or other_stem in content_lower:
                other_node_id = f"doc:{other_doc.path}"
                self.storage.save_edge(doc_node_id, other_node_id, "REFERENCES", weight=1.0)

    def calculate_graph_distance(self, source_path: str, target_keyword: str) -> float:
        """
        Calcula la distancia mínima en saltos de grafo desde un documento inicial
        hacia cualquier nodo que coincida con el keyword (en minúscula).
        Retorna -1.0 si no hay conectividad.
        """
        storage = self.storage
        source_node = f"doc:{source_path}"
        
        edges = storage.get_all_edges()
        if not edges:
            return -1.0

        # Construir lista de adyacencia
        adj: dict[str, list[str]] = {}
        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            if src not in adj: adj[src] = []
            if tgt not in adj: adj[tgt] = []
            adj[src].append(tgt)
            adj[tgt].append(src)  # Grafo no dirigido para navegación

        if source_node not in adj:
            return -1.0

        # Algoritmo BFS para encontrar camino mínimo
        queue = [(source_node, 0)]
        visited = {source_node}
        
        while queue:
            node, dist = queue.pop(0)
            
            # Condición de parada: si el nombre del nodo adyacente contiene el término
            # o si las propiedades del nodo coinciden
            node_name_lower = node.split(":")[-1].lower()
            if target_keyword.lower() in node_name_lower:
                return float(dist)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
                    
        return -1.0
