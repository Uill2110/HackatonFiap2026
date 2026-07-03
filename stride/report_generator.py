"""
Gerador de relatório de Modelagem de Ameaças (STRIDE).

Orquestra o pipeline completo:
1. Detecta componentes na imagem do diagrama (model.predict).
2. Mapeia componentes para ameaças STRIDE (stride.knowledge_base).
3. Usa a Claude API para enriquecer a análise com linguagem natural,
   resumo executivo e recomendações priorizadas.
4. Preenche o template e salva o relatório em Markdown.
"""

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from model.predict import detectar_componentes
from stride.knowledge_base import CATEGORIAS_STRIDE, mapear_componentes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELO_TEXTO = "claude-sonnet-4-6"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "report_template.md"


def _formatar_lista_componentes(componentes: dict) -> str:
    """Formata a lista de componentes identificados em Markdown.

    Args:
        componentes: Dicionário componente -> dados STRIDE (ver
            `stride.knowledge_base.mapear_componentes`).

    Returns:
        Texto Markdown com a lista de componentes.
    """
    if not componentes:
        return "_Nenhum componente reconhecido foi identificado na imagem._"

    linhas = [f"- {dados['nome_exibicao']}" for dados in componentes.values()]
    return "\n".join(linhas)


def _formatar_analise_ameacas(componentes: dict) -> str:
    """Formata a análise de ameaças por componente em Markdown.

    Args:
        componentes: Dicionário componente -> dados STRIDE.

    Returns:
        Texto Markdown com seções por componente e suas ameaças.
    """
    if not componentes:
        return "_Sem componentes para análise._"

    blocos = []
    for dados in componentes.values():
        blocos.append(f"### {dados['nome_exibicao']}\n")
        for ameaca in dados["ameacas"]:
            categoria = CATEGORIAS_STRIDE.get(ameaca["categoria"], ameaca["categoria"])
            contramedidas = "\n".join(f"  - {c}" for c in ameaca["contramedidas"])
            blocos.append(
                f"**{categoria}**\n\n"
                f"{ameaca['descricao']}\n\n"
                f"Contramedidas recomendadas:\n{contramedidas}\n"
            )
    return "\n".join(blocos)


def _gerar_resumo_e_recomendacoes(
    client: Anthropic, componentes: dict, observacoes: str
) -> tuple[str, str]:
    """Usa a Claude API para gerar resumo executivo e recomendações.

    Args:
        client: Cliente da Anthropic API já configurado.
        componentes: Dicionário componente -> dados STRIDE identificados.
        observacoes: Observações textuais geradas pela etapa de detecção.

    Returns:
        Tupla (resumo_executivo, recomendacoes_priorizadas), ambos em texto
        Markdown.

    Raises:
        RuntimeError: Se a resposta do modelo não seguir o formato esperado.
    """
    nomes_componentes = [dados["nome_exibicao"] for dados in componentes.values()]
    todas_ameacas = [
        f"{dados['nome_exibicao']}: {ameaca['categoria']} - {ameaca['descricao']}"
        for dados in componentes.values()
        for ameaca in dados["ameacas"]
    ]

    prompt = (
        "Você é um especialista em segurança de aplicações e modelagem de "
        "ameaças STRIDE. Com base nas informações abaixo sobre uma "
        "arquitetura de software, escreva:\n"
        "1. Um RESUMO EXECUTIVO (3 a 5 frases, linguagem acessível para "
        "stakeholders não técnicos) sobre o nível geral de risco.\n"
        "2. RECOMENDAÇÕES PRIORITÁRIAS (lista de 3 a 6 itens, em ordem de "
        "prioridade, com ações concretas e objetivas).\n\n"
        f"Observações da arquitetura: {observacoes}\n\n"
        f"Componentes identificados: {', '.join(nomes_componentes)}\n\n"
        "Ameaças mapeadas:\n" + "\n".join(f"- {a}" for a in todas_ameacas) + "\n\n"
        "Responda em Markdown, usando exatamente os títulos '## Resumo "
        "Executivo' e '## Recomendações Prioritárias' como separadores."
    )

    resposta = client.messages.create(
        model=MODELO_TEXTO,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = resposta.content[0].text.strip()

    if "## Recomendações Prioritárias" not in texto:
        raise RuntimeError(f"Resposta do modelo fora do formato esperado: {texto}")

    resumo, recomendacoes = texto.split("## Recomendações Prioritárias", maxsplit=1)
    resumo = resumo.replace("## Resumo Executivo", "").strip()
    recomendacoes = recomendacoes.strip()

    return resumo, recomendacoes


def gerar_relatorio(
    caminho_imagem: str | Path,
    nome_projeto: str = "Análise de Arquitetura",
    diretorio_saida: str | Path | None = None,
) -> Path:
    """Gera o relatório STRIDE completo para uma imagem de arquitetura.

    Args:
        caminho_imagem: Caminho para a imagem do diagrama de arquitetura.
        nome_projeto: Nome do projeto/arquitetura, usado no cabeçalho do
            relatório.
        diretorio_saida: Diretório onde o relatório será salvo. Se None,
            usa a variável de ambiente REPORT_OUTPUT_DIR (ou
            "docs/exemplos_relatorio/" como padrão).

    Returns:
        Caminho do arquivo Markdown gerado.

    Raises:
        FileNotFoundError: Se a imagem ou o template não existirem.
        RuntimeError: Se a ANTHROPIC_API_KEY não estiver configurada.
    """
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY não definida no ambiente (.env)")

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")

    caminho_imagem = Path(caminho_imagem)
    diretorio_saida = Path(
        diretorio_saida or os.environ.get("REPORT_OUTPUT_DIR", "docs/exemplos_relatorio/")
    )
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    logger.info("Detectando componentes em %s", caminho_imagem)
    deteccao = detectar_componentes(caminho_imagem)
    componentes = mapear_componentes(deteccao.get("componentes_detectados", []))
    observacoes = deteccao.get("observacoes", "")

    client = Anthropic(api_key=api_key)

    logger.info("Gerando resumo executivo e recomendações via %s", MODELO_TEXTO)
    resumo, recomendacoes = _gerar_resumo_e_recomendacoes(client, componentes, observacoes)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    relatorio = (
        template.replace("{{projeto}}", nome_projeto)
        .replace("{{data}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("{{arquitetura}}", caminho_imagem.name)
        .replace("{{lista_componentes}}", _formatar_lista_componentes(componentes))
        .replace("{{analise_ameacas}}", _formatar_analise_ameacas(componentes))
        .replace("{{resumo}}", resumo)
        .replace("{{recomendacoes}}", recomendacoes)
    )

    nome_arquivo = f"relatorio_stride_{caminho_imagem.stem}.md"
    caminho_saida = diretorio_saida / nome_arquivo
    caminho_saida.write_text(relatorio, encoding="utf-8")
    logger.info("Relatório salvo em %s", caminho_saida)

    return caminho_saida


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gera relatório de Modelagem de Ameaças STRIDE a partir de uma imagem."
    )
    parser.add_argument("--input", required=True, help="Caminho para a imagem do diagrama")
    parser.add_argument(
        "--nome-projeto", default="Análise de Arquitetura", help="Nome do projeto/arquitetura"
    )
    parser.add_argument("--output-dir", default=None, help="Diretório de saída do relatório")
    parser.add_argument(
        "--pdf", action="store_true", help="Também exporta o relatório em PDF"
    )
    args = parser.parse_args()

    caminho_saida = gerar_relatorio(args.input, args.nome_projeto, args.output_dir)
    print(f"Relatório gerado: {caminho_saida}")

    if args.pdf:
        from stride.pdf_export import exportar_para_pdf

        caminho_pdf = exportar_para_pdf(caminho_saida)
        print(f"PDF gerado: {caminho_pdf}")


if __name__ == "__main__":
    main()
