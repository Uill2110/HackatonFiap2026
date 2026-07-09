"""
Interface web (Streamlit) para o MVP de Modelagem de Ameaças STRIDE.

Permite enviar uma imagem de diagrama de arquitetura, executa o pipeline de
detecção de componentes + geração de relatório STRIDE (via provedor de LLM
configurado) e apresenta o resultado como um painel com download (.md e .pdf).
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path. Necessário porque
# `streamlit run app/streamlit_app.py` adiciona a pasta `app/` (e não a raiz)
# ao path, o que quebraria os imports absolutos `stride`/`model`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import markdown as _markdown
import streamlit as st
from dotenv import load_dotenv

from stride.knowledge_base import CATEGORIAS_STRIDE
from stride.llm import PROVEDOR_PADRAO
from stride.report_generator import gerar_relatorio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(
    page_title="STRIDE Threat Modeler",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cor por categoria STRIDE — sistema derivado da própria metodologia, usado como
# assinatura visual (legenda + selos).
STRIDE_CORES = {
    "S": "#F472B6",  # Spoofing
    "T": "#FB923C",  # Tampering
    "R": "#FACC15",  # Repudiation
    "I": "#38BDF8",  # Information Disclosure
    "D": "#A78BFA",  # Denial of Service
    "E": "#F87171",  # Elevation of Privilege
}

_PROVEDORES = {
    "anthropic": ("Anthropic · Claude", "ANTHROPIC_API_KEY"),
    "openai": ("OpenAI · GPT", "OPENAI_API_KEY"),
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&display=swap');

:root{
  --bg:#0E1117; --panel:#161A2B; --panel2:#1C2136;
  --border:rgba(255,255,255,.08); --text:#E6E8F0; --muted:#8A90A6;
  --brand:#6366F1; --cyan:#22D3EE;
}
#MainMenu, footer, [data-testid="stToolbar"] {visibility:hidden;}
[data-testid="stDecoration"]{display:none;}
.block-container{padding-top:1.6rem; padding-bottom:3rem; max-width:1180px;}

/* Hero */
.app-hero{
  position:relative; overflow:hidden; border:1px solid var(--border);
  border-radius:18px; padding:24px 28px; margin-bottom:6px;
  display:flex; align-items:center; justify-content:space-between; gap:18px;
  background:
    radial-gradient(1100px 200px at 0% 0%, rgba(99,102,241,.18), transparent 60%),
    linear-gradient(180deg, var(--panel), var(--bg));
}
.app-hero::before{content:""; position:absolute; left:0; top:0; bottom:0; width:4px;
  background:linear-gradient(180deg, var(--brand), var(--cyan));}
.hero-left{display:flex; align-items:center; gap:16px;}
.hero-badge{width:54px; height:54px; border-radius:15px; display:grid; place-items:center;
  font-size:27px; border:1px solid var(--border);
  background:linear-gradient(135deg, rgba(99,102,241,.28), rgba(34,211,238,.14));}
.hero-eyebrow{font:600 11px/1 'Space Grotesk',sans-serif; letter-spacing:.22em;
  text-transform:uppercase; color:var(--cyan);}
.hero-title{font:700 30px/1.05 'Space Grotesk',sans-serif; letter-spacing:-.01em; margin:7px 0 5px;}
.hero-sub{color:var(--muted); font-size:13.5px; max-width:560px;}
.chip{display:inline-flex; align-items:center; gap:8px; padding:8px 13px; border-radius:999px;
  border:1px solid var(--border); background:var(--panel2); font-size:12.5px; white-space:nowrap;}
.dot{width:8px; height:8px; border-radius:50%;}
.dot.ok{background:#34D399; box-shadow:0 0 0 3px rgba(52,211,153,.18);}
.dot.warn{background:#F5A524; box-shadow:0 0 0 3px rgba(245,165,36,.18);}

/* Rótulo de seção */
.sec{font:600 11px/1 'Space Grotesk',sans-serif; letter-spacing:.2em; text-transform:uppercase;
  color:var(--muted); margin:26px 0 10px;}

/* Stat tiles */
.stat{border:1px solid var(--border); border-radius:14px; padding:16px 18px; height:100%;
  background:var(--panel); position:relative; overflow:hidden;}
.stat::before{content:""; position:absolute; top:0; left:0; right:0; height:3px;
  background:var(--accent,var(--brand));}
.stat .num{font:700 30px/1 'Space Grotesk',sans-serif;}
.stat .lbl{color:var(--muted); font-size:12.5px; margin-top:6px;}

/* Chips de componentes */
.chips{display:flex; flex-wrap:wrap; gap:8px;}
.pill{display:inline-flex; align-items:center; gap:8px; padding:7px 13px; border-radius:999px;
  border:1px solid var(--border); background:var(--panel2); font-size:13px;}
.pill .d{width:7px; height:7px; border-radius:50%; background:var(--cyan);}

/* Legenda STRIDE (assinatura) */
.stride{display:flex; flex-direction:column; gap:9px; margin-top:4px;}
.stride-item{display:flex; align-items:center; gap:10px; font-size:12px; color:var(--muted);}
.badge{width:24px; height:24px; border-radius:7px; display:grid; place-items:center;
  font:700 12px/1 'Space Grotesk',sans-serif; color:#0B0E16; flex:0 0 auto;}

/* Placeholder / empty state */
.drop{border:1px dashed var(--border); border-radius:16px; padding:34px 26px; text-align:center;
  background:linear-gradient(180deg, var(--panel), var(--bg)); color:var(--muted);}
.drop .ic{font-size:32px;}
.drop b{color:var(--text);}

/* Botões */
.stButton>button, .stDownloadButton>button{border-radius:11px; font-weight:600; border:1px solid var(--border);}
.stButton>button[kind="primary"]{border:none; color:#fff;
  background:linear-gradient(135deg, var(--brand), #7C3AED); box-shadow:0 8px 24px rgba(99,102,241,.35);}
.stDownloadButton>button{width:100%; background:var(--panel2); color:var(--text);}

/* Relatório renderizado */
.report{border:1px solid var(--border); border-radius:16px; padding:4px 26px 22px; background:var(--panel);}
.report h1{display:none;}
.report h2{font:700 18px/1.2 'Space Grotesk',sans-serif; margin-top:26px; padding-top:16px;
  border-top:1px solid var(--border);}
.report h3{font:600 15px/1.25 'Space Grotesk',sans-serif; margin-top:20px; padding-left:12px;
  border-left:3px solid var(--brand);}
.report strong{color:#fff;}

[data-testid="stFileUploaderDropzone"]{border-radius:14px; border:1px dashed var(--border);
  background:var(--panel);}
</style>
"""


def _resolver_provedor() -> tuple[str, str | None, str | None]:
    """Retorna (chave_provedor, nome_exibicao, variavel_chave).

    nome/variavel são None se o `LLM_PROVIDER` for inválido.
    """
    provedor = os.environ.get("LLM_PROVIDER", PROVEDOR_PADRAO).strip().lower()
    nome, variavel = _PROVEDORES.get(provedor, (None, None))
    return provedor, nome, variavel


def _hero() -> None:
    """Renderiza o cabeçalho de marca com o chip do provedor ativo."""
    provedor, nome, _ = _resolver_provedor()
    if nome:
        chip = f'<span class="chip"><span class="dot ok"></span>{nome}</span>'
    else:
        chip = (
            f'<span class="chip"><span class="dot warn"></span>'
            f'LLM_PROVIDER inválido: {provedor}</span>'
        )
    st.markdown(
        '<div class="app-hero"><div class="hero-left">'
        '<div class="hero-badge">🛡️</div><div>'
        '<div class="hero-eyebrow">FIAP Software Security</div>'
        '<div class="hero-title">STRIDE Threat Modeler</div>'
        '<div class="hero-sub">Envie um diagrama de arquitetura e receba um '
        'relatório de modelagem de ameaças STRIDE — componentes detectados, '
        'ameaças por componente e recomendações priorizadas.</div>'
        f'</div></div>{chip}</div>',
        unsafe_allow_html=True,
    )


def _legenda_stride() -> None:
    """Renderiza a legenda das 6 categorias STRIDE (assinatura visual)."""
    itens = []
    for letra, cor in STRIDE_CORES.items():
        rotulo = CATEGORIAS_STRIDE[letra].split(" (")[0]
        itens.append(
            f'<div class="stride-item"><span class="badge" style="background:{cor}">'
            f'{letra}</span>{rotulo}</div>'
        )
    st.markdown(f'<div class="stride">{"".join(itens)}</div>', unsafe_allow_html=True)


def _extrair_metricas(conteudo: str) -> dict:
    """Extrai métricas do relatório para o painel (parsing tolerante a falhas).

    Args:
        conteudo: Markdown do relatório gerado.

    Returns:
        Dicionário com `componentes` (lista de nomes), `n_ameacas` e
        `n_categorias`. Campos ficam vazios/zero se o parsing falhar.
    """
    componentes: list[str] = []
    try:
        bloco = conteudo.split("## Componentes Identificados", 1)[1].split("\n## ", 1)[0]
        componentes = [
            linha.strip()[2:].strip()
            for linha in bloco.splitlines()
            if linha.strip().startswith("- ")
        ]
    except (IndexError, ValueError):
        pass
    n_ameacas = conteudo.count("Contramedidas recomendadas:")
    n_categorias = sum(1 for full in CATEGORIAS_STRIDE.values() if f"**{full}**" in conteudo)
    return {"componentes": componentes, "n_ameacas": n_ameacas, "n_categorias": n_categorias}


def _stat_tiles(metricas: dict) -> None:
    """Renderiza as métricas do relatório como três stat tiles."""
    dados = [
        (len(metricas["componentes"]), "Componentes detectados", "#6366F1"),
        (metricas["n_ameacas"], "Ameaças mapeadas", "#FB923C"),
        (f'{metricas["n_categorias"]}/6', "Categorias STRIDE", "#22D3EE"),
    ]
    for coluna, (num, lbl, cor) in zip(st.columns(3), dados):
        coluna.markdown(
            f'<div class="stat" style="--accent:{cor}"><div class="num">{num}</div>'
            f'<div class="lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )


def _chips_componentes(nomes: list[str]) -> None:
    """Renderiza os componentes detectados como chips."""
    if not nomes:
        return
    pills = "".join(f'<span class="pill"><span class="d"></span>{n}</span>' for n in nomes)
    st.markdown(f'<div class="chips">{pills}</div>', unsafe_allow_html=True)


def main() -> None:
    """Renderiza a interface principal do Streamlit."""
    st.markdown(_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sec">Configuração</div>', unsafe_allow_html=True)
        nome_projeto = st.text_input("Nome do projeto", value="Análise de Arquitetura")

        _, nome, variavel = _resolver_provedor()
        if variavel:
            st.caption(f"Provedor: **{nome}** — configure `{variavel}` no `.env`.")
        else:
            st.warning("`LLM_PROVIDER` inválido no `.env`. Use `anthropic` ou `openai`.")

        st.markdown('<div class="sec">Metodologia STRIDE</div>', unsafe_allow_html=True)
        _legenda_stride()

    _hero()

    st.markdown('<div class="sec">1 · Diagrama de arquitetura</div>', unsafe_allow_html=True)
    arquivo_enviado = st.file_uploader(
        "Envie um PNG, JPG ou WEBP", type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )

    if arquivo_enviado is None:
        st.markdown(
            '<div class="drop"><div class="ic">🗺️</div>'
            '<p><b>Comece enviando um diagrama.</b><br>'
            'O modelo identifica os componentes e monta o relatório de ameaças.</p></div>',
            unsafe_allow_html=True,
        )
        return

    col_prev, col_acao = st.columns([1.5, 1])
    with col_prev:
        st.image(arquivo_enviado, caption="Diagrama enviado", use_container_width=True)
    with col_acao:
        st.markdown('<div class="sec">2 · Análise</div>', unsafe_allow_html=True)
        st.caption("Detecta os componentes e gera o relatório STRIDE completo.")
        gerar = st.button(
            "Gerar relatório STRIDE", type="primary", use_container_width=True
        )

    if not gerar:
        return

    with st.spinner("Detectando componentes e gerando o relatório…"):
        try:
            caminho_relatorio = _processar_imagem(arquivo_enviado, nome_projeto)
        except Exception as erro:  # noqa: BLE001 - exibido ao usuário final
            logger.exception("Falha ao gerar relatório")
            st.error(f"Não foi possível gerar o relatório: {erro}")
            return

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
    """Exibe o painel de resultado: métricas, componentes, relatório e downloads.

    Args:
        caminho_relatorio: Caminho do arquivo Markdown gerado.
    """
    from stride.pdf_export import exportar_para_pdf

    conteudo = caminho_relatorio.read_text(encoding="utf-8")
    metricas = _extrair_metricas(conteudo)

    st.markdown('<div class="sec">3 · Resultado</div>', unsafe_allow_html=True)
    _stat_tiles(metricas)

    if metricas["componentes"]:
        st.markdown('<div class="sec">Componentes identificados</div>', unsafe_allow_html=True)
        _chips_componentes(metricas["componentes"])

    st.markdown('<div class="sec">Downloads</div>', unsafe_allow_html=True)
    col_md, col_pdf = st.columns(2)
    with col_md:
        st.download_button(
            "⬇️  Relatório (.md)", data=conteudo,
            file_name=caminho_relatorio.name, mime="text/markdown",
        )
    with col_pdf:
        try:
            caminho_pdf = exportar_para_pdf(caminho_relatorio)
            st.download_button(
                "⬇️  Relatório (.pdf)", data=caminho_pdf.read_bytes(),
                file_name=caminho_pdf.name, mime="application/pdf",
            )
        except Exception as erro:  # noqa: BLE001 - exibido ao usuário final
            logger.exception("Falha ao exportar PDF")
            st.warning(f"Não foi possível gerar o PDF: {erro}")

    st.markdown('<div class="sec">Relatório completo</div>', unsafe_allow_html=True)
    html = _markdown.markdown(conteudo, extensions=["nl2br"])
    st.markdown(f'<div class="report">{html}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
