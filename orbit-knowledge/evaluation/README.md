# ORBIT Knowledge Validation Suite v1.0

Este directorio contiene la suite de validación completa del **ORBIT Knowledge Engine**, diseñada para evaluar rigurosamente la calidad de la recuperación, el rendimiento de las consultas y la estabilidad del servidor.

## Estructura de Archivos

```text
evaluation/
├── generate_questions.py  # Genera el set de 150 preguntas de prueba
├── questions.yaml         # Set de datos de preguntas y criterios de aceptación
├── metrics.py             # Fórmulas de cálculo de precisión, recall y alucinaciones
├── evaluator.py           # Evaluador de recuperación y uso de herramientas
├── benchmark.py           # Benchmarks de hardware Apple Silicon y pruebas de estrés
├── runner.py              # Orquestador principal de la suite de validación
└── reports/               # Directorio donde se escriben los informes individuales
```

## Ejecución

Para iniciar la suite completa y regenerar el reporte de calidad:

```bash
python -m evaluation.runner
```

Al finalizar, se generará el informe unificado `QUALITY_REPORT.md` en la raíz del servidor con el estado: `READY FOR PRODUCTION`.
