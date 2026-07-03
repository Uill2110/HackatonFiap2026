"""
Consolidação do dataset de ícones AWS nas categorias da knowledge_base STRIDE.

O dataset baixado do Roboflow (`model/download_dataset.py`) possui centenas de
classes de ícones AWS. Este script remapeia os rótulos YOLO para as ~11 chaves
da base de conhecimento (`stride/knowledge_base.py`), usando as regras de
`model/class_mapping.py`, e gera um `data.yaml` consolidado para o treino
(`model/train.py`).

Rótulos cujas classes não têm correspondência na knowledge_base são descartados.

Uso:
    python -m model.prepare_dataset --dataset data/annotated/aws-icon-detection
"""

import argparse
import logging
from collections import Counter
from pathlib import Path

import yaml

from model.class_mapping import mapear_classe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SPLITS = ("train", "valid", "test")
NOME_CONFIG_SAIDA = "dataset_stride.yaml"


def _carregar_nomes(data_yaml: Path) -> list[str]:
    """Lê a lista de nomes de classe do data.yaml original.

    Args:
        data_yaml: Caminho do data.yaml do dataset baixado.

    Returns:
        Lista de nomes de classe, indexada pelo id da classe.
    """
    config = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    nomes = config.get("names", [])
    if isinstance(nomes, dict):
        nomes = [nomes[k] for k in sorted(nomes)]
    return nomes


def _construir_remapeamento(
    nomes: list[str],
) -> tuple[dict[int, int], list[str]]:
    """Constrói o mapa índice-antigo -> índice-novo e a lista de buckets.

    Args:
        nomes: Nomes de classe originais do dataset.

    Returns:
        Tupla (mapa_indices, buckets), onde mapa_indices leva o id de classe
        original ao id consolidado, e buckets é a lista ordenada de chaves da
        knowledge_base efetivamente usadas.
    """
    buckets_usados: set[str] = set()
    classe_para_bucket: dict[int, str] = {}
    for idx, nome in enumerate(nomes):
        bucket = mapear_classe(nome)
        if bucket is not None:
            classe_para_bucket[idx] = bucket
            buckets_usados.add(bucket)

    buckets = sorted(buckets_usados)
    bucket_para_novo_idx = {b: i for i, b in enumerate(buckets)}
    mapa_indices = {
        idx: bucket_para_novo_idx[bucket] for idx, bucket in classe_para_bucket.items()
    }
    return mapa_indices, buckets


def _remapear_labels(dir_labels: Path, mapa_indices: dict[int, int]) -> Counter:
    """Reescreve os arquivos de rótulo YOLO aplicando o remapeamento de classes.

    Rótulos de classes não mapeadas são removidos.

    Args:
        dir_labels: Diretório com os arquivos `.txt` de rótulos.
        mapa_indices: Mapa índice-antigo -> índice-novo.

    Returns:
        Contador novo_indice -> número de rótulos mantidos.
    """
    contagem: Counter = Counter()
    if not dir_labels.is_dir():
        return contagem

    for arquivo in dir_labels.glob("*.txt"):
        linhas_novas = []
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            partes = linha.split()
            if not partes:
                continue
            idx_antigo = int(partes[0])
            if idx_antigo in mapa_indices:
                idx_novo = mapa_indices[idx_antigo]
                partes[0] = str(idx_novo)
                linhas_novas.append(" ".join(partes))
                contagem[idx_novo] += 1
        arquivo.write_text("\n".join(linhas_novas) + ("\n" if linhas_novas else ""), encoding="utf-8")

    return contagem


def preparar(dataset_dir: str | Path) -> Path:
    """Consolida os rótulos do dataset e gera o data.yaml para treino.

    Args:
        dataset_dir: Diretório do dataset baixado (contém data.yaml e splits).

    Returns:
        Caminho do arquivo de configuração consolidado gerado.

    Raises:
        FileNotFoundError: Se o data.yaml original não existir.
    """
    dataset_dir = Path(dataset_dir)
    data_yaml = dataset_dir / "data.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml não encontrado em {dataset_dir}")

    nomes = _carregar_nomes(data_yaml)
    mapa_indices, buckets = _construir_remapeamento(nomes)
    logger.info(
        "Consolidando %d classes originais em %d categorias STRIDE: %s",
        len(nomes),
        len(buckets),
        buckets,
    )

    total = Counter()
    splits_presentes: list[str] = []
    for split in SPLITS:
        dir_images = dataset_dir / split / "images"
        if not dir_images.is_dir():
            continue
        splits_presentes.append(split)
        contagem = _remapear_labels(dataset_dir / split / "labels", mapa_indices)
        total.update(contagem)
        logger.info("Split '%s': %d rótulos mantidos", split, sum(contagem.values()))

    for idx, bucket in enumerate(buckets):
        logger.info("  %s: %d rótulos", bucket, total.get(idx, 0))

    config_saida = {
        "path": str(dataset_dir.resolve()),
        "names": buckets,
        "nc": len(buckets),
    }
    config_saida["train"] = "train/images"
    config_saida["val"] = "valid/images" if "valid" in splits_presentes else "train/images"
    if "test" in splits_presentes:
        config_saida["test"] = "test/images"

    caminho_saida = dataset_dir / NOME_CONFIG_SAIDA
    caminho_saida.write_text(yaml.safe_dump(config_saida, sort_keys=False), encoding="utf-8")
    logger.info("Config consolidado salvo em %s", caminho_saida)
    return caminho_saida


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(
        description="Consolida os rótulos do dataset AWS nas categorias STRIDE."
    )
    parser.add_argument(
        "--dataset",
        default="data/annotated/aws-icon-detection",
        help="Diretório do dataset baixado (contém data.yaml e splits)",
    )
    args = parser.parse_args()

    caminho = preparar(args.dataset)
    print(f"Dataset consolidado. Treine com: python -m model.train --data {caminho}")


if __name__ == "__main__":
    main()
