import yaml
from pathlib import Path

def generate_questions():
    questions = []

    # 1. Arquitectura (30 preguntas)
    for i in range(30):
        questions.append({
            "category": "Arquitectura",
            "question": f"¿Cómo se define la arquitectura de ORBIT en la pregunta de diseño {i}?",
            "expected_tools": ["get_architecture"],
            "expected_keywords": ["arquitectura", "diseño", "ORBIT"],
            "minimum_score": 0.85
        })

    # 2. Tecnologías (20 preguntas)
    for i in range(20):
        questions.append({
            "category": "Tecnologías",
            "question": f"¿Qué tecnologías se declaran en el inventario tecnológico de la consulta {i}?",
            "expected_tools": ["get_stack"],
            "expected_keywords": ["FastMCP", "SQLite", "Python"],
            "minimum_score": 0.90
        })

    # 3. Configuración (20 preguntas)
    for i in range(20):
        questions.append({
            "category": "Configuración",
            "question": f"¿Cuál es el valor configurado de la variable en el sistema {i}?",
            "expected_tools": ["search_documentation"],
            "expected_keywords": ["settings", "configuracion", "val"],
            "minimum_score": 0.80
        })

    # 4. Docker (15 preguntas)
    for i in range(15):
        questions.append({
            "category": "Docker",
            "question": f"¿Qué servicios o puertos de red expone el contenedor Docker en la consulta {i}?",
            "expected_tools": ["get_services"],
            "expected_keywords": ["docker", "servicios", "compose"],
            "minimum_score": 0.85
        })

    # 5. Python (15 preguntas)
    for i in range(15):
        questions.append({
            "category": "Python",
            "question": f"¿Cómo maneja Python los imports y decoradores en el módulo {i}?",
            "expected_tools": ["get_dependencies"],
            "expected_keywords": ["python", "imports", "librerias"],
            "minimum_score": 0.85
        })

    # 6. Servicios (15 preguntas)
    for i in range(15):
        questions.append({
            "category": "Servicios",
            "question": f"¿Cuáles son los proyectos y servicios de conocimiento indexados en la lista {i}?",
            "expected_tools": ["list_projects"],
            "expected_keywords": ["proyectos", "servicios"],
            "minimum_score": 0.80
        })

    # 7. Dependencias (15 preguntas)
    for i in range(15):
        questions.append({
            "category": "Dependencias",
            "question": f"¿Qué dependencias de librerías de terceros se requieren en el entorno {i}?",
            "expected_tools": ["get_dependencies"],
            "expected_keywords": ["dependencias", "requirements", "librerias"],
            "minimum_score": 0.85
        })

    # 8. Documentación (20 preguntas)
    for i in range(20):
        questions.append({
            "category": "Documentación",
            "question": f"¿Cómo se resumen los documentos y READMEs del proyecto en la consulta {i}?",
            "expected_tools": ["summarize_document"],
            "expected_keywords": ["resumen", "README", "documento"],
            "minimum_score": 0.85
        })

    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "questions.yaml", "w", encoding="utf-8") as f:
        yaml.dump(questions, f, allow_unicode=True, sort_keys=False)
        
    print(f"Generadas {len(questions)} preguntas con éxito en {output_dir}/questions.yaml")

if __name__ == "__main__":
    generate_questions()
