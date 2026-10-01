"""Leitura de uploads com limite de tamanho, compartilhada pelos routers."""
from fastapi import HTTPException, UploadFile

_TAMANHO_BLOCO = 1024 * 1024  # 1 MB


def erro_amigavel(status_code: int, mensagem: str) -> HTTPException:
    """Mesmo formato de detail usado por /api/extracao, que o frontend já sabe ler."""
    return HTTPException(status_code=status_code, detail={"mensagem_amigavel": mensagem})


async def ler_com_limite(arquivo: UploadFile, limite_bytes: int) -> bytes:
    """Lê o upload em blocos e aborta (413) assim que passar do limite,
    sem carregar o restante do arquivo na memória."""
    partes = []
    total = 0
    while bloco := await arquivo.read(_TAMANHO_BLOCO):
        total += len(bloco)
        if total > limite_bytes:
            raise erro_amigavel(
                413,
                f"Arquivo muito grande. O tamanho máximo permitido é {limite_bytes // (1024 * 1024)}MB.",
            )
        partes.append(bloco)
    return b"".join(partes)
