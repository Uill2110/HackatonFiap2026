"""
Treinamento do modelo supervisionado YOLOv8 para detecção de componentes de
arquitetura.

Treina um modelo YOLOv8 a partir do dataset anotado (formato YOLO) baixado com
`model/download_dataset.py`, e copia os melhores pesos (`best.pt`) para o caminho
apontado por `MODEL_WEIGHTS_PATH`, usado na inferência (`model/predict.py`).

Uso:
    python -m model.train --data data/annotated/dataset.yaml --epochs 50
    python -m model.train --data data/annotated/data.yaml --model yolov8s.pt --device 0
"""

import argparse
import logging
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PESOS_PADRAO_SAIDA = "model/weights/best.pt"


def _resolver_destino_pesos(destino: str | None) -> Path:
    """Determina o caminho final dos pesos treinados.

    Args:
        destino: Caminho informado via CLI, ou None para usar
            MODEL_WEIGHTS_PATH (.env) / o padrão do projeto.

    Returns:
        Caminho de destino dos pesos.
    """
    load_dotenv()
    caminho = destino or os.environ.get("MODEL_WEIGHTS_PATH", PESOS_PADRAO_SAIDA)
    return Path(caminho)


def treinar(
    data: str | Path,
    epochs: int = 50,
    model: str = "yolov8n.pt",
    imgsz: int = 640,
    batch: int = 8,
    device: str = "0",
    workers: int = 0,
    destino_pesos: str | None = None,
) -> Path:
    """Treina o modelo YOLOv8 e salva os melhores pesos no destino configurado.

    Args:
        data: Caminho do arquivo `dataset.yaml`/`data.yaml` do dataset YOLO.
        epochs: Número de épocas de treino.
        model: Modelo base pré-treinado (ex.: "yolov8n.pt", "yolov8s.pt").
        imgsz: Tamanho da imagem de entrada.
        batch: Tamanho do batch (mantenha baixo em GPUs com pouca VRAM).
        device: Dispositivo de treino ("0" para a primeira GPU, "cpu" para CPU).
        workers: Nº de processos do DataLoader. Use 0 no Windows para evitar
            o erro de paging file (WinError 1455) ao recarregar as DLLs do CUDA.
        destino_pesos: Caminho final para copiar o `best.pt`. Se None, usa
            MODEL_WEIGHTS_PATH (.env) ou o padrão do projeto.

    Returns:
        Caminho do arquivo de pesos treinados copiado para o destino.

    Raises:
        FileNotFoundError: Se o arquivo de configuração do dataset não existir.
    """
    # Import tardio: ultralytics é dependência pesada.
    from ultralytics import YOLO

    caminho_data = Path(data)
    if not caminho_data.exists():
        raise FileNotFoundError(f"Config do dataset não encontrada: {caminho_data}")

    logger.info("Iniciando treino YOLOv8 (%s) por %d épocas no device %s", model, epochs, device)
    modelo = YOLO(model)
    resultados = modelo.train(
        data=str(caminho_data),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        workers=workers,
        plots=False,  # evita crash em matplotlib/seaborn no Windows (pagefile/DLLs)
        project="model/runs",
        name="stride_detector",
        exist_ok=True,
    )

    melhores = Path(resultados.save_dir) / "weights" / "best.pt"
    destino = _resolver_destino_pesos(destino_pesos)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(melhores, destino)
    logger.info("Pesos treinados copiados para %s", destino)

    return destino


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(description="Treina o detector YOLOv8 de componentes.")
    parser.add_argument(
        "--data",
        default="data/annotated/synthetic/dataset_stride.yaml",
        help="Caminho do dataset.yaml (ver model/generate_synthetic.py)",
    )
    parser.add_argument("--epochs", type=int, default=60, help="Número de épocas")
    parser.add_argument("--model", default="yolov8n.pt", help="Modelo base pré-treinado")
    parser.add_argument("--imgsz", type=int, default=1024, help="Tamanho da imagem de entrada")
    parser.add_argument("--batch", type=int, default=6, help="Tamanho do batch")
    parser.add_argument("--device", default="0", help="Device de treino ('0' GPU, 'cpu')")
    parser.add_argument(
        "--workers", type=int, default=0, help="Workers do DataLoader (0 no Windows)"
    )
    parser.add_argument("--output", default=None, help="Caminho de saída dos pesos (best.pt)")
    args = parser.parse_args()

    destino = treinar(
        data=args.data,
        epochs=args.epochs,
        model=args.model,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        destino_pesos=args.output,
    )
    print(f"Modelo treinado salvo em: {destino}")


if __name__ == "__main__":
    main()
