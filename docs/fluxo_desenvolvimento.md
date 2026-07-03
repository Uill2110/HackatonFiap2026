# Fluxo de Desenvolvimento

Documentação do fluxo utilizado para desenvolver o MVP de Modelagem de Ameaças
STRIDE a partir de imagens de diagramas de arquitetura.

## 1. Visão geral da solução

```
[Imagem do diagrama]
      │
      ▼
[Detecção supervisionada — YOLOv8 treinado]  (model/predict.py)
      │  classes YOLO → chaves da knowledge_base (model/class_mapping.py)
      ▼
[Base de conhecimento STRIDE]  (stride/knowledge_base.py)
      │  componente → ameaças (S,T,R,I,D,E) + contramedidas
      ▼
[Claude API — enriquecimento textual]  (stride/report_generator.py)
      │  resumo executivo + recomendações priorizadas
      ▼
[Relatório STRIDE em Markdown]  →  [PDF]  (stride/pdf_export.py)
```

A detecção de componentes é **supervisionada** (YOLOv8). O Claude API
(`claude-sonnet-4-6`) é usado **apenas** para o texto do relatório (resumo e
recomendações), não para a detecção.

## 2. Pipeline de execução (runtime)

1. Upload da imagem (Streamlit `app/` ou API `api/`).
2. Inferência YOLOv8 em `imgsz=1024` (`model/predict.py`) → componentes detectados.
3. Mapeamento componente → ameaças STRIDE (`stride/knowledge_base.py`, 11 componentes).
4. Claude API gera resumo executivo + recomendações (`stride/report_generator.py`).
5. Relatório preenchido no template e salvo em Markdown; opcionalmente exportado
   para PDF (`stride/pdf_export.py`).

## 3. Pipeline de preparação do modelo (detecção supervisionada)

```bash
python -m model.download_dataset      # dataset de ícones AWS (Roboflow Universe)
python -m model.generate_synthetic    # gera diagramas sintéticos + data.yaml
python -m model.train --device 0      # treina YOLOv8 na GPU → model/weights/best.pt
```

## 4. Decisões técnicas relevantes

### Detecção via YOLOv8 (não Claude Vision)
O enunciado pede **detecção supervisionada** (dataset → anotação → treino). Por
isso a detecção usa um modelo YOLOv8 treinado, e não visão zero-shot.

### Dataset sintético (decisão central)
O dataset público disponível (`aws-icon-detection`, Roboflow) contém **um ícone
isolado por imagem** (caixa cobrindo a imagem inteira). Um modelo treinado
diretamente nele aprende a **classificar um ícone único**, e não a **localizar
vários ícones** — resultado: **0 detecções** em diagramas de arquitetura reais.

Solução: `model/generate_synthetic.py` usa esses ícones como "carimbos",
compondo diagramas sintéticos (vários ícones em posições/escalas aleatórias num
canvas, com linhas simulando conexões e bounding boxes corretas). O modelo passa
a aprender a localizar múltiplos componentes. As centenas de classes de ícone
AWS são consolidadas nas ~11 categorias da knowledge_base por regras de
palavra-chave (`model/class_mapping.py`).

### Consolidação de classes
`model/class_mapping.py` traduz nomes de classe AWS (ex.: `Res_Amazon-Aurora-Instance`)
para as chaves genéricas da knowledge_base (ex.: `banco_dados`) via palavras-chave.
Classes sem correspondência são descartadas.

### Ambiente / dependências
- Gerenciado com **uv**; **torch com CUDA** instalado do índice `cu124`
  (os wheels `cu121` foram descontinuados no Python 3.12).
- Treino no Windows usa `--workers 0` e `plots=False` para evitar crash de
  paging file / DLLs do CUDA (`WinError 1455` / segfault).
- Versões alinhadas para compatibilidade: `numpy 2.x` exige `ultralytics ≥ 8.4`
  (uso de `np.trapezoid`); `anthropic ≥ 0.40` para compatibilidade com `httpx`
  recente; `streamlit 1.58` para `use_container_width`.

## 5. Resultados

- Treino (YOLOv8n, imgsz 1024, 60 épocas, RTX 2060): **mAP50 ≈ 0,90**.
- Em um diagrama de arquitetura AWS real: de **0 → ~29 detecções** cobrindo 9 dos
  11 tipos de componentes (Lambda, SQS/SNS, S3, DynamoDB, API Gateway, WAF, IAM,
  load balancer, usuários).
- Relatório STRIDE gerado em Markdown e PDF, com resumo e recomendações via Claude.

## 6. Limitações conhecidas

- O modelo aprendeu com diagramas **sintéticos** (ícones AWS sobre fundo branco);
  generaliza bem para diagramas no estilo AWS oficial, mas pode variar em estilos
  visuais muito diferentes.
- Categorias com poucos ícones-fonte (ex.: `api_gateway`, `load_balancer`) têm
  menos variedade de exemplo.
- É um MVP de viabilidade, não um detector de produção.

## 7. Status

- [x] Estrutura do projeto e base de conhecimento STRIDE
- [x] Download do dataset (Roboflow) + consolidação de classes
- [x] Geração de dataset sintético e treino do YOLOv8 (`best.pt` gerado)
- [x] Detecção supervisionada funcionando em diagrama real
- [x] Gerador de relatório (Markdown) + enriquecimento via Claude
- [x] Exportação para PDF
- [x] Interface Streamlit e API FastAPI (`/analyze`, `/analyze/download`, `/health`)
- [ ] Imagens de teste oficiais das 2 arquiteturas (AWS e Azure) em `data/test/`
- [ ] Vídeo de apresentação (até 15 min)
