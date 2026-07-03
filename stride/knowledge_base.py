"""
Base de conhecimento STRIDE.

Mapeia componentes de arquitetura de software para as ameaças STRIDE
aplicáveis, incluindo descrição da ameaça no contexto do componente e
contramedidas recomendadas.
"""

from typing import TypedDict


class Ameaca(TypedDict):
    """Representa uma ameaça STRIDE aplicada a um componente."""

    categoria: str
    descricao: str
    contramedidas: list[str]


class ComponenteSTRIDE(TypedDict):
    """Representa o conjunto de ameaças associadas a um componente."""

    nome_exibicao: str
    ameacas: list[Ameaca]


# Categorias STRIDE de referência
CATEGORIAS_STRIDE: dict[str, str] = {
    "S": "Spoofing (Falsificação de identidade)",
    "T": "Tampering (Adulteração de dados)",
    "R": "Repudiation (Negação de ações realizadas)",
    "I": "Information Disclosure (Exposição indevida de dados)",
    "D": "Denial of Service (Indisponibilidade do sistema)",
    "E": "Elevation of Privilege (Escalada de privilégios)",
}


# Base de conhecimento: componente -> ameaças STRIDE
KNOWLEDGE_BASE: dict[str, ComponenteSTRIDE] = {
    "usuario": {
        "nome_exibicao": "Usuário / Cliente Externo",
        "ameacas": [
            {
                "categoria": "S",
                "descricao": "Credenciais de usuário podem ser roubadas ou "
                "reutilizadas para se passar por um usuário legítimo.",
                "contramedidas": [
                    "Autenticação multifator (MFA)",
                    "Políticas de senha forte e bloqueio após tentativas falhas",
                ],
            },
            {
                "categoria": "R",
                "descricao": "Usuário pode negar ter realizado uma ação "
                "dentro do sistema.",
                "contramedidas": [
                    "Registro de auditoria (audit logs) com timestamp e identidade",
                    "Assinatura digital de transações críticas",
                ],
            },
        ],
    },
    "api_gateway": {
        "nome_exibicao": "API Gateway",
        "ameacas": [
            {
                "categoria": "S",
                "descricao": "Requisições falsificadas podem se passar por "
                "clientes autorizados caso a autenticação seja fraca.",
                "contramedidas": [
                    "Validação de tokens (JWT/OAuth2) em toda requisição",
                    "Mutual TLS entre serviços confiáveis",
                ],
            },
            {
                "categoria": "T",
                "descricao": "Payloads podem ser adulterados em trânsito ou "
                "via injeção de parâmetros.",
                "contramedidas": [
                    "Validação e sanitização de entrada",
                    "HTTPS/TLS obrigatório em todas as rotas",
                ],
            },
            {
                "categoria": "D",
                "descricao": "Gateway pode ser sobrecarregado por excesso de "
                "requisições, causando indisponibilidade.",
                "contramedidas": [
                    "Rate limiting e throttling",
                    "Integração com WAF/CDN para mitigação de DDoS",
                ],
            },
            {
                "categoria": "E",
                "descricao": "Falhas de autorização podem permitir acesso a "
                "rotas administrativas por usuários comuns.",
                "contramedidas": [
                    "Controle de acesso baseado em papéis (RBAC)",
                    "Princípio do menor privilégio em políticas de rota",
                ],
            },
        ],
    },
    "load_balancer": {
        "nome_exibicao": "Load Balancer",
        "ameacas": [
            {
                "categoria": "D",
                "descricao": "Pode ser alvo de ataques volumétricos que "
                "esgotam conexões e recursos.",
                "contramedidas": [
                    "Auto-scaling de backends",
                    "Limites de conexão e timeout configurados",
                ],
            },
            {
                "categoria": "T",
                "descricao": "Configurações de roteamento podem ser "
                "adulteradas, redirecionando tráfego para destinos maliciosos.",
                "contramedidas": [
                    "Controle de acesso restrito à configuração de infraestrutura",
                    "Versionamento e revisão de mudanças de configuração (IaC)",
                ],
            },
        ],
    },
    "servidor_aplicacao": {
        "nome_exibicao": "Servidor de Aplicação",
        "ameacas": [
            {
                "categoria": "T",
                "descricao": "Código ou dados em memória/disco podem ser "
                "adulterados por meio de vulnerabilidades de aplicação.",
                "contramedidas": [
                    "Validação de entrada e saída",
                    "Atualizações regulares de dependências e patches de segurança",
                ],
            },
            {
                "categoria": "I",
                "descricao": "Erros não tratados podem expor stack traces, "
                "variáveis de ambiente ou dados sensíveis.",
                "contramedidas": [
                    "Tratamento de erros genérico para o cliente",
                    "Segregação de variáveis sensíveis em cofres de segredos",
                ],
            },
            {
                "categoria": "E",
                "descricao": "Vulnerabilidades de execução remota de código "
                "podem permitir escalada de privilégios no host.",
                "contramedidas": [
                    "Execução com usuário de menor privilégio (non-root)",
                    "Sandboxing/containers com políticas restritivas",
                ],
            },
        ],
    },
    "banco_dados": {
        "nome_exibicao": "Banco de Dados (RDS, SQL, NoSQL)",
        "ameacas": [
            {
                "categoria": "T",
                "descricao": "Dados podem ser adulterados via injeção SQL/NoSQL "
                "ou acesso direto não autorizado.",
                "contramedidas": [
                    "Uso de queries parametrizadas / ORMs",
                    "Restrição de acesso de rede ao banco (security groups/VPC)",
                ],
            },
            {
                "categoria": "I",
                "descricao": "Exposição de dados sensíveis em caso de backup "
                "mal protegido ou acesso indevido.",
                "contramedidas": [
                    "Criptografia em repouso e em trânsito",
                    "Mascaramento de dados sensíveis e controle de acesso por papel",
                ],
            },
            {
                "categoria": "R",
                "descricao": "Alterações em registros podem não ter rastro de "
                "quem as realizou.",
                "contramedidas": [
                    "Habilitar logs de auditoria do banco de dados",
                    "Trilhas de auditoria (audit trail) em tabelas críticas",
                ],
            },
        ],
    },
    "cache": {
        "nome_exibicao": "Cache (Redis, ElastiCache)",
        "ameacas": [
            {
                "categoria": "I",
                "descricao": "Dados sensíveis em cache podem ser acessados "
                "se a instância estiver exposta sem autenticação.",
                "contramedidas": [
                    "Habilitar autenticação (AUTH) e TLS no cache",
                    "Evitar armazenar dados sensíveis em texto puro no cache",
                ],
            },
            {
                "categoria": "D",
                "descricao": "Esgotamento de memória pode causar falhas em "
                "cascata na aplicação.",
                "contramedidas": [
                    "Políticas de expiração (TTL) e eviction adequadas",
                    "Monitoramento de uso de memória com alertas",
                ],
            },
        ],
    },
    "fila_mensagens": {
        "nome_exibicao": "Fila de Mensagens (SQS, RabbitMQ)",
        "ameacas": [
            {
                "categoria": "T",
                "descricao": "Mensagens podem ser adulteradas ou injetadas por "
                "produtores não autorizados.",
                "contramedidas": [
                    "Controle de acesso por produtor/consumidor (IAM policies)",
                    "Assinatura/validação de integridade das mensagens",
                ],
            },
            {
                "categoria": "D",
                "descricao": "Acúmulo excessivo de mensagens (poison queue) "
                "pode degradar o processamento.",
                "contramedidas": [
                    "Dead-letter queues e políticas de retry com limite",
                    "Monitoramento de profundidade da fila com alertas",
                ],
            },
        ],
    },
    "servico_autenticacao": {
        "nome_exibicao": "Serviço de Autenticação (IAM, OAuth)",
        "ameacas": [
            {
                "categoria": "S",
                "descricao": "Tokens roubados ou mal configurados podem "
                "permitir a falsificação de identidade.",
                "contramedidas": [
                    "Tokens de curta duração com refresh seguro",
                    "MFA para contas privilegiadas",
                ],
            },
            {
                "categoria": "E",
                "descricao": "Configurações incorretas de papéis/políticas "
                "podem conceder privilégios excessivos.",
                "contramedidas": [
                    "Revisão periódica de políticas de IAM (least privilege)",
                    "Separação de ambientes e papéis por função",
                ],
            },
        ],
    },
    "cdn_waf": {
        "nome_exibicao": "CDN / WAF / Shield",
        "ameacas": [
            {
                "categoria": "D",
                "descricao": "Apesar da proteção, regras mal configuradas "
                "podem deixar passar ataques de DDoS/L7.",
                "contramedidas": [
                    "Regras de WAF atualizadas (OWASP Core Rule Set)",
                    "Proteção anti-DDoS (ex: AWS Shield) habilitada",
                ],
            },
            {
                "categoria": "T",
                "descricao": "Cache do CDN pode ser envenenado (cache "
                "poisoning) servindo conteúdo malicioso.",
                "contramedidas": [
                    "Validação de cabeçalhos de cache e chaves de cache adequadas",
                    "Invalidação de cache controlada e auditável",
                ],
            },
        ],
    },
    "storage": {
        "nome_exibicao": "Storage (S3, Blob)",
        "ameacas": [
            {
                "categoria": "I",
                "descricao": "Buckets/containers configurados como públicos "
                "podem expor dados sensíveis.",
                "contramedidas": [
                    "Bloqueio de acesso público por padrão",
                    "Criptografia em repouso com chaves gerenciadas",
                ],
            },
            {
                "categoria": "T",
                "descricao": "Objetos podem ser sobrescritos ou removidos por "
                "credenciais comprometidas.",
                "contramedidas": [
                    "Versionamento de objetos e políticas de retenção",
                    "Políticas de acesso restritivas (IAM/bucket policy)",
                ],
            },
        ],
    },
    "monitoramento": {
        "nome_exibicao": "Serviço de Monitoramento (CloudWatch, CloudTrail)",
        "ameacas": [
            {
                "categoria": "R",
                "descricao": "Logs podem ser apagados ou alterados para "
                "esconder atividades maliciosas.",
                "contramedidas": [
                    "Armazenamento de logs imutável (write-once)",
                    "Replicação de logs para conta/região separada",
                ],
            },
            {
                "categoria": "I",
                "descricao": "Logs podem conter dados sensíveis expostos a "
                "quem tem acesso ao serviço de monitoramento.",
                "contramedidas": [
                    "Mascaramento de dados sensíveis em logs",
                    "Controle de acesso restrito aos dashboards e logs",
                ],
            },
        ],
    },
}


def listar_componentes() -> list[str]:
    """Retorna as chaves de todos os componentes suportados pela base."""
    return list(KNOWLEDGE_BASE.keys())


def obter_ameacas(componente: str) -> ComponenteSTRIDE | None:
    """Retorna as ameaças STRIDE associadas a um componente.

    Args:
        componente: Chave do componente (ex: "api_gateway").

    Returns:
        Estrutura com nome de exibição e lista de ameaças, ou None se o
        componente não estiver mapeado na base de conhecimento.
    """
    return KNOWLEDGE_BASE.get(componente)


def mapear_componentes(componentes_detectados: list[str]) -> dict[str, ComponenteSTRIDE]:
    """Mapeia uma lista de componentes detectados para suas ameaças STRIDE.

    Componentes não encontrados na base de conhecimento são ignorados.

    Args:
        componentes_detectados: Lista de chaves de componentes detectados
            na imagem da arquitetura.

    Returns:
        Dicionário componente -> ameaças STRIDE, apenas para componentes
        reconhecidos.
    """
    resultado: dict[str, ComponenteSTRIDE] = {}
    for componente in componentes_detectados:
        info = obter_ameacas(componente)
        if info is not None:
            resultado[componente] = info
    return resultado
