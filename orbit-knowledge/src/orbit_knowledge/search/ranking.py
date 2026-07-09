import math
import re

class BM25:
    """
    Algoritmo de clasificación de relevancia léxica BM25 implementado
    en Python puro sin dependencias nativas.
    """
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avg_doc_len = 0.0
        self.doc_lens: list[int] = []
        self.doc_term_freqs: list[dict[str, int]] = []
        self.doc_freqs: dict[str, int] = {}
        
        total_len = 0
        for doc in corpus:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            total_len += len(tokens)
            
            freqs: dict[str, int] = {}
            for token in tokens:
                freqs[token] = freqs.get(token, 0) + 1
            self.doc_term_freqs.append(freqs)
            
            for token in freqs:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                
        if self.corpus_size > 0:
            self.avg_doc_len = total_len / self.corpus_size
            
    def _tokenize(self, text: str) -> list[str]:
        # Convertir a minúsculas y extraer tokens alfanuméricos
        return re.findall(r"\w+", text.lower())
        
    def idf(self, term: str) -> float:
        df = self.doc_freqs.get(term, 0)
        # Suavizado clásico de IDF para evitar valores negativos
        return math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))
        
    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        """Calcula el puntaje de similitud BM25 para el documento indicado."""
        score = 0.0
        doc_len = self.doc_lens[doc_idx]
        freqs = self.doc_term_freqs[doc_idx]
        
        for term in query_tokens:
            tf = freqs.get(term, 0)
            if tf == 0:
                continue
            idf_val = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
            score += idf_val * (numerator / denominator)
            
        return score


def calculate_hybrid_score(
    bm25_score: float,
    vector_score: float,
    modified_time: float,
    project_boost: float = 0.0
) -> float:
    """
    Combina BM25 (40%), Vector Score (40%), Recency del archivo (10%)
    y Project Boost (10%) para computar el rango final.
    Acota el resultado estrictamente entre 0.01 y 0.99.
    """
    # 1. Normalizar score BM25 (asumiendo que valores superiores a 15 son extremadamente relevantes)
    normalized_bm25 = min(bm25_score / 15.0, 1.0)
    
    # 2. Recency score (mayor peso para archivos modificados recientemente)
    # Comparar con fecha UNIX actual
    import time
    age_seconds = max(time.time() - modified_time, 0.0)
    # Decaimiento exponencial: vida media de 30 días (2592000 seg)
    recency_score = math.exp(-age_seconds / 2592000.0)
    
    # 3. Sumar pesos de combinación
    final_score = (
        (normalized_bm25 * 0.4) +
        (vector_score * 0.4) +
        (recency_score * 0.1) +
        (project_boost * 0.1)
    )
    
    return min(max(final_score, 0.01), 0.99)
