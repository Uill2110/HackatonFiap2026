"""
Rota de análise: recebe uma imagem de diagrama de arquitetura e devolve o
Relatório de Modelagem de Ameaças STRIDE gerado pelo pipeline.

Expõe `stride.report_generator.gerar_relatorio` via `POST /analyze`.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from stride.report_generator import gerar_relatorio

logger = logging.getLogger(__name__)

router = APIRouter()

EXTENSOES_SUPORTADAS: set[str] = {".png", ".jpg", ".jpeg", ".webp"}


class RelatorioResponse(BaseModel):
    """Resposta da análise com o relatório STRIDE em Markdown.

    Attributes:
        projeto: Nome do projeto/arquitetura analisado.
        arquivo: Nome do arquivo de imagem enviado.
        relatorio_markdown: Conteúdo completo do relatório em Markdown.
        caminho_relatorio: Caminho do arquivo `.md` salvo no servidor.
    """

    projeto: str
    arquivo: str
    relatorio_markdown: str
    caminho_relatorio: str


def _salvar_upload_temporario(arquivo: UploadFile) -> Path:
    """Salva o upload em arquivo temporário, validando a extensão.

    Args:
        arquivo: Arquivo de imagem recebido na requisição.

    Returns:
        Caminho do arquivo temporário gravado em disco.

    Raises:
        HTTPException: Se a extensão da imagem não for suportada.
    """
    sufixo = Path(arquivo.filename or "").suffix.lower()
    if sufixo not in EXTENSOES_SUPORTADAS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Extensão '{sufixo}' não suportada. "
                f"Use uma das: {', '.join(sorted(EXTENSOES_SUPORTADAS))}."
            ),
        )

    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as temp:
        temp.write(arquivo.file.read())
        return Path(temp.name)


@router.post("/analyze", response_model=RelatorioResponse)
async def analisar_arquitetura(
    imagem: UploadFile = File(..., description="Imagem do diagrama de arquitetura"),
    nome_projeto: str = Form("Análise de Arquitetura"),
) -> RelatorioResponse:
    """Gera o relatório STRIDE a partir de uma imagem de diagrama.

    Args:
        imagem: Arquivo de imagem (PNG, JPG ou WEBP) do diagrama.
        nome_projeto: Nome do projeto/arquitetura para o cabeçalho do relatório.

    Returns:
        Objeto com o relatório em Markdown e metadados.

    Raises:
        HTTPException: Em caso de extensão inválida ou falha no pipeline.
    """
    caminho_imagem = _salvar_upload_temporario(imagem)

    try:
        caminho_relatorio = gerar_relatorio(caminho_imagem, nome_projeto=nome_projeto)
    except FileNotFoundError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    except RuntimeError as erro:
        raise HTTPException(status_code=502, detail=str(erro)) from erro
    except Exception as erro:  # noqa: BLE001 - converte falha inesperada em 500
        logger.exception("Falha ao gerar relatório")
        raise HTTPException(status_code=500, detail=f"Erro interno: {erro}") from erro
    finally:
        caminho_imagem.unlink(missing_ok=True)

    return RelatorioResponse(
        projeto=nome_projeto,
        arquivo=imagem.filename or caminho_imagem.name,
        relatorio_markdown=caminho_relatorio.read_text(encoding="utf-8"),
        caminho_relatorio=str(caminho_relatorio),
    )


@router.post("/analyze/download")
async def analisar_e_baixar(
    imagem: UploadFile = File(..., description="Imagem do diagrama de arquitetura"),
    nome_projeto: str = Form("Análise de Arquitetura"),
) -> FileResponse:
    """Gera o relatório STRIDE e devolve o arquivo `.md` para download.

    Args:
        imagem: Arquivo de imagem (PNG, JPG ou WEBP) do diagrama.
        nome_projeto: Nome do projeto/arquitetura para o cabeçalho do relatório.

    Returns:
        Resposta de arquivo com o relatório Markdown como anexo.

    Raises:
        HTTPException: Em caso de extensão inválida ou falha no pipeline.
    """
    caminho_imagem = _salvar_upload_temporario(imagem)

    try:
        caminho_relatorio = gerar_relatorio(caminho_imagem, nome_projeto=nome_projeto)
    except FileNotFoundError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    except RuntimeError as erro:
        raise HTTPException(status_code=502, detail=str(erro)) from erro
    except Exception as erro:  # noqa: BLE001 - converte falha inesperada em 500
        logger.exception("Falha ao gerar relatório")
        raise HTTPException(status_code=500, detail=f"Erro interno: {erro}") from erro
    finally:
        caminho_imagem.unlink(missing_ok=True)

    return FileResponse(
        path=caminho_relatorio,
        media_type="text/markdown",
        filename=caminho_relatorio.name,
    )
