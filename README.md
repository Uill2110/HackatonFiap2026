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
supervisionada). O fluxo de preparação do modelo:

```bash
# 1. Baixar o dataset anotado do Roboflow Universe (formato YOLOv8)
python -m model.download_dataset

# 2. Conferir as classes impressas e ajustar model/class_mapping.py
#    (mapeia cada classe do dataset -> chave da knowledge_base)

# 3. Treinar o modelo (usa GPU via --device 0)
python -m model.train --data data/annotated/dataset.yaml --epochs 50 --device 0
```

O treino salva os pesos em `MODEL_WEIGHTS_PATH` (padrão `model/weights/best.pt`),
usado automaticamente na inferência.

## Uso

> Execute sempre a partir da raiz do projeto — os módulos usam imports
> absolutos, por isso são executados como módulos (`python -m ...`).

```bash
# Interface web
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
