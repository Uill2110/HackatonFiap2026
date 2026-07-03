# CLAUDE.md — Hackathon: Modelagem de Ameaças com IA (STRIDE)

## Visão geral do projeto

Sistema de MVP que recebe uma imagem de diagrama de arquitetura de software e gera automaticamente um **Relatório de Modelagem de Ameaças** baseado na metodologia STRIDE.

**Contexto:** Hackathon FIAP POS TECH — Fase 5  
**Empresa fictícia:** FIAP Software Security  
**Objetivo:** Validar a viabilidade de uma feature de detecção supervisionada de ameaças

---

## Stack tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem principal | Python 3.11+ |
| Visão computacional | YOLOv8 (ultralytics) ou GPT-4 Vision / Claude via API |
| LLM para relatório | Anthropic Claude API (claude-sonnet-4-6) |
| Backend / API | FastAPI |
| Interface web | Streamlit (MVP simples) |
| Anotação de dataset | Roboflow ou LabelImg |
| Controle de versão | Git + GitHub |
| Ambiente | Python venv + requirements.txt |

---

## Estrutura do projeto

```
stride-threat-modeler/
├── CLAUDE.md                  # Este arquivo
├── README.md
├── requirements.txt
├── .env.example               # Variáveis de ambiente (nunca commitar .env)
│
├── data/
│   ├── raw/                   # Imagens brutas de arquiteturas
│   ├── annotated/             # Dataset anotado (YOLO format)
│   └── test/                  # Arquiteturas de avaliação do hackathon
│       ├── arquitetura_aws.png
│       └── arquitetura_azure.png
│
├── model/
│   ├── train.py               # Script de treinamento YOLOv8
│   ├── predict.py             # Inferência: imagem → componentes detectados
│   └── weights/               # Pesos do modelo treinado (.pt)
│
├── stride/
│   ├── knowledge_base.py      # Mapeamento componente → ameaças STRIDE
│   ├── report_generator.py    # Gera relatório usando Claude API
│   └── templates/
│       └── report_template.md
│
├── api/
│   ├── main.py                # FastAPI app
│   └── routes/
│       └── analyze.py         # POST /analyze → relatório STRIDE
│
├── app/
│   └── streamlit_app.py       # Interface web para upload e visualização
│
└── docs/
    ├── fluxo_desenvolvimento.md
    └── exemplos_relatorio/
```

---

## Fluxo principal do sistema

```
[Imagem de diagrama]
        ↓
[Modelo de detecção] → identifica componentes (usuário, API, DB, firewall...)
        ↓
[Base de conhecimento STRIDE] → mapeia ameaças por componente
        ↓
[Claude API] → enriquece com linguagem natural e contramedidas
        ↓
[Relatório STRIDE] → PDF ou Markdown estruturado
```

---

## Metodologia STRIDE — referência rápida

| Letra | Ameaça | Descrição |
|---|---|---|
| S | Spoofing | Falsificação de identidade |
| T | Tampering | Adulteração de dados |
| R | Repudiation | Negação de ações realizadas |
| I | Information Disclosure | Exposição indevida de dados |
| D | Denial of Service | Indisponibilidade do sistema |
| E | Elevation of Privilege | Escalada de privilégios |

---

## Componentes de arquitetura suportados (MVP)

- Usuário / cliente externo
- API Gateway
- Load Balancer
- Servidor de aplicação
- Banco de dados (RDS, SQL, NoSQL)
- Cache (Redis, ElastiCache)
- Fila de mensagens (SQS, RabbitMQ)
- Serviço de autenticação (IAM, OAuth)
- CDN / WAF / Shield
- Storage (S3, Blob)
- Serviço de monitoramento (CloudWatch, CloudTrail)

---

## Comandos úteis

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar interface web (Streamlit)
streamlit run app/streamlit_app.py

# Rodar API FastAPI
uvicorn api.main:app --reload

# Treinar modelo YOLOv8
python model/train.py --data data/annotated/dataset.yaml --epochs 50

# Rodar inferência em imagem
python model/predict.py --image data/test/arquitetura_aws.png

# Gerar relatório STRIDE completo
python stride/report_generator.py --input data/test/arquitetura_aws.png
```

---

## Variáveis de ambiente (.env)

```
ANTHROPIC_API_KEY=sk-...
MODEL_WEIGHTS_PATH=model/weights/best.pt
REPORT_OUTPUT_DIR=docs/exemplos_relatorio/
```

---

## Padrões de código

- Docstrings em português para funções principais
- Type hints obrigatórios em todas as funções
- Arquivos de configuração sempre via variáveis de ambiente (nunca hardcoded)
- Nenhuma chave de API deve aparecer no código ou commits
- Logs com `logging` (não `print`) em produção
- Funções com responsabilidade única — máximo 40 linhas por função

---

## Entregáveis do hackathon

- [ ] Código no GitHub com README completo
- [ ] `docs/fluxo_desenvolvimento.md` — documentação do fluxo
- [ ] Vídeo de até 15 minutos explicando a solução
- [ ] Sistema rodando nas 2 arquiteturas de teste (AWS e Azure)

---

## Status atual (continuar a partir daqui)

Já implementado:

- [x] Estrutura de diretórios, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- [x] `stride/knowledge_base.py` — mapeamento componente → ameaças STRIDE (11 componentes do MVP)
- [x] **Detecção supervisionada com YOLOv8** (substituiu o Claude Vision):
  - [x] `model/download_dataset.py` — baixa dataset de ícones AWS do Roboflow Universe (formato YOLOv8)
  - [x] `model/class_mapping.py` — traduz classe AWS → chave da knowledge_base (regras por palavra-chave)
  - [x] `model/generate_synthetic.py` — gera diagramas sintéticos (ícones em canvas) p/ o modelo aprender a localizar múltiplos componentes; peça central da detecção em diagramas reais
  - [x] `model/train.py` — treina o YOLOv8 na GPU (imgsz 1024, `workers=0`/`plots=False` no Windows) e salva `best.pt` em `MODEL_WEIGHTS_PATH`
  - [x] `model/predict.py` — inferência via modelo treinado em `imgsz=1024` (mesmo contrato de retorno)
- [x] `stride/report_generator.py` — pipeline completo (detecção → STRIDE → resumo/recomendações via Claude → Markdown)
- [x] `stride/pdf_export.py` — exportação do relatório Markdown para PDF (markdown → HTML → xhtml2pdf); CLI `--pdf` e botão no Streamlit
- [x] `app/streamlit_app.py` — upload de imagem, geração e exibição/download do relatório (.md e .pdf)
- [x] `api/main.py` + `api/routes/analyze.py` — endpoints `POST /analyze` (JSON), `POST /analyze/download` (arquivo `.md`) e `GET /health`, expondo `stride.report_generator.gerar_relatorio`

Pendente:

- [ ] Instalar torch com CUDA + `requirements.txt` e configurar `.env` real (`ANTHROPIC_API_KEY`, `ROBOFLOW_API_KEY`)
- [ ] Rodar `download_dataset` + ajustar `class_mapping` + `train` para gerar `best.pt` real
- [ ] Obter/posicionar imagens de teste em `data/test/` (`arquitetura_aws.png`, `arquitetura_azure.png`)
- [ ] Testar pipeline ponta a ponta com as 2 arquiteturas (AWS e Azure)
- [ ] Validar relatório gerado e ajustar `stride/templates/report_template.md` se necessário
- [x] Exportação do relatório para PDF (`stride/pdf_export.py`)
- [ ] Vídeo de até 15 minutos explicando a solução

## Notas de execução

- `model/predict.py` e `stride/report_generator.py` usam imports absolutos
  (`from model.predict import ...`, `from stride.knowledge_base import ...`).
  Execute sempre a partir da raiz do projeto, com `python -m`:
  ```bash
  python -m model.download_dataset
  python -m model.train --data data/annotated/dataset.yaml --epochs 50 --device 0
  python -m stride.report_generator --input data/test/arquitetura_aws.png
  python -m model.predict --image data/test/arquitetura_aws.png
  streamlit run app/streamlit_app.py
  ```

---

## Notas importantes para o Claude Code

- Priorize sempre o MVP funcional antes de otimizações
- A detecção de componentes é **supervisionada com YOLOv8** (dataset do Roboflow → treino → inferência). O Claude API é usado apenas para o resumo executivo e as recomendações do relatório (`stride/report_generator.py`)
- O relatório STRIDE deve ser gerado em Markdown e exportável como PDF
- Todas as dependências devem estar em `requirements.txt`
- O projeto deve rodar com um único comando após configurar o `.env`
