"""
Geração de diagramas de arquitetura sintéticos para treino do detector.

O dataset público de ícones AWS contém uma imagem por ícone (caixa "full-frame"),
o que ensina o modelo apenas a classificar um ícone que preenche a tela inteira —
ele não aprende a LOCALIZAR múltiplos ícones num diagrama real.

Este script usa esses ícones como "carimbos": cola vários deles, em posições e
escalas aleatórias, sobre um canvas branco (com linhas leves simulando conexões),
gerando bounding boxes corretas. O resultado é um dataset de detecção de verdade,
consolidado nas categorias da knowledge_base STRIDE.

Uso:
    python -m model.generate_synthetic --source data/annotated/aws-icon-detection \\
        --out data/annotated/synthetic --n-train 400 --n-val 80
"""

import argparse
import logging
import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from model.class_mapping import mapear_classe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

Caixa = tuple[int, int, int, int]  # (x1, y1, x2, y2)
Stamp = tuple[Path, str]  # (caminho do ícone, chave do bucket)


def _carregar_nomes(source: Path) -> list[str]:
    """Lê os nomes de classe do data.yaml do dataset de ícones."""
    config = yaml.safe_load((source / "data.yaml").read_text(encoding="utf-8"))
    nomes = config.get("names", [])
    if isinstance(nomes, dict):
        nomes = [nomes[k] for k in sorted(nomes)]
    return nomes


def _coletar_stamps(source: Path, nomes: list[str], splits: list[str]) -> list[Stamp]:
    """Coleta (imagem de ícone, bucket) para ícones mapeáveis à knowledge_base.

    Args:
        source: Diretório do dataset de ícones.
        nomes: Lista de nomes de classe (indexada pelo id).
        splits: Splits do dataset a percorrer (ex.: ["train"]).

    Returns:
        Lista de pares (caminho da imagem do ícone, chave do bucket STRIDE).
    """
    stamps: list[Stamp] = []
    for split in splits:
        dir_labels = source / split / "labels"
        dir_images = source / split / "images"
        if not dir_labels.is_dir():
            continue
        for lbl in dir_labels.glob("*.txt"):
            linhas = lbl.read_text(encoding="utf-8").splitlines()
            if not linhas or not linhas[0].split():
                continue
            bucket = mapear_classe(nomes[int(linhas[0].split()[0])])
            if bucket is None:
                continue
            img = next(dir_images.glob(f"{lbl.stem}.*"), None)
            if img is not None:
                stamps.append((img, bucket))
    return stamps


def _posicao_sem_sobreposicao(
    canvas: int, tam: int, existentes: list[Caixa], tentativas: int = 40
) -> Caixa | None:
    """Sorteia uma posição para um ícone evitando sobreposição com os já postos.

    Args:
        canvas: Lado do canvas quadrado.
        tam: Lado do ícone a posicionar.
        existentes: Caixas já ocupadas.
        tentativas: Máximo de sorteios antes de desistir.

    Returns:
        Caixa (x1, y1, x2, y2) livre, ou None se não achar após as tentativas.
    """
    for _ in range(tentativas):
        x1 = random.randint(0, canvas - tam)
        y1 = random.randint(0, canvas - tam)
        x2, y2 = x1 + tam, y1 + tam
        colide = any(not (x2 < e[0] or x1 > e[2] or y2 < e[1] or y1 > e[3]) for e in existentes)
        if not colide:
            return (x1, y1, x2, y2)
    return None


def _desenhar_conexoes(draw: ImageDraw.ImageDraw, caixas: list[Caixa]) -> None:
    """Desenha linhas leves entre alguns ícones, simulando setas de um diagrama."""
    centros = [((c[0] + c[2]) // 2, (c[1] + c[3]) // 2) for c in caixas]
    for i in range(len(centros) - 1):
        if random.random() < 0.6:
            draw.line([centros[i], centros[i + 1]], fill=(180, 180, 180), width=2)


def _gerar_imagem(
    stamps: list[Stamp],
    buckets_idx: dict[str, int],
    canvas: int,
    faixa_qtd: tuple[int, int],
    faixa_tam: tuple[int, int],
) -> tuple[Image.Image, list[str]]:
    """Gera uma imagem sintética e seus rótulos YOLO.

    Args:
        stamps: Pool de ícones (imagem, bucket).
        buckets_idx: Mapa bucket -> índice de classe.
        canvas: Lado do canvas quadrado.
        faixa_qtd: (mín, máx) de ícones por imagem.
        faixa_tam: (mín, máx) do lado de cada ícone.

    Returns:
        Tupla (imagem, linhas_de_rotulo_yolo).
    """
    img = Image.new("RGB", (canvas, canvas), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    caixas: list[Caixa] = []
    rotulos: list[str] = []

    for _ in range(random.randint(*faixa_qtd)):
        caminho, bucket = random.choice(stamps)
        tam = random.randint(*faixa_tam)
        pos = _posicao_sem_sobreposicao(canvas, tam, caixas)
        if pos is None:
            continue
        icone = Image.open(caminho).convert("RGB").resize((tam, tam))
        img.paste(icone, (pos[0], pos[1]))
        caixas.append(pos)
        cx = (pos[0] + tam / 2) / canvas
        cy = (pos[1] + tam / 2) / canvas
        wn = hn = tam / canvas
        rotulos.append(f"{buckets_idx[bucket]} {cx:.6f} {cy:.6f} {wn:.6f} {hn:.6f}")

    _desenhar_conexoes(draw, caixas)
    return img, rotulos


def _escrever_split(
    stamps: list[Stamp],
    buckets_idx: dict[str, int],
    out: Path,
    split: str,
    n: int,
    canvas: int,
    faixa_qtd: tuple[int, int],
    faixa_tam: tuple[int, int],
) -> None:
    """Gera e grava `n` imagens sintéticas (com rótulos) para um split."""
    dir_img = out / split / "images"
    dir_lbl = out / split / "labels"
    dir_img.mkdir(parents=True, exist_ok=True)
    dir_lbl.mkdir(parents=True, exist_ok=True)

    for i in range(n):
        img, rotulos = _gerar_imagem(stamps, buckets_idx, canvas, faixa_qtd, faixa_tam)
        img.save(dir_img / f"synt_{i:05d}.jpg", quality=90)
        (dir_lbl / f"synt_{i:05d}.txt").write_text(
            "\n".join(rotulos) + ("\n" if rotulos else ""), encoding="utf-8"
        )
    logger.info("Split '%s': %d imagens sintéticas geradas", split, n)


def gerar(
    source: str | Path,
    out: str | Path,
    n_train: int = 400,
    n_val: int = 80,
    canvas: int = 1280,
    faixa_qtd: tuple[int, int] = (5, 18),
    faixa_tam: tuple[int, int] = (48, 110),
) -> Path:
    """Gera o dataset sintético completo e o data.yaml correspondente.

    Args:
        source: Diretório do dataset de ícones AWS.
        out: Diretório de saída do dataset sintético.
        n_train: Número de imagens de treino.
        n_val: Número de imagens de validação.
        canvas: Lado do canvas quadrado.
        faixa_qtd: (mín, máx) de ícones por imagem.
        faixa_tam: (mín, máx) do lado de cada ícone.

    Returns:
        Caminho do dataset_stride.yaml gerado.

    Raises:
        RuntimeError: Se não houver ícones mapeáveis no dataset de origem.
    """
    source, out = Path(source), Path(out)
    nomes = _carregar_nomes(source)
    stamps_train = _coletar_stamps(source, nomes, ["train"])
    stamps_val = _coletar_stamps(source, nomes, ["valid", "test"]) or stamps_train
    if not stamps_train:
        raise RuntimeError("Nenhum ícone mapeável encontrado no dataset de origem.")

    buckets = sorted({b for _, b in stamps_train})
    buckets_idx = {b: i for i, b in enumerate(buckets)}
    logger.info("Ícones-carimbo: %d (train), %d (val) | classes: %s",
                len(stamps_train), len(stamps_val), buckets)

    _escrever_split(stamps_train, buckets_idx, out, "train", n_train, canvas, faixa_qtd, faixa_tam)
    _escrever_split(stamps_val, buckets_idx, out, "valid", n_val, canvas, faixa_qtd, faixa_tam)

    config = {"path": str(out.resolve()), "train": "train/images", "val": "valid/images",
              "names": buckets, "nc": len(buckets)}
    caminho_yaml = out / "dataset_stride.yaml"
    caminho_yaml.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    logger.info("Config salvo em %s", caminho_yaml)
    return caminho_yaml


def main() -> None:
    """Ponto de entrada para execução via linha de comando."""
    parser = argparse.ArgumentParser(description="Gera diagramas sintéticos para treino do detector.")
    parser.add_argument("--source", default="data/annotated/aws-icon-detection")
    parser.add_argument("--out", default="data/annotated/synthetic")
    parser.add_argument("--n-train", type=int, default=400)
    parser.add_argument("--n-val", type=int, default=80)
    parser.add_argument("--canvas", type=int, default=1280)
    args = parser.parse_args()

    caminho = gerar(args.source, args.out, args.n_train, args.n_val, args.canvas)
    print(f"Dataset sintético gerado. Treine com: python -m model.train --data {caminho}")


if __name__ == "__main__":
    main()
