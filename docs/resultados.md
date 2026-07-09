# Resultados e Avaliação do Detector

Este documento reporta o desempenho **quantitativo** do detector de componentes
(YOLOv8) — a etapa de visão computacional do pipeline STRIDE. As métricas são
geradas de forma reprodutível por `model/evaluate.py`, que roda `model.val()`
sobre o split de validação do dataset e salva os números e gráficos aqui.

> Reproduzir: `python -m model.evaluate` (gera `docs/avaliacao/metricas.json` e
> copia a matriz de confusão para `docs/avaliacao/`).

## Metodologia de avaliação

- **Modelo:** YOLOv8n (`model/weights/best.pt`).
- **Conjunto:** split de validação do dataset sintético (`data/annotated/synthetic`),
  gerado por `model/generate_synthetic.py` — ícones AWS "carimbados" em canvas
  com caixas verdadeiras. Resolução de avaliação `imgsz=1024` (igual ao treino).
- **Métricas:** precisão, recall, **mAP@50** e **mAP@50-95** (COCO), geral e por classe.

## Resultado do modelo atual

> ⚠️ **Modelo de baseline (treino reduzido).** Os pesos avaliados vêm de um
> treino curto em **CPU** (20 épocas), feito para validar o pipeline ponta a
> ponta. Os números abaixo são o **piso** — o retreino completo (mais épocas /
> mais dados sintéticos, de preferência em GPU/Colab — ver
> [`notebooks`](../notebooks)) eleva bastante o desempenho.

| Métrica | Valor |
|---|---|
| mAP@50 | **0,322** |
| mAP@50-95 | 0,319 |
| Precisão (média) | 0,402 |
| Recall (médio) | 0,547 |

### Por classe (mAP@50)

| Componente | Precisão | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|
| storage | 0,76 | 1,00 | **0,98** | 0,97 |
| servidor_aplicacao | 0,47 | 0,62 | **0,65** | 0,65 |
| banco_dados | 0,26 | 0,93 | **0,50** | 0,49 |
| fila_mensagens | 0,24 | 1,00 | 0,42 | 0,42 |
| cdn_waf | 0,09 | 1,00 | 0,17 | 0,17 |
| usuario | 0,11 | 0,19 | 0,16 | 0,16 |
| api_gateway | 1,00 | 0,00 | 0,15 | 0,15 |
| servico_autenticacao | 0,10 | 0,73 | 0,10 | 0,10 |
| cache | 0,00 | 0,00 | 0,05 | 0,05 |
| load_balancer | 1,00 | 0,00 | 0,04 | 0,04 |

> `monitoramento` não teve instâncias suficientes no split de validação desta
> execução, por isso não aparece na tabela.

### Matriz de confusão

![Matriz de confusão](avaliacao/confusion_matrix.png)

(versão normalizada em [`avaliacao/confusion_matrix_normalized.png`](avaliacao/confusion_matrix_normalized.png))

## Discussão

- **Classes fortes** (`storage`, `servidor_aplicacao`, `banco_dados`) têm ícones
  visualmente distintos e boa representação no dataset — mAP@50 de 0,50 a 0,98.
- **Classes fracas** (`cache`, `load_balancer`, `api_gateway`, `servico_autenticacao`)
  sofrem com (a) poucas épocas de treino, (b) desbalanceamento de classes no
  dataset sintético e (c) ícones parecidos entre si. Recall 0 com precisão 1,0
  (ex.: `api_gateway`, `load_balancer`) indica que o modelo quase não detecta a
  classe, mas acerta quando detecta — sintoma clássico de subtreino/poucos exemplos.
- **Gap sintético → real:** o treino usa colagens de ícones em fundo branco; um
  diagrama real tem fundo colorido, caixas de agrupamento (VPC/subnets) e rótulos.
  Sem um conjunto de teste com diagramas reais anotados, a generalização é uma
  limitação conhecida (ver [`fluxo_desenvolvimento.md`](fluxo_desenvolvimento.md)).

## Próximos passos para melhorar as métricas

1. **Retreino completo** (60+ épocas, `imgsz=1024`) em GPU/Colab.
2. **Balancear o dataset sintético** — garantir contagem semelhante de ícones por
   classe em `model/generate_synthetic.py`.
3. **Aumentar a diversidade** — fundos coloridos e caixas de agrupamento no canvas
   sintético para reduzir o gap para diagramas reais.
4. **Conjunto de teste real anotado** (AWS e Azure) para medir generalização, além
   do split sintético.
