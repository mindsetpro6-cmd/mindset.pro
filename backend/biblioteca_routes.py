from fastapi import APIRouter, HTTPException, Query
from backend.supabase_client import obter_cliente_supabase

router = APIRouter(
    prefix="/biblioteca",
    tags=["Biblioteca A Arca do Saber"],
)


def consultar_tabela(nome_tabela: str, limite: int = 50):
    """
    Consulta os registos ativos de uma tabela da Biblioteca.
    Acesso ao Supabase feito exclusivamente pelo backend.
    """
    try:
        cliente = obter_cliente_supabase()

        consulta = (
            cliente.table(nome_tabela)
            .select("*")
            .limit(limite)
        )

        if nome_tabela in (
            "biblioteca_materiais",
            "biblioteca_livros",
            "biblioteca_videos",
        ):
            consulta = consulta.eq("ativo", True)

        resposta = consulta.execute()

        return resposta.data or []

    except Exception as erro:
        print(f"Erro ao consultar {nome_tabela}: {erro}")

        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar a Biblioteca.",
        )


@router.get("/estado")
def estado_biblioteca():
    """Verifica se as quatro tabelas estão acessíveis."""

    tabelas = [
        "biblioteca_materiais",
        "biblioteca_livros",
        "biblioteca_videos",
        "biblioteca_jornal",
    ]

    try:
        cliente = obter_cliente_supabase()
        resultado = {}

        for tabela in tabelas:
            resposta = (
                cliente.table(tabela)
                .select("*", count="exact")
                .limit(0)
                .execute()
            )

            resultado[tabela] = resposta.count or 0

        return {
            "status": "ok",
            "biblioteca": "conectada",
            "tabelas": resultado,
        }

    except Exception as erro:
        print(f"Erro ao verificar Biblioteca: {erro}")

        raise HTTPException(
            status_code=503,
            detail="Não foi possível verificar as tabelas da Biblioteca.",
        )


@router.get("/materiais")
def listar_materiais(
    limite: int = Query(default=50, ge=1, le=100)
):
    """Lista materiais escolares ativos."""

    return {
        "materiais": consultar_tabela(
            "biblioteca_materiais", limite
        )
    }


@router.get("/livros")
def listar_livros(
    limite: int = Query(default=50, ge=1, le=100)
):
    """Lista livros ativos."""

    return {
        "livros": consultar_tabela(
            "biblioteca_livros", limite
        )
    }


@router.get("/videos")
def listar_videos(
    limite: int = Query(default=50, ge=1, le=100)
):
    """Lista vídeos ativos."""

    return {
        "videos": consultar_tabela(
            "biblioteca_videos", limite
        )
    }


@router.get("/jornal")
def listar_jornal(
    limite: int = Query(default=50, ge=1, le=100)
):
    """Lista apenas publicações do Jornal já publicadas."""

    registos = consultar_tabela(
        "biblioteca_jornal", limite
    )

    estados_publicados = {
        "publicado",
        "publicada",
        "published",
    }

    publicacoes = [
        registo
        for registo in registos
        if str(registo.get("estado", "")).strip().lower()
        in estados_publicados
    ]

    return {
        "publicacoes": publicacoes
    }
