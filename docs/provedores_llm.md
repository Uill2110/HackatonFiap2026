# Provedores de LLM (Claude ou OpenAI)

A etapa de **texto** do relatório STRIDE — o resumo executivo e as
recomendações priorizadas — é gerada por um LLM. O projeto suporta **dois
provedores**, escolhidos por variável de ambiente, sem alterar código:

- **Anthropic (Claude)** — padrão.
- **OpenAI (GPT)** — alternativa, para quem não tem conta/crédito na Anthropic.

As demais etapas (detecção YOLOv8, mapeamento STRIDE, template, PDF) são
**independentes do provedor** e não mudam.

> A troca de provedor afeta **apenas** o resumo e as recomendações. A detecção
> de componentes continua sendo feita localmente pelo modelo YOLOv8 treinado.

## Variáveis de ambiente

| Variável | Quando usar | Padrão |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` ou `openai` | `anthropic` |
| `ANTHROPIC_API_KEY` | `LLM_PROVIDER=anthropic` | — |
| `ANTHROPIC_MODEL` | opcional, sobrescreve o modelo Claude | `claude-sonnet-4-6` |
| `OPENAI_API_KEY` | `LLM_PROVIDER=openai` | — |
| `OPENAI_MODEL` | opcional, sobrescreve o modelo OpenAI | `gpt-4o` |

Só é necessária a chave do provedor **selecionado**. Se a chave do provedor
ativo não estiver definida, o pipeline falha com uma mensagem clara.

## Usar o Claude (padrão)

No `.env`:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-sonnet-4-6   # opcional
```

Nenhuma configuração extra é necessária — este é o comportamento padrão.

## Usar a OpenAI

1. Obtenha uma chave em [platform.openai.com](https://platform.openai.com/api-keys).
2. No `.env`:

   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   # OPENAI_MODEL=gpt-4o   # opcional (ex.: gpt-4o-mini para custo menor)
   ```

3. Rode o pipeline normalmente:

   ```bash
   python -m stride.report_generator --input data/test/arquitetura_teste.jpg --pdf
   ```

A interface Streamlit e a API FastAPI respeitam a mesma configuração — basta
ter o `.env` correto no ambiente onde elas rodam.

## Como funciona internamente

O acoplamento fica isolado em `stride/llm.py`, que expõe
`gerar_resposta(prompt)`. O `stride/report_generator.py` monta o prompt STRIDE,
chama `gerar_resposta` e faz o parsing do resultado — sem saber qual provedor
respondeu. Para adicionar um terceiro provedor no futuro, basta uma nova função
`_gerar_<provedor>` e uma entrada no dispatch de `gerar_resposta`.
