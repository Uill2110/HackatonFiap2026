"""
Mapeamento entre classes de ícones AWS (dataset do Roboflow) e as chaves da base
de conhecimento STRIDE (`stride/knowledge_base.py`).

O dataset `aws-icon-detection` possui centenas de classes de granularidade fina
(ex.: "Res_Amazon-Aurora-Instance", "Arch_AWS-Lambda"). A base de conhecimento
usa ~11 chaves genéricas (ex.: "banco_dados", "servidor_aplicacao"). Como mapear
cada nome à mão é inviável, o mapeamento é feito por **regras de palavra-chave**:
o nome da classe é normalizado e comparado com um conjunto de tokens; a primeira
regra que casar define a chave.

Este mapeamento é usado tanto para consolidar os rótulos do dataset antes do
treino (`model/prepare_dataset.py`) quanto, por robustez, na inferência
(`model/predict.py`).
"""

import logging

from stride.knowledge_base import listar_componentes

logger = logging.getLogger(__name__)

# Regras ordenadas (mais específicas primeiro). Cada regra é (tokens, chave):
# se qualquer token aparecer como substring no nome normalizado, retorna a chave.
# A ordem importa para evitar colisões (ex.: "elasticache" antes de regras de
# compute; "load_balanc" nunca deve casar via "elastic").
REGRAS_PALAVRA_CHAVE: list[tuple[tuple[str, ...], str]] = [
    # Cache (antes de compute; "elasticache" contém "cache")
    (("elasticache", "memcached", "_redis", "cache", "_dax"), "cache"),
    # Load balancer
    (("load_balanc", "load_balancer", "elastic_load", "_elb", "_alb", "_nlb"), "load_balancer"),
    # CDN / WAF / Shield / Firewall
    (("cloudfront", "_waf", "shield", "firewall", "global_accelerator"), "cdn_waf"),
    # Monitoramento / auditoria
    (("cloudwatch", "cloudtrail", "x_ray", "xray", "aws_config", "_config_"), "monitoramento"),
    # Autenticação / identidade
    (
        ("identity", "_iam", "cognito", "secrets_manager", "directory_service", "sso", "_auth"),
        "servico_autenticacao",
    ),
    # API Gateway (usar "api_gateway" para não pegar transit/nat/internet gateway)
    (("api_gateway", "appsync"), "api_gateway"),
    # Fila / mensageria
    (
        ("simple_queue", "_sqs", "simple_notification", "_sns", "kafka", "_msk", "_mq",
         "eventbridge", "kinesis", "queue"),
        "fila_mensagens",
    ),
    # Banco de dados
    (
        ("aurora", "dynamodb", "_rds", "relational_database", "redshift", "documentdb",
         "neptune", "database", "_db_", "elasticache_notyet", "memorydb", "timestream",
         "keyspaces"),
        "banco_dados",
    ),
    # Storage
    (
        ("simple_storage", "_s3", "s3_", "_efs", "_ebs", "_fsx", "glacier", "storage_gateway",
         "backup", "storage", "bucket"),
        "storage",
    ),
    # Servidor de aplicação / compute
    (
        ("_ec2", "ec2_", "lambda", "fargate", "_ecs", "_eks", "elastic_beanstalk", "compute",
         "instance", "app_runner", "lightsail", "_server", "batch"),
        "servidor_aplicacao",
    ),
    # Usuário / cliente externo
    (
        ("_user", "users", "office_building", "client", "mobile", "browser", "corporate"),
        "usuario",
    ),
]

_CHAVES_VALIDAS = set(listar_componentes())


def _normalizar(nome_classe: str) -> str:
    """Normaliza um nome de classe para comparação por substring.

    Args:
        nome_classe: Nome da classe conforme o dataset/modelo.

    Returns:
        Nome em minúsculas com espaços/hífens convertidos para underscore.
    """
    return nome_classe.strip().lower().replace(" ", "_").replace("-", "_")


def mapear_classe(nome_classe: str) -> str | None:
    """Traduz o nome de uma classe para uma chave da knowledge_base.

    Se o nome já for uma chave válida da knowledge_base (caso do modelo já
    treinado com classes consolidadas), retorna a própria chave. Caso
    contrário, aplica as regras de palavra-chave.

    Args:
        nome_classe: Nome da classe (do dataset AWS ou do modelo consolidado).

    Returns:
        Chave correspondente da knowledge_base, ou None se não houver
        correspondência.
    """
    normalizado = _normalizar(nome_classe)

    # Identidade: classe já é uma chave da knowledge_base (modelo consolidado).
    if normalizado in _CHAVES_VALIDAS:
        return normalizado

    for tokens, chave in REGRAS_PALAVRA_CHAVE:
        if any(token in normalizado for token in tokens):
            return chave

    logger.debug("Classe sem mapeamento: %s", nome_classe)
    return None


def _validar_mapeamento() -> None:
    """Garante que todas as regras apontam para chaves válidas da knowledge_base.

    Raises:
        ValueError: Se alguma chave de destino não existir em `knowledge_base`.
    """
    destinos = {chave for _, chave in REGRAS_PALAVRA_CHAVE}
    invalidas = destinos - _CHAVES_VALIDAS
    if invalidas:
        raise ValueError(f"Chaves de mapeamento inexistentes na knowledge_base: {invalidas}")


_validar_mapeamento()
