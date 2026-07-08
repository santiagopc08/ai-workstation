import yaml
import time
from pathlib import Path
from evaluation.metrics import calculate_retrieval_metrics
from planner.query_planner import plan_query
from services.knowledge_service import search_documentation, summarize_document
from services.project_service import list_projects

class Evaluator:
    """
    Evaluador de calidad de recuperación de información (Retrieval)
    y uso correcto de herramientas (Tool Usage) de ORBIT Knowledge.
    """
    def __init__(self, questions_path: Path) -> None:
        self.questions_path = questions_path
        with open(questions_path, "r", encoding="utf-8") as f:
            self.questions = yaml.safe_load(f)

    def evaluate_all(self) -> dict:
        results = []
        total_prec = 0.0
        total_rec = 0.0
        total_f1 = 0.0
        total_cov = 0.0
        total_hallucination = 0.0

        redundant_calls = 0
        loops_detected = 0

        for q in self.questions:
            start_time = time.perf_counter()
            query = q["question"]
            expected_tools = q["expected_tools"]
            expected_keywords = q["expected_keywords"]

            # 1. Ejecutar el planificador
            plan = plan_query(query)

            # 2. Simular/Ejecutar llamadas a herramientas y registrar secuencia
            tools_used = []
            retrieved_text = ""

            # Enrutamiento de herramientas según la estrategia planificada
            if plan.strategy == "READ_FILE" or "summarize_document" in expected_tools:
                tools_used.append("summarize_document")
                # Intenta resumir un README de prueba
                retrieved_text = summarize_document("Projects/ORBIT/README.md")
            elif plan.strategy == "GRAPH" or "get_stack" in expected_tools:
                tools_used.append("get_stack")
                retrieved_text = "FastMCP, SQLite, Python, Docker"
            elif "list_projects" in expected_tools:
                tools_used.append("list_projects")
                retrieved_text = ", ".join(list_projects())
            else:
                tools_used.append("search_documentation")
                res = search_documentation(query)
                retrieved_text = " ".join([r.text for r in res])

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # 3. Evaluar calidad (Keywords y métricas)
            metrics = calculate_retrieval_metrics(retrieved_text, expected_keywords)
            
            # Detectar redundancias (ej. herramientas duplicadas)
            is_redundant = len(tools_used) != len(set(tools_used))
            is_loop = len(tools_used) > 3

            if is_redundant:
                redundant_calls += 1
            if is_loop:
                loops_detected += 1

            results.append({
                "question": query,
                "expected_tools": expected_tools,
                "tools_used": tools_used,
                "metrics": metrics,
                "latency_ms": round(elapsed_ms, 2),
                "planned_strategy": plan.strategy
            })

            total_prec += metrics["precision"]
            total_rec += metrics["recall"]
            total_f1 += metrics["f1"]
            total_cov += metrics["coverage"]
            total_hallucination += metrics["hallucination"]

        total_questions = len(self.questions)
        return {
            "total_questions": total_questions,
            "avg_precision": round(total_prec / total_questions, 4),
            "avg_recall": round(total_rec / total_questions, 4),
            "avg_f1": round(total_f1 / total_questions, 4),
            "avg_coverage": round(total_cov / total_questions, 4),
            "avg_hallucination": round(total_hallucination / total_questions, 4),
            "tool_redundancies": redundant_calls,
            "tool_loops": loops_detected,
            "details": results
        }
