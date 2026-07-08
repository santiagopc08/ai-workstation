
def calculate_retrieval_metrics(retrieved_text: str, expected_keywords: list[str]) -> dict[str, float]:
    """
    Calcula precisión, recall, F1, cobertura y tasa de alucinación
    del texto recuperado frente a las palabras clave esperadas.
    """
    if not expected_keywords:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "coverage": 1.0,
            "hallucination": 0.0
        }

    text_lower = retrieved_text.lower()
    matches = 0
    for kw in expected_keywords:
        if kw.lower() in text_lower:
            matches += 1

    recall = matches / len(expected_keywords)
    coverage = recall
    
    # Definimos precisión en base a la tasa de acierto directo
    precision = matches / len(expected_keywords)
    
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # La alucinación representa la proporción de información requerida ausente o inventada
    hallucination = max(0.0, 1.0 - recall)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "coverage": coverage,
        "hallucination": hallucination
    }
