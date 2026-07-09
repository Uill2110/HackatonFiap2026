"""
Testes da abstração de provedor de LLM (`stride.llm`).

Cobrem a seleção de provedor, os erros de configuração (chave ausente,
provedor inválido) e o caminho da OpenAI. Nenhum SDK real é necessário: o
caminho da OpenAI é exercitado com um módulo `openai` fake registrado em
`sys.modules`, então não há chamada de rede nem dependência do pacote `openai`.
"""

import sys
import types

import pytest

import stride.llm as llm


def _isolar_ambiente(monkeypatch) -> None:
    """Remove variáveis relevantes e neutraliza o load_dotenv (não ler .env real)."""
    for chave in (
        "LLM_PROVIDER",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_MODEL",
        "OPENAI_MODEL",
    ):
        monkeypatch.delenv(chave, raising=False)
    monkeypatch.setattr(llm, "load_dotenv", lambda *a, **k: None)


def _registrar_openai_fake(monkeypatch, capturado: dict) -> None:
    """Instala um módulo `openai` fake cujo cliente captura os argumentos da chamada."""

    class _FakeCompletions:
        def create(self, model, max_tokens, messages):
            capturado["model"] = model
            capturado["max_tokens"] = max_tokens
            capturado["messages"] = messages
            msg = type("Msg", (), {"content": "  resposta de teste  "})()
            choice = type("Choice", (), {"message": msg})()
            return type("Resp", (), {"choices": [choice]})()

    class _FakeChat:
        def __init__(self):
            self.completions = _FakeCompletions()

    class _FakeOpenAI:
        def __init__(self, api_key):
            capturado["api_key"] = api_key
            self.chat = _FakeChat()

    modulo_fake = types.ModuleType("openai")
    modulo_fake.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", modulo_fake)


def test_provedor_padrao_e_anthropic() -> None:
    """O provedor padrão deve permanecer Anthropic (Claude)."""
    assert llm.PROVEDOR_PADRAO == "anthropic"


def test_provedor_invalido_levanta(monkeypatch) -> None:
    """Um LLM_PROVIDER desconhecido falha com mensagem clara."""
    _isolar_ambiente(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    with pytest.raises(RuntimeError, match="LLM_PROVIDER inválido"):
        llm.gerar_resposta("oi")


def test_openai_sem_chave_levanta(monkeypatch) -> None:
    """Selecionar OpenAI sem OPENAI_API_KEY falha antes de qualquer chamada."""
    _isolar_ambiente(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm.gerar_resposta("oi")


def test_anthropic_sem_chave_levanta(monkeypatch) -> None:
    """Selecionar Anthropic sem ANTHROPIC_API_KEY falha antes de qualquer chamada."""
    _isolar_ambiente(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        llm.gerar_resposta("oi")


def test_openai_usa_cliente_e_modelo_corretos(monkeypatch) -> None:
    """O caminho da OpenAI monta o cliente, usa o modelo padrão e lê a resposta."""
    _isolar_ambiente(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")

    capturado: dict = {}
    _registrar_openai_fake(monkeypatch, capturado)

    resultado = llm.gerar_resposta("prompt-de-teste")

    assert resultado == "resposta de teste"  # .strip() aplicado
    assert capturado["api_key"] == "sk-teste"
    assert capturado["model"] == "gpt-4o"  # OPENAI_MODEL padrão
    assert capturado["messages"] == [{"role": "user", "content": "prompt-de-teste"}]


def test_openai_respeita_modelo_customizado(monkeypatch) -> None:
    """OPENAI_MODEL sobrescreve o modelo padrão."""
    _isolar_ambiente(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    capturado: dict = {}
    _registrar_openai_fake(monkeypatch, capturado)

    llm.gerar_resposta("oi")
    assert capturado["model"] == "gpt-4o-mini"
