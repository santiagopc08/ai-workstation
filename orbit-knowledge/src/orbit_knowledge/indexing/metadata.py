import ast
import json
import re
from typing import Any
from orbit_knowledge.providers.markdown import extract_markdown_metadata

def extract_markdown_metadata_extended(content: str) -> dict[str, Any]:
    """
    Parsea archivos Markdown y extrae títulos, H1-H3, tablas, links,
    bloques de código y conteo de palabras totales.
    """
    base_meta = extract_markdown_metadata(content)
    # Calcular conteo de palabras
    words = content.split()
    base_meta["word_count"] = len(words)
    return base_meta

def extract_python_metadata_extended(content: str) -> dict[str, Any]:
    """
    Parsea código Python utilizando AST. Extrae clases, funciones,
    docstrings, importaciones y decoradores aplicados a clases o funciones.
    """
    classes: list[str] = []
    functions: list[str] = []
    imports: list[str] = []
    decorators: list[str] = []
    docstring = ""
    
    try:
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree) or ""
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                # Extraer decoradores
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                        decorators.append(dec.func.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
                # Extraer decoradores
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                        decorators.append(dec.func.id)
            elif isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception:
        pass
        
    return {
        "classes": classes,
        "functions": functions,
        "imports": imports,
        "decorators": list(set(decorators)),
        "docstring": docstring
    }

def extract_json_metadata_extended(content: str) -> dict[str, Any]:
    """
    Parsea JSON y extrae sus claves raíces y el esquema estructural de tipos.
    """
    try:
        data = json.loads(content)
        keys = list(data.keys()) if isinstance(data, dict) else []
        schema = {}
        if isinstance(data, dict):
            for k, v in data.items():
                schema[k] = type(v).__name__
        return {
            "keys": keys,
            "schema": schema
        }
    except Exception:
        return {"keys": [], "schema": {}}

def extract_docker_metadata_extended(content: str) -> dict[str, Any]:
    """
    Parsea Docker Compose en YAML. Extrae servicios, puertos, imágenes y volúmenes montados.
    """
    try:
        import yaml
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return {"services": [], "ports": [], "images": [], "volumes": []}
            
        services = list(data.get("services", {}).keys())
        ports: list[str] = []
        images: list[str] = []
        volumes: list[str] = []
        
        # Extraer de cada servicio
        for svc_data in data.get("services", {}).values():
            if not isinstance(svc_data, dict):
                continue
            
            # Puertos
            svc_ports = svc_data.get("ports", [])
            if isinstance(svc_ports, list):
                ports.extend(str(p) for p in svc_ports)
                
            # Imagen Docker
            img = svc_data.get("image", "")
            if img:
                images.append(str(img))
                
            # Volúmenes
            svc_vols = svc_data.get("volumes", [])
            if isinstance(svc_vols, list):
                volumes.extend(str(v) for v in svc_vols)
                
        # Volúmenes declarados globalmente
        top_vols = list(data.get("volumes", {}).keys()) if isinstance(data.get("volumes"), dict) else []
        volumes.extend(top_vols)
        
        return {
            "services": services,
            "ports": list(set(ports)),
            "images": list(set(images)),
            "volumes": list(set(volumes))
        }
    except Exception:
        return {"services": [], "ports": [], "images": [], "volumes": []}

def extract_yaml_metadata_generic(content: str) -> dict[str, Any]:
    """
    Parsea archivos YAML genéricos (que no sean compose).
    Extrae claves raíces y anclas (anchors) mediante expresiones regulares.
    """
    root_keys: list[str] = []
    anchors: list[str] = []
    
    try:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            root_keys = list(data.keys())
    except Exception:
        pass
        
    # Buscar anclas (anchors) utilizando una expresión regular (&anchor_name)
    try:
        anchors = list(set(re.findall(r"&([a-zA-Z0-9_-]+)", content)))
    except Exception:
        pass
        
    return {
        "root_keys": root_keys,
        "anchors": anchors
    }
