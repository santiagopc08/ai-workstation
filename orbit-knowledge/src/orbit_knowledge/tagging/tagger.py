import re

# Reglas de etiquetado extensible basadas en expresiones regulares
TAG_RULES: dict[str, list[str]] = {
    "python": [r"\.py$", r"\bimport\s+", r"\bdef\s+\w+\(", r"\bclass\s+\w+"],
    "docker": [r"docker", r"docker-compose", r"compose\.yaml", r"compose\.yml", r"dockerfile"],
    "fastmcp": [r"fastmcp", r"@mcp\.tool", r"@mcp\.resource"],
    "rag": [r"\brag\b", r"embeddings?", r"vectors?", r"chunks?"],
    "api": [r"\bapis?\b", r"endpoints?", r"rest", r"graphql", r"https?", r"\bposts?\b", r"\bgets?\b"],
    "security": [r"\bkeys?\b", r"\btokens?\b", r"\bauth\b", r"passwords?", r"\bjwt\b", r"crypt"],
    "performance": [r"\bperfs?\b", r"caches?", r"latenc\w+", r"benchmarks?", r"speed"],
    "database": [r"sqlite\d?", r"postgres", r"mysql", r"databases?", r"\bdbs?\b", r"\bsql\b"],
    "react": [r"\breact\b", r"\bjsx\b", r"\btsx\b", r"components?"],
    "azure": [r"azure", r"microsoft azure"],
    "aws": [r"aws", r"amazon", r"\bs3\b", r"\bec2\b", r"lambdas?"],
    "terraform": [r"terraform", r"\b\.tf\b", r"tfstate"],
    "logging": [r"logging", r"loggers?", r"\blogs?\b"],
    "architecture": [r"architectures?", r"designs?", r"structures?", r"layers?"]
}

def auto_tag(path: str, content: str) -> list[str]:
    """
    Analiza el nombre de archivo y el contenido de forma no estructurada
    para asociar etiquetas tecnológicas y conceptuales de manera extensible y rápida.
    """
    tags: list[str] = []
    path_lower = path.lower()
    content_lower = content.lower()

    for tag, patterns in TAG_RULES.items():
        for pattern in patterns:
            if re.search(pattern, path_lower) or re.search(pattern, content_lower):
                tags.append(tag)
                break
                
    return sorted(list(set(tags)))
