"""
Testes do mapeamento classe AWS -> chave da knowledge_base
(`model.class_mapping`).

As regras de palavra-chave são a peça mais frágil da detecção: a ordem importa
(ex.: "elasticache" contém "cache" e não pode cair em compute/banco). Estes
testes fixam o comportamento esperado das regras e garantem que todo destino
aponta para uma chave existente na knowledge_base.
"""

import pytest

from model.class_mapping import REGRAS_PALAVRA_CHAVE, mapear_classe
from stride.knowledge_base import listar_componentes


def test_identidade_para_chave_valida() -> None:
    """Uma classe que já é chave da base (modelo consolidado) retorna a si mesma."""
    assert mapear_classe("banco_dados") == "banco_dados"
    assert mapear_classe("api_gateway") == "api_gateway"


@pytest.mark.parametrize(
    "nome_classe, esperado",
    [
        # Cache tem precedência sobre compute/banco (colisão via substring "cache")
        ("Arch_Amazon-ElastiCache", "cache"),
        ("Res_Amazon-ElastiCache_Cache-Node", "cache"),
        # Load balancer (não deve casar com cache por "elastic")
        ("Arch_Elastic-Load-Balancing", "load_balancer"),
        # CDN / WAF / Shield
        ("Arch_Amazon-CloudFront", "cdn_waf"),
        ("Arch_AWS-Shield", "cdn_waf"),
        # Monitoramento
        ("Arch_Amazon-CloudWatch", "monitoramento"),
        ("Arch_AWS-CloudTrail", "monitoramento"),
        # Autenticação / identidade
        ("Arch_AWS-Identity-and-Access-Management", "servico_autenticacao"),
        # API Gateway
        ("Arch_Amazon-API-Gateway", "api_gateway"),
        # Fila / mensageria
        ("Arch_Amazon-Simple-Queue-Service", "fila_mensagens"),
        # Banco de dados
        ("Arch_Amazon-Aurora", "banco_dados"),
        ("Arch_Amazon-DynamoDB", "banco_dados"),
        # Storage
        ("Arch_Amazon-Simple-Storage-Service", "storage"),
        # Compute / servidor de aplicação
        ("Arch_AWS-Lambda", "servidor_aplicacao"),
        ("Arch_Amazon-EC2", "servidor_aplicacao"),
        # Usuário / cliente externo
        ("Res_User-", "usuario"),
        ("Res_Office-building", "usuario"),
    ],
)
def test_regras_de_palavra_chave(nome_classe: str, esperado: str) -> None:
    """Classes representativas do dataset AWS caem no bucket STRIDE correto."""
    assert mapear_classe(nome_classe) == esperado


def test_classe_sem_correspondencia_retorna_none() -> None:
    """Classe sem palavra-chave conhecida não é mapeada."""
    assert mapear_classe("Arch_Amazon-Braket") is None


def test_normalizacao_ignora_caixa_e_separadores() -> None:
    """Maiúsculas, espaços e hífens não afetam o mapeamento."""
    assert mapear_classe("amazon dynamodb") == "banco_dados"
    assert mapear_classe("AMAZON-DYNAMODB") == "banco_dados"


def test_todos_os_destinos_sao_chaves_validas() -> None:
    """Toda regra aponta para uma chave existente na knowledge_base.

    Equivale à checagem que `class_mapping._validar_mapeamento` faz no import,
    mas explícita como teste para pegar regressões cedo.
    """
    chaves_validas = set(listar_componentes())
    destinos = {chave for _, chave in REGRAS_PALAVRA_CHAVE}
    assert destinos <= chaves_validas
