"""
Testes da base de conhecimento STRIDE (`stride.knowledge_base`).

Cobrem o contrato usado pelo restante do pipeline: a estrutura de cada
componente, o mapeamento de componentes detectados para ameaças e o
comportamento com entradas desconhecidas.
"""

from stride.knowledge_base import (
    CATEGORIAS_STRIDE,
    KNOWLEDGE_BASE,
    listar_componentes,
    mapear_componentes,
    obter_ameacas,
)

CATEGORIAS_VALIDAS = set(CATEGORIAS_STRIDE)  # {"S", "T", "R", "I", "D", "E"}


def test_listar_componentes_retorna_todas_as_chaves() -> None:
    """`listar_componentes` deve refletir exatamente as chaves da base."""
    componentes = listar_componentes()
    assert set(componentes) == set(KNOWLEDGE_BASE)
    assert len(componentes) == 11  # 11 componentes do MVP


def test_obter_ameacas_componente_conhecido() -> None:
    """Um componente conhecido retorna nome de exibição e lista de ameaças."""
    info = obter_ameacas("api_gateway")
    assert info is not None
    assert info["nome_exibicao"] == "API Gateway"
    assert len(info["ameacas"]) > 0


def test_obter_ameacas_componente_desconhecido_retorna_none() -> None:
    """Componente fora da base retorna None (não levanta exceção)."""
    assert obter_ameacas("componente_inexistente") is None


def test_mapear_componentes_filtra_desconhecidos() -> None:
    """Componentes não mapeados são silenciosamente ignorados."""
    resultado = mapear_componentes(["api_gateway", "banco_dados", "inexistente"])
    assert set(resultado) == {"api_gateway", "banco_dados"}


def test_mapear_componentes_lista_vazia() -> None:
    """Lista vazia produz dicionário vazio."""
    assert mapear_componentes([]) == {}


def test_estrutura_de_todos_os_componentes() -> None:
    """Todo componente deve ter nome de exibição e ameaças bem formadas.

    Este teste protege o contrato que `report_generator` consome: cada ameaça
    precisa de uma categoria STRIDE válida, uma descrição e ao menos uma
    contramedida.
    """
    for chave, info in KNOWLEDGE_BASE.items():
        assert info["nome_exibicao"], f"{chave} sem nome_exibicao"
        assert info["ameacas"], f"{chave} sem ameaças"
        for ameaca in info["ameacas"]:
            assert ameaca["categoria"] in CATEGORIAS_VALIDAS, (
                f"{chave}: categoria inválida {ameaca['categoria']!r}"
            )
            assert ameaca["descricao"].strip(), f"{chave}: descrição vazia"
            assert ameaca["contramedidas"], f"{chave}: sem contramedidas"
