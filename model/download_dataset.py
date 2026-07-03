"""
Download do dataset de diagramas de arquitetura do Roboflow Universe.

Baixa um dataset já anotado no formato YOLOv8 para `data/annotated/`, para
posterior treino do modelo supervisionado (ver `model/train.py`).

Os identificadores do dataset (workspace, projeto e versão) são configuráveis
via variáveis de ambiente ou argumentos de linha de comando, permitindo trocar
de dataset sem alterar o código. Os valores padrão apontam para um dataset
público de diagramas de sistema; confirme/ajuste os identificadores a partir do
snippet "Download this Dataset" da página do dataset no Roboflow Universe.

Uso:
    python -m model.download_dataset
    python -m model.download_dataset --workspace <ws> --project <slug> --version 1
"""

import argparse
import logging
import os
import shutil
from pathlib import Path

import yaml
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DIRETORIO_DATASET = Path("data/annotated")

# Identificadores padrão do dataset no Roboflow Universe. Ajuste conforme o
# dataset escolhido (workspace/projeto/versão do snippet de download).
WORKSPACE_PADRAO = "steven-kuo-5s6aq"
PROJECT_PADRAO = "aws-icon-detection"
VERSION_PADRAO = 5


def _obter_api_key() -> str:
    """Lê a ROBOFLOW_API_KEY do ambiente (.env).

    Returns:
        A chave de API do Roboflow.

    Raises:
        RuntimeError: Se a chave não estiver configurada.
    """
    load_dotenv()
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("ROBOFLOW_API_KEY não definida no ambiente (.env)")
    return api_key


def _reportar_classes(diretorio: Path) -> list[str]:
    """Lê e loga as classes do `data.yaml` gerado pelo download.

    Args:
        diretorio: Diretório onde o dataset foi baixado.

    Returns:
        Lista de nomes das classes do dataset (vazia se o arquivo não existir).
    """
    data_yaml = diretorio / "data.yaml"
    if not data_yaml.exists():
        logger.warning("data.yaml não encontrado em %s", diretorio)
        return []

    config = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    nomes = config.get("names", [])
    if isinstance(nomes, dict):  # formato {0: "classe", ...}
        nomes = [nomes[k] for k in sorted(nomes)]

    logger.info("Classes do dataset (%d): %s", len(nomes), nomes)
    logger.info("Use estes nomes para preencher model/class_mapping.py")
    return nomes


def baixar_dataset(
    workspace: str = WORKSPACE_PADRAO,
    project: str = PROJECT_PADRAO,
    version: int = VERSION_PADRAO,
    destino: str | Path = DIRETORIO_DATASET,
) -> Path:
    """Baixa o dataset do Roboflow Universe no formato YOLOv8.

    Args:
        workspace: Nome do workspace no Roboflow.
        project: Slug do projeto/dataset.
        version: Número da versão do dataset.
        destino: Diretório onde o dataset será salvo.

    Returns:
        Caminho do diretório do dataset baixado.

    Raises:
        RuntimeError: Se a ROBOFLOW_API_KEY não estiver configurada.
    """
    # Import tardio: roboflow é dependência pesada e só necessária aqui.
    from roboflow import Roboflow

    api_key = _obter_api_key()
    # O SDK do Roboflow PULA o download se o diretório de destino já existir.
    # Por isso baixamos numa subpasta nomeada pelo projeto e a recriamos.
    local = Path(destino) / project

    if (local / "data.yaml").exists():
        logger.info("Dataset já presente em %s (pulando download)", local)
        _reportar_classes(local)
        return local

    if local.exists():
        shutil.rmtree(local)
    local.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Baixando dataset %s/%s v%d do Roboflow", workspace, project, version)
    rf = Roboflow(api_key=api_key)
    projeto = rf.workspace(workspace).project(project)
    dataset = projeto.version(version).download("yolov8", location=str(local))

    diretorio = Path(dataset.location)
    logger.info("Dataset salvo em %s", diretorio)
    _reportar_classes(diretorio)
    return diretorio


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(
        description="Baixa dataset de diagramas de arquitetura do Roboflow Universe."
    )
    parser.add_argument("--workspace", default=WORKSPACE_PADRAO, help="Workspace no Roboflow")
    parser.add_argument("--project", default=PROJECT_PADRAO, help="Slug do projeto/dataset")
    parser.add_argument("--version", type=int, default=VERSION_PADRAO, help="Versão do dataset")
    parser.add_argument(
        "--destino", default=str(DIRETORIO_DATASET), help="Diretório de saída do dataset"
    )
    args = parser.parse_args()

    baixar_dataset(args.workspace, args.project, args.version, args.destino)


if __name__ == "__main__":
    main()
