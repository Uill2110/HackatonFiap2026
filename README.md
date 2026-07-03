# STRIDE Threat Modeler

MVP que recebe uma imagem de diagrama de arquitetura de software e gera automaticamente um Relatório de Modelagem de Ameaças baseado na metodologia STRIDE.

Hackathon FIAP POS TECH — Fase 5 | Empresa fictícia: FIAP Software Security

## Setup

Este projeto usa [uv](https://docs.astral.sh/uv/) para gerenciar o ambiente.

```bash
uv venv                       # cria o .venv
# ative: source .venv/bin/activate  (Windows: .venv\Scripts\activate)

# Instale o torch COM CUDA antes do requirements.txt (o índice padrão traz a
# versão CPU-only). Os wheels cu121 foram descontinuados no Python 3.12; use cu124:
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

uv pip install -r requirements.txt
cp .env.example .env          # preencher ANTHROPIC_API_KEY e ROBOFLOW_API_KEY
```

> Com pip tradicional, troque `uv pip install` por `pip install` e `uv venv` por
> `python -m venv .venv`.

## Detecção supervisionada (YOLOv8)

A detecção de componentes usa um modelo **YOLOv8 treinado** (detecção
supervisionada). O dataset público do Roboflow contém ícones AWS isolados
(um por imagem), então geramos **diagramas sintéticos** — colando esses ícones,
em posições e escalas variadas, num canvas — para o modelo aprender a localizar
múltiplos componentes num diagrama real. Fluxo de preparação do modelo:

```bash
# 1. Baixar o dataset de ícones AWS (Roboflow, formato YOLOv8)
python -m model.download_dataset

# 2. Gerar os diagramas sintéticos + data.yaml (consolidados nas categorias STRIDE)
python -m model.generate_synthetic

# 3. Treinar o modelo na GPU (usa os defaults: dataset sintético, imgsz 1024, workers 0)
python -m model.train --device 0
```

O treino salva os pesos em `MODEL_WEIGHTS_PATH` (padrão `model/weights/best.pt`),
usado automaticamente na inferência.

> No Windows, o treino usa `--workers 0` por padrão para evitar um erro de
> paging file ao recarregar as DLLs do CUDA. `model/class_mapping.py` traduz as
> classes AWS para as chaves da knowledge_base — só precisa de ajuste se você
> trocar de dataset.

## Uso

> Rode **sempre a partir da raiz do projeto**, com o ambiente ativo
> (`.venv\Scripts\activate` no Windows / `source .venv/bin/activate`). Os
> módulos usam imports absolutos (`stride`, `model`).

```bash
# Interface web (a partir da raiz do projeto)
streamlit run app/streamlit_app.py

# API
uvicorn api.main:app --reload

# Geração de relatório via linha de comando
python -m stride.report_generator --input data/test/arquitetura_aws.png

# Detecção de componentes isolada (apenas inferência)
python -m model.predict --image data/test/arquitetura_aws.png
```

## Estrutura

- `data/` — imagens de arquitetura (raw, anotadas, testes)
- `model/` — detecção supervisionada de componentes (dataset → treino → inferência YOLOv8)
- `stride/` — base de conhecimento STRIDE e gerador de relatório
- `api/` — FastAPI
- `app/` — interface Streamlit
- `docs/` — documentação e exemplos de relatório

## Metodologia STRIDE

| Letra | Ameaça | Descrição |
|---|---|---|
| S | Spoofing | Falsificação de identidade |
| T | Tampering | Adulteração de dados |
| R | Repudiation | Negação de ações realizadas |
| I | Information Disclosure | Exposição indevida de dados |
| D | Denial of Service | Indisponibilidade do sistema |
| E | Elevation of Privilege | Escalada de privilégios |
