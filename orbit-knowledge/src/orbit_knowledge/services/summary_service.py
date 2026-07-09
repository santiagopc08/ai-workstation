def extract_sentence_summary(text: str, sentence_count: int = 3) -> str:
    """
    Genera un resumen simple extrayendo las primeras oraciones del texto.
    """
    if not text:
        return ""
    # Dividir texto por oraciones básicas
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return text[:200]
    return ". ".join(sentences[:sentence_count]) + "."
