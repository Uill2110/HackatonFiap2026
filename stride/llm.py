"""
Abstração de provedor de LLM para a etapa de texto do relatório (resumo
executivo e recomendações).

Permite escolher entre **Anthropic (Claude)** e **OpenAI (GPT)** apenas por
variável de ambiente, sem alterar o restante do pipeline STRIDE. O resto do
sistema (detecção, mapeamento, template) permanece agnóstico ao provedor:
`stride.report_generator` monta o prompt e chama `gerar_resposta` daqui.

Configuração (.env):
    LLM_PROVIDER       anthropic (padrão) | openai
    ANTHROPIC_API_KEY  chave da Anthropic (quando LLM_PROVIDER=anthropic)
    ANTHROPIC_MODEL    modelo Claude (padrão: claude-sonnet-4-6)
    OPENAI_API_KEY     chave da OpenAI (quando LLM_PROVIDER=openai)
    OPENAI_MODEL       modelo OpenAI (padrão: gpt-4o)
"""

import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROVEDOR_PADRAO = "anthropic"
MODELO_ANTHROPIC_PADRAO = "claude-sonnet-4-6"
MODELO_OPENAI_PADRAO = "gpt-4o"
MAX_TOKENS_PADRAO = 1500


def gerar_resposta(prompt: str, max_tokens: int = MAX_TOKENS_PADRAO) -> str:
    """Gera texto a partir do prompt usando o provedor de LLM configurado.

    Args:
        prompt: Texto de entrada enviado ao modelo.
        max_tokens: Máximo de tokens na resposta.

    Returns:
        Texto gerado pelo modelo (já com espaços das bordas removidos).

    Raises:
        RuntimeError: Se `LLM_PROVIDER` for inválido ou a chave de API do
            provedor selecionado não estiver configurada.
    """
    load_dotenv()
    provedor = os.environ.get("LLM_PROVIDER", PROVEDOR_PADRAO).strip().lower()
    logger.info("Gerando texto via provedor de LLM '%s'", provedor)

    if provedor == "anthropic":
        return _gerar_anthropic(prompt, max_tokens)
    if provedor == "openai":
        return _gerar_openai(prompt, max_tokens)

    raise RuntimeError(
        f"LLM_PROVIDER inválido: {provedor!r}. Use 'anthropic' ou 'openai'."
    )


def _gerar_anthropic(prompt: str, max_tokens: int) -> str:
    """Gera texto usando a Claude API (Anthropic).

    Args:
        prompt: Texto de entrada.
        max_tokens: Máximo de tokens na resposta.

    Returns:
        Texto da resposta do modelo.

    Raises:
        RuntimeError: Se ANTHROPIC_API_KEY não estiver definida.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY não definida no ambiente (.env)")

    # Import tardio: SDK só é necessário quando este provedor é usado.
    from anthropic import Anthropic

    modelo = os.environ.get("ANTHROPIC_MODEL", MODELO_ANTHROPIC_PADRAO)
    client = Anthropic(api_key=api_key)
    resposta = client.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resposta.content[0].text.strip()


def _gerar_openai(prompt: str, max_tokens: int) -> str:
    """Gera texto usando a API da OpenAI (GPT).

    Args:
        prompt: Texto de entrada.
        max_tokens: Máximo de tokens na resposta.

    Returns:
        Texto da resposta do modelo.

    Raises:
        RuntimeError: Se OPENAI_API_KEY não estiver definida.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não definida no ambiente (.env)")

    # Import tardio: SDK só é necessário quando este provedor é usado.
    from openai import OpenAI

    modelo = os.environ.get("OPENAI_MODEL", MODELO_OPENAI_PADRAO)
    client = OpenAI(api_key=api_key)
    resposta = client.chat.completions.create(
        model=modelo,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return (resposta.choices[0].message.content or "").strip()
