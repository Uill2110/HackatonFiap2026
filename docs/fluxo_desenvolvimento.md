# Fluxo de Desenvolvimento

## Pipeline

1. Upload da imagem do diagrama de arquitetura
2. Detecção supervisionada de componentes via **YOLOv8 treinado** (`model/predict.py`)
3. Tradução das classes YOLO → chaves da knowledge_base (`model/class_mapping.py`)
4. Mapeamento componente → ameaças STRIDE (base de conhecimento)
5. Enriquecimento via Claude API (resumo executivo + recomendações)
6. Geração do relatório STRIDE em Markdown / PDF

## Pipeline de treino do modelo (detecção supervisionada)

1. Buscar dataset anotado no Roboflow Universe (`model/download_dataset.py`)
2. Ajustar o mapeamento de classes (`model/class_mapping.py`) conforme o `data.yaml`
3. Treinar o YOLOv8 na GPU (`model/train.py`) → gera `model/weights/best.pt`
4. Inferência usa automaticamente os pesos via `MODEL_WEIGHTS_PATH`

## Status

- [x] Estrutura do projeto
- [x] Base de conhecimento STRIDE
- [x] Dataset anotado (Roboflow Universe) — script de download
- [x] Treino do modelo supervisionado (YOLOv8) — script de treino
- [x] Detecção de componentes (YOLOv8 treinado)
- [x] Gerador de relatório
- [x] Interface Streamlit
- [x] API FastAPI (`/analyze`, `/analyze/download`, `/health`)
- [ ] Executar download + treino com dataset real e gerar `best.pt`
- [ ] Testes com arquiteturas AWS e Azure (faltam imagens em `data/test/`)
- [ ] Exportação para PDF
- [ ] Vídeo de apresentação
