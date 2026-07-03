"""
Interface web (Streamlit) para o MVP de Modelagem de Ameaças STRIDE.

Permite ao usuário enviar uma imagem de diagrama de arquitetura, executa o
pipeline de detecção de componentes + geração de relatório STRIDE via
Claude API, e exibe o resultado na tela com opção de download.
"""

import logging
import sys
import tempfile
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path. Necessário porque
# `streamlit run app/streamlit_app.py` adiciona a pasta `app/` (e não a raiz)
# ao path, o que quebraria os imports absolutos `stride`/`model`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

from stride.report_generator import gerar_relatorio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(page_title="STRIDE Threat Modeler", page_icon="🛡️", layout="wide")


def main() -> None:
    """Renderiza a interface principal do Streamlit."""
    st.title("🛡️ STRIDE Threat Modeler")
    st.caption("FIAP Software Security — Hackathon FIAP POS TECH, Fase 5")

    st.markdown(
        "Envie uma imagem de **diagrama de arquitetura de software** "
        "(PNG, JPG ou WEBP) para gerar automaticamente um relatório de "
        "Modelagem de Ameaças baseado na metodologia **STRIDE**."
    )

    with st.sidebar:
        st.header("Configurações")
        nome_projeto = st.text_input("Nome do projeto/arquitetura", value="Análise de Arquitetura")
        st.markdown(
            "---\n"
            "Certifique-se de que a variável de ambiente "
            "`ANTHROPIC_API_KEY` está configurada no arquivo `.env`."
        )

    arquivo_enviado = st.file_uploader(
        "Diagrama de arquitetura", type=["png", "jpg", "jpeg", "webp"]
    )

    if arquivo_enviado is None:
        st.info("Aguardando upload de uma imagem para iniciar a análise.")
        return

    st.image(arquivo_enviado, caption="Diagrama enviado", use_container_width=True)

    if st.button("Gerar relatório STRIDE", type="primary"):
        with st.spinner("Analisando arquitetura e gerando relatório..."):
            try:
                caminho_relatorio = _processar_imagem(arquivo_enviado, nome_projeto)
            except Exception as erro:  # noqa: BLE001 - exibido ao usuário final
                logger.exception("Falha ao gerar relatório")
                st.error(f"Erro ao gerar relatório: {erro}")
                return

        st.success("Relatório gerado com sucesso!")
        _exibir_resultado(caminho_relatorio)


def _processar_imagem(arquivo_enviado, nome_projeto: str) -> Path:
    """Salva a imagem enviada em arquivo temporário e gera o relatório.

    Args:
        arquivo_enviado: Objeto de upload retornado pelo `st.file_uploader`.
        nome_projeto: Nome do projeto a ser exibido no relatório.

    Returns:
        Caminho do arquivo Markdown do relatório gerado.
    """
    sufixo = Path(arquivo_enviado.name).suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as arquivo_temp:
        arquivo_temp.write(arquivo_enviado.getvalue())
        caminho_imagem = Path(arquivo_temp.name)

    return gerar_relatorio(caminho_imagem, nome_projeto=nome_projeto)


def _exibir_resultado(caminho_relatorio: Path) -> None:
    """Exibe o conteúdo do relatório e botão de download.

    Args:
        caminho_relatorio: Caminho do arquivo Markdown gerado.
    """
    conteudo = caminho_relatorio.read_text(encoding="utf-8")

    st.download_button(
        label="Baixar relatório (.md)",
        data=conteudo,
        file_name=caminho_relatorio.name,
        mime="text/markdown",
    )

    st.markdown("---")
    st.markdown(conteudo)


if __name__ == "__main__":
    main()
