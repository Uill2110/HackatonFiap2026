"""
Avaliação do detector YOLOv8 treinado.

Roda `model.val()` sobre o split de validação do dataset e reporta as métricas
de detecção — mAP@50, mAP@50-95, precisão e recall (geral e por classe) —,
além de salvar a matriz de confusão e as curvas PR geradas pela Ultralytics.

As métricas são impressas, gravadas em `docs/avaliacao/metricas.json` e os
gráficos (PNG) são copiados para `docs/avaliacao/`, servindo como evidência
quantitativa do desempenho do modelo.

Uso:
    python -m model.evaluate
    python -m model.evaluate --data data/annotated/synthetic/dataset_stride.yaml
"""

import argparse
import json
import logging
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PESOS_PADRAO = "model/weights/best.pt"
DATASET_PADRAO = "data/annotated/synthetic/dataset_stride.yaml"
IMGSZ_PADRAO = 1024
DIRETORIO_SAIDA = Path("docs/avaliacao")
GRAFICOS = ("confusion_matrix.png", "confusion_matrix_normalized.png", "PR_curve.png")


def _resolver_pesos(pesos: str | None) -> Path:
    """Determina o caminho dos pesos treinados.

    Args:
        pesos: Caminho informado via CLI, ou None para usar MODEL_WEIGHTS_PATH
            (.env) / o padrão do projeto.

    Returns:
        Caminho do arquivo `.pt`.

    Raises:
        FileNotFoundError: Se os pesos não existirem.
    """
    load_dotenv()
    caminho = Path(pesos or os.environ.get("MODEL_WEIGHTS_PATH", PESOS_PADRAO))
    if not caminho.exists():
        raise FileNotFoundError(
            f"Pesos não encontrados em {caminho}. Treine o modelo primeiro "
            "(python -m model.train)."
        )
    return caminho


def _metricas_por_classe(resultados) -> list[dict]:
    """Extrai precisão/recall/mAP por classe dos resultados da validação.

    Args:
        resultados: Objeto retornado por `YOLO.val()`.

    Returns:
        Lista de dicionários (uma entrada por classe avaliada).
    """
    caixa = resultados.box
    nomes = resultados.names
    por_classe = []
    for posicao, classe_id in enumerate(caixa.ap_class_index):
        por_classe.append(
            {
                "classe": nomes[int(classe_id)],
                "precisao": round(float(caixa.p[posicao]), 4),
                "recall": round(float(caixa.r[posicao]), 4),
                "mAP50": round(float(caixa.ap50[posicao]), 4),
                "mAP50_95": round(float(caixa.ap[posicao]), 4),
            }
        )
    return por_classe


def _copiar_graficos(save_dir: Path) -> list[str]:
    """Copia os gráficos gerados pela Ultralytics para o diretório de saída.

    Args:
        save_dir: Diretório onde a validação salvou os PNGs.

    Returns:
        Nomes dos arquivos efetivamente copiados.
    """
    DIRETORIO_SAIDA.mkdir(parents=True, exist_ok=True)
    copiados = []
    for nome in GRAFICOS:
        origem = save_dir / nome
        if origem.exists():
            shutil.copy2(origem, DIRETORIO_SAIDA / nome)
            copiados.append(nome)
    return copiados


def avaliar(
    data: str | Path = DATASET_PADRAO,
    pesos: str | None = None,
    imgsz: int = IMGSZ_PADRAO,
    device: str = "cpu",
) -> dict:
    """Avalia o modelo treinado e persiste métricas + gráficos.

    Args:
        data: Caminho do `dataset.yaml` (usa o split de validação definido nele).
        pesos: Caminho dos pesos `.pt` (None usa MODEL_WEIGHTS_PATH / padrão).
        imgsz: Resolução de avaliação (deve casar com a do treino/inferência).
        device: Dispositivo ("cpu" ou "0" para a primeira GPU).

    Returns:
        Dicionário com métricas gerais e por classe.

    Raises:
        FileNotFoundError: Se os pesos ou o dataset não existirem.
    """
    # Import tardio: ultralytics é dependência pesada.
    from ultralytics import YOLO

    caminho_data = Path(data)
    if not caminho_data.exists():
        raise FileNotFoundError(f"Config do dataset não encontrada: {caminho_data}")

    caminho_pesos = _resolver_pesos(pesos)
    logger.info("Avaliando %s em %s (imgsz=%d)", caminho_pesos, caminho_data, imgsz)

    modelo = YOLO(str(caminho_pesos))
    resultados = modelo.val(
        data=str(caminho_data),
        imgsz=imgsz,
        device=device,
        plots=True,
        project="model/runs",
        name="val",
        exist_ok=True,
    )

    caixa = resultados.box
    metricas = {
        "geral": {
            "mAP50": round(float(caixa.map50), 4),
            "mAP50_95": round(float(caixa.map), 4),
            "precisao": round(float(caixa.mp), 4),
            "recall": round(float(caixa.mr), 4),
        },
        "por_classe": _metricas_por_classe(resultados),
    }

    graficos = _copiar_graficos(Path(resultados.save_dir))
    metricas["graficos"] = graficos

    DIRETORIO_SAIDA.mkdir(parents=True, exist_ok=True)
    (DIRETORIO_SAIDA / "metricas.json").write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    logger.info(
        "mAP50=%.4f | mAP50-95=%.4f | precisão=%.4f | recall=%.4f",
        metricas["geral"]["mAP50"],
        metricas["geral"]["mAP50_95"],
        metricas["geral"]["precisao"],
        metricas["geral"]["recall"],
    )
    logger.info("Métricas salvas em %s", DIRETORIO_SAIDA / "metricas.json")
    if graficos:
        logger.info("Gráficos copiados para %s: %s", DIRETORIO_SAIDA, ", ".join(graficos))

    return metricas


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(description="Avalia o detector YOLOv8 treinado.")
    parser.add_argument("--data", default=DATASET_PADRAO, help="Caminho do dataset.yaml")
    parser.add_argument("--pesos", default=None, help="Caminho dos pesos (.pt)")
    parser.add_argument("--imgsz", type=int, default=IMGSZ_PADRAO, help="Resolução de avaliação")
    parser.add_argument("--device", default="cpu", help="Device ('cpu' ou '0')")
    args = parser.parse_args()

    metricas = avaliar(args.data, args.pesos, args.imgsz, args.device)
    print(json.dumps(metricas, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
