# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é o projeto

MVP do Hackathon FIAP POS TECH — Fase 5 (empresa fictícia "FIAP Software Security").
Recebe uma imagem de diagrama de arquitetura e gera um **Relatório de Modelagem de
Ameaças STRIDE**. A detecção de componentes é **supervisionada com YOLOv8**; a Claude
API entra apenas no fim, para o resumo executivo e as recomendações do relatório.

## Pipeline (o coração do sistema)

O fluxo vive em `stride/report_generator.py::gerar_relatorio` e encadeia 4 etapas.
Entender esse encadeamento evita a maioria dos erros:

1. **Detecção** — `model/predict.py::detectar_componentes(imagem)` roda o YOLOv8 e
   retorna `{"componentes_detectados": [chaves...], "observacoes": str}`. Esse **contrato
   de retorno é fixo**: API, Streamlit e o gerador dependem dele. As classes cruas do
   modelo passam por `model/class_mapping.py::mapear_classe` para virar chaves da
   knowledge_base; classes sem correspondência são descartadas.
2. **Mapeamento STRIDE** — `stride/knowledge_base.py::mapear_componentes` converte as
   chaves em ameaças + contramedidas (dado 100% estático, sem IA).
3. **Enriquecimento via Claude** — `_gerar_resumo_e_recomendacoes` chama a API
   (modelo `claude-sonnet-4-6`, ver constante `MODELO_TEXTO`). O prompt **exige** que a
   resposta contenha o literal `## Recomendações Prioritárias` como separador — se faltar,
   levanta `RuntimeError`. Ao mexer nesse prompt, mantenha esse contrato.
4. **Template** — `stride/templates/report_template.md` é preenchido por substituição de
   placeholders (`{{projeto}}`, `{{data}}`, `{{arquitetura}}`, `{{lista_componentes}}`,
   `{{analise_ameacas}}`, `{{resumo}}`, `{{recomendacoes}}`). Adicionar um placeholder no
   template exige um `.replace(...)` correspondente no gerador.

`stride/pdf_export.py` converte o Markdown final em PDF (markdown → HTML → xhtml2pdf).

### As três chaves que amarram tudo

`class_mapping.py`, `knowledge_base.py` e o `predict.py` compartilham o mesmo vocabulário
de ~11 chaves de componente (`usuario`, `api_gateway`, `banco_dados`, ...). `class_mapping`
tem um `_validar_mapeamento()` que roda no import e falha se alguma regra apontar para uma
chave inexistente na knowledge_base. **Ao adicionar um componente, atualize os três lugares.**

## Como a detecção é treinada (não-óbvio)

O dataset público do Roboflow (`aws-icon-detection`) tem **um ícone por imagem** — treinar
direto nele só ensina a classificar um ícone que preenche a tela, não a *localizar* vários
num diagrama. Por isso há duas rotas para produzir o `dataset_stride.yaml` de treino:

- `model/generate_synthetic.py` — **rota recomendada** (usada no README). Cola os ícones
  como "carimbos" em posições/escalas aleatórias num canvas, com linhas simulando conexões,
  gerando bounding boxes reais de detecção multi-componente.
- `model/prepare_dataset.py` — apenas reescreve os rótulos originais consolidando as
  centenas de classes AWS nas ~11 categorias STRIDE (mantém uma-imagem-por-ícone).

Ambos consolidam via `class_mapping.mapear_classe` e emitem `dataset_stride.yaml`.

`imgsz=1024` é usado tanto no treino quanto na inferência **de propósito** — ícones são
pequenos e se perdem no default 640 do YOLO. Se mudar num lado, mude no outro
(`train.py` default e `predict.py::IMGSZ_INFERENCIA`).

## Comandos

Rode **sempre a partir da raiz do projeto** com o venv ativo. Os módulos usam imports
absolutos (`from stride...`, `from model...`), então use `python -m`, nunca
`python model/predict.py`.

```bash
# Preparar modelo (uma vez): baixar → gerar sintético → treinar
python -m model.download_dataset
python -m model.generate_synthetic
python -m model.train --device 0            # salva best.pt em MODEL_WEIGHTS_PATH

# Usar o pipeline
python -m stride.report_generator --input data/test/arquitetura_aws.png --pdf
python -m model.predict --image data/test/arquitetura_aws.png   # só a detecção
streamlit run app/streamlit_app.py
uvicorn api.main:app --reload               # POST /analyze, POST /analyze/download, GET /health
```

Não há suíte de testes nem linter configurados no repo.

## Ambiente e gotchas de Windows/CUDA

- **Ordem de instalação importa**: instale `torch`/`torchvision` com CUDA *antes* do
  `requirements.txt`, senão o pip traz a versão CPU-only. Os wheels cu121 foram
  descontinuados no Python 3.12 — use cu124:
  `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124`
- **Treino no Windows**: `train.py` usa `workers=0` (evita `WinError 1455`/pagefile ao
  recarregar DLLs do CUDA) e `plots=False` (evita crash em matplotlib/seaborn). Não
  reative esses defaults sem necessidade.
- Config sempre via `.env` (nunca hardcoded): `ANTHROPIC_API_KEY`, `ROBOFLOW_API_KEY`,
  `MODEL_WEIGHTS_PATH`, `REPORT_OUTPUT_DIR`. O gerador falha cedo se a chave Anthropic
  faltar; `predict.py` falha se `best.pt` não existir (modelo não treinado).

## Convenções de código

- Docstrings e nomes de função/variável em **português**; type hints obrigatórios.
- `logging` em vez de `print` no código de biblioteca; funções de responsabilidade única.
- Dependências pesadas (`ultralytics`, `roboflow`) têm **import tardio** dentro das funções
  que as usam — preserve esse padrão para não pagar o custo de import no resto do pipeline.
- `metodologia STRIDE`: S(poofing), T(ampering), R(epudiation), I(nformation disclosure),
  D(enial of service), E(levation of privilege).

## Status / pendências do hackathon

Implementado: knowledge_base, pipeline completo de detecção→relatório→PDF, API, Streamlit,
scripts de dataset/treino. Pendente: rodar o treino real para gerar `best.pt`, posicionar
`data/test/arquitetura_{aws,azure}.png`, validar ponta-a-ponta nas 2 arquiteturas, e o
vídeo de até 15 min. Priorize o MVP funcional antes de otimizações.
