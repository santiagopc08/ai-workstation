import hashlib
import re

class SimHash:
    """
    Algoritmo de huella digital de similitud SimHash de 64 bits.
    Permite detectar similitudes entre textos y duplicados cercanos de forma offline sin embeddings.
    """
    def __init__(self, text: str) -> None:
        self.fingerprint: str = self._calculate_simhash(text)
        
    def _calculate_simhash(self, text: str) -> str:
        # Tokenizar el texto (palabras minúsculas)
        features = re.findall(r"\w+", text.lower())
        if not features:
            return "0" * 64
            
        # Pesos por frecuencia de ocurrencia
        weights: dict[str, int] = {}
        for f in features:
            weights[f] = weights.get(f, 0) + 1
            
        vector = [0] * 64
        for feature, weight in weights.items():
            # Obtener hash de 64 bits del feature tomando los primeros 16 caracteres hexadecimales de MD5
            h = int(hashlib.md5(feature.encode("utf-8")).hexdigest()[:16], 16)
            for i in range(64):
                bit = (h >> i) & 1
                if bit:
                    vector[i] += weight
                else:
                    vector[i] -= weight
                    
        fingerprint_bits = []
        for val in vector:
            if val > 0:
                fingerprint_bits.append("1")
            else:
                fingerprint_bits.append("0")
                
        return "".join(fingerprint_bits)


def hamming_distance(f1: str, f2: str) -> int:
    """
    Calcula la distancia de Hamming entre dos huellas SimHash (cantidad de bits divergentes).
    Un valor de <= 3 sobre 64 indica extrema similitud.
    """
    if len(f1) != len(f2):
        return 64
    return sum(c1 != c2 for c1, c2 in zip(f1, f2))


def are_near_duplicates(text1: str, text2: str, threshold: int = 3) -> bool:
    """
    Compara dos textos mediante SimHash y determina si son casi idénticos.
    """
    sh1 = SimHash(text1)
    sh2 = SimHash(text2)
    return hamming_distance(sh1.fingerprint, sh2.fingerprint) <= threshold
