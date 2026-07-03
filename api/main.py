"""
Aplicação FastAPI do MVP de Modelagem de Ameaças STRIDE.

Expõe o pipeline de geração de relatório (`stride.report_generator`) como uma
API HTTP. Execute a partir da raiz do projeto:

    uvicorn api.main:app --reload
"""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from api.routes import analyze

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

app = FastAPI(
    title="STRIDE Threat Modeler API",
    description=(
        "Recebe uma imagem de diagrama de arquitetura e gera automaticamente "
        "um Relatório de Modelagem de Ameaças baseado na metodologia STRIDE."
    ),
    version="1.0.0",
)

app.include_router(analyze.router, tags=["analyze"])


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Verifica se a API está no ar.

    Returns:
        Dicionário com o status do serviço.
    """
    return {"status": "ok"}
