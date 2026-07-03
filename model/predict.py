"""
Detecção supervisionada de componentes de arquitetura em uma imagem de diagrama.

A detecção é feita por um modelo YOLOv8 treinado (ver `model/train.py`). As
classes detectadas são traduzidas para as chaves da base de conhecimento STRIDE
(`stride/knowledge_base.py`) por meio de `model/class_mapping.py`.

O contrato de saída (`detectar_componentes`) é mantido compatível com o restante
do pipeline (`stride/report_generator.py`, API e Streamlit): retorna um dicionário
com "componentes_detectados" e "observacoes".
"""

import argparse
import json
import logging
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from model.class_mapping import mapear_classe
from stride.knowledge_base import listar_componentes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PESOS_PADRAO = "model/weights/best.pt"
CONFIANCA_MINIMA = 0.25

EXTENSOES_SUPORTADAS: set[str] = {".png", ".jpg", ".jpeg", ".webp"}


def _resolver_caminho_pesos() -> Path:
    """Determina o caminho dos pesos do modelo treinado.

    Returns:
        Caminho do arquivo `.pt` de pesos.

    Raises:
        FileNotFoundError: Se os pesos não existirem (modelo não treinado).
    """
    load_dotenv()
    caminho = Path(os.environ.get("MODEL_WEIGHTS_PATH", PESOS_PADRAO))
    if not caminho.exists():
        raise FileNotFoundError(
            f"Pesos do modelo não encontrados em {caminho}. "
            "Treine o modelo primeiro: python -m model.train --data <dataset.yaml>"
        )
    return caminho


def _montar_observacoes(contagem: Counter) -> str:
    """Monta um texto descritivo a partir das contagens de componentes.

    Args:
        contagem: Contador chave_componente -> quantidade detectada.

    Returns:
        Texto descritivo das detecções.
    """
    if not contagem:
        return "Nenhum componente reconhecido foi detectado pelo modelo YOLOv8."

    itens = ", ".join(f"{qtd}x {chave}" for chave, qtd in sorted(contagem.items()))
    return f"Detectados via YOLOv8: {itens}."


def detectar_componentes(
    caminho_imagem: str | Path, confianca_minima: float = CONFIANCA_MINIMA
) -> dict:
    """Detecta componentes de arquitetura em uma imagem usando YOLOv8.

    Args:
        caminho_imagem: Caminho para a imagem do diagrama de arquitetura.
        confianca_minima: Confiança mínima para considerar uma detecção.

    Returns:
        Dicionário com "componentes_detectados" (lista de chaves válidas da
        `stride/knowledge_base.py`, sem repetição) e "observacoes" (texto
        descritivo das detecções).

    Raises:
        FileNotFoundError: Se a imagem ou os pesos do modelo não existirem.
        ValueError: Se a extensão da imagem não for suportada.
    """
    # Import tardio: ultralytics é dependência pesada.
    from ultralytics import YOLO

    caminho = Path(caminho_imagem)
    if not caminho.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho}")
    if caminho.suffix.lower() not in EXTENSOES_SUPORTADAS:
        raise ValueError(f"Extensão de imagem não suportada: {caminho.suffix}")

    pesos = _resolver_caminho_pesos()
    logger.info("Carregando modelo de %s", pesos)
    modelo = YOLO(str(pesos))

    logger.info("Executando inferência em %s", caminho)
    resultados = modelo.predict(source=str(caminho), conf=confianca_minima, verbose=False)

    contagem: Counter = Counter()
    for resultado in resultados:
        nomes = resultado.names  # índice -> nome da classe
        for box in resultado.boxes:
            classe_id = int(box.cls[0])
            nome_classe = nomes[classe_id]
            chave = mapear_classe(nome_classe)
            if chave is not None:
                contagem[chave] += 1

    componentes_detectados = sorted(contagem.keys())
    validos = set(listar_componentes())
    componentes_detectados = [c for c in componentes_detectados if c in validos]

    logger.info("Componentes detectados: %s", componentes_detectados)

    return {
        "componentes_detectados": componentes_detectados,
        "observacoes": _montar_observacoes(contagem),
    }


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(
        description="Detecta componentes de arquitetura em uma imagem usando YOLOv8."
    )
    parser.add_argument("--image", required=True, help="Caminho para a imagem do diagrama")
    parser.add_argument(
        "--conf", type=float, default=CONFIANCA_MINIMA, help="Confiança mínima da detecção"
    )
    args = parser.parse_args()

    resultado = detectar_componentes(args.image, confianca_minima=args.conf)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
