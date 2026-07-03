"""
Exportação de relatórios STRIDE (Markdown) para PDF.

Converte o relatório em Markdown para HTML (biblioteca `markdown`) e depois para
PDF (`xhtml2pdf`/pisa) — solução puro-Python, sem dependências nativas, que
funciona no Windows sem instalar GTK/cairo.
"""

import logging
from pathlib import Path

import markdown as md_lib
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

# Estilo simples e legível para o PDF.
CSS_PDF = """
@page { size: A4; margin: 2cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #1a1a1a; line-height: 1.4; }
h1 { font-size: 18pt; color: #2b3a67; border-bottom: 2px solid #2b3a67; padding-bottom: 4px; }
h2 { font-size: 14pt; color: #2b3a67; margin-top: 16px; }
h3 { font-size: 12pt; color: #3f5185; margin-top: 12px; }
strong { color: #000000; }
ul { margin-top: 4px; }
li { margin-bottom: 2px; }
hr { border: 0; border-top: 1px solid #cccccc; }
"""


def _markdown_para_html(texto_md: str) -> str:
    """Converte texto Markdown em um documento HTML estilizado.

    Args:
        texto_md: Conteúdo do relatório em Markdown.

    Returns:
        Documento HTML completo (com CSS embutido) pronto para o conversor PDF.
    """
    corpo = md_lib.markdown(texto_md, extensions=["extra", "sane_lists"])
    return f"<html><head><style>{CSS_PDF}</style></head><body>{corpo}</body></html>"


def exportar_para_pdf(caminho_md: str | Path, caminho_pdf: str | Path | None = None) -> Path:
    """Gera um PDF a partir de um relatório Markdown.

    Args:
        caminho_md: Caminho do arquivo `.md` do relatório.
        caminho_pdf: Caminho de saída do PDF. Se None, usa o mesmo nome/pasta
            do Markdown com extensão `.pdf`.

    Returns:
        Caminho do arquivo PDF gerado.

    Raises:
        FileNotFoundError: Se o arquivo Markdown não existir.
        RuntimeError: Se a conversão para PDF falhar.
    """
    caminho_md = Path(caminho_md)
    if not caminho_md.exists():
        raise FileNotFoundError(f"Relatório Markdown não encontrado: {caminho_md}")

    destino = Path(caminho_pdf) if caminho_pdf else caminho_md.with_suffix(".pdf")
    html = _markdown_para_html(caminho_md.read_text(encoding="utf-8"))

    with destino.open("wb") as saida:
        resultado = pisa.CreatePDF(html, dest=saida, encoding="utf-8")

    if resultado.err:
        raise RuntimeError(f"Falha ao gerar PDF: {resultado.err} erro(s)")

    logger.info("PDF gerado em %s", destino)
    return destino
