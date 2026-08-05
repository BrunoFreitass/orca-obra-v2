"""
OrçaObra AI — Limpador de Conflitos de Merge
Remove marcadores de conflito do Git (<<<<<<< HEAD, =======, >>>>>>>)
que ficaram espalhados nos arquivos apos o git pull.

Mantem a versao LOCAL (entre <<<<<<< HEAD e =======), que e o codigo
real do projeto. Descarta a versao do remote (entre ======= e >>>>>>>),
que geralmente e vazia ou so tinha o README inicial.

Execute na pasta raiz do projeto (onde esta app.py).
"""
import os
import re

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("❌ ERRO: execute na pasta raiz do projeto (onde esta app.py)")
    print(f"   Pasta atual: {RAIZ}")
    exit(1)

# Padrao para detectar blocos de conflito:
# <<<<<<< HEAD
# ... conteudo local ...
# =======
# ... conteudo remoto ...
# >>>>>>> hash
PADRAO_CONFLITO = re.compile(
    r'^<<<<<<< HEAD\n.*?^=======\n.*?^>>>>>>> [a-f0-9]+\n?',
    re.MULTILINE | re.DOTALL
)

# Padrao mais simples: so remove as linhas de marcador, mantendo tudo entre elas
# Mas isso deixaria lixo. Melhor: extrair so o conteudo LOCAL.

def limpar_conflitos(caminho):
    """Remove blocos de conflito de merge, mantendo a versao LOCAL."""
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    if "<<<<<<< HEAD" not in conteudo:
        return False  # nao tinha conflito

    linhas = conteudo.splitlines()
    resultado = []
    dentro_conflito = False
    pegar_local = True  # comeca pegando o lado local
    i = 0

    while i < len(linhas):
        linha = linhas[i]

        if linha.startswith("<<<<<<< HEAD"):
            dentro_conflito = True
            pegar_local = True
            i += 1
            continue

        if linha.startswith("======="):
            pegar_local = False
            i += 1
            continue

        if linha.startswith(">>>>>>>"):
            dentro_conflito = False
            pegar_local = True
            i += 1
            continue

        if dentro_conflito and pegar_local:
            resultado.append(linha)
        elif not dentro_conflito:
            resultado.append(linha)

        i += 1

    # Remove linhas em branco extras no final
    while resultado and resultado[-1].strip() == "":
        resultado.pop()

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(resultado))
        if resultado:
            f.write("\n")

    return True


arquivos_afetados = []
for raiz, dirs, arquivos in os.walk(RAIZ):
    # Pula pastas de ambiente virtual e cache
    dirs[:] = [d for d in dirs if d not in (".venv", "venv", "__pycache__", ".git", ".pytest_cache")]
    for nome in arquivos:
        if nome.endswith(".py"):
            caminho = os.path.join(raiz, nome)
            if limpar_conflitos(caminho):
                rel = os.path.relpath(caminho, RAIZ)
                arquivos_afetados.append(rel)

print("=" * 60)
print("  ORÇAOBRA AI — LIMPADOR DE CONFLITOS DE MERGE")
print("=" * 60)
print()

if arquivos_afetados:
    print(f"✅ {len(arquivos_afetados)} arquivo(s) limpo(s):")
    for arq in arquivos_afetados:
        print(f"   • {arq}")
else:
    print("ℹ️  Nenhum arquivo com conflito encontrado.")

print()
print("Próximo passo: rode os testes novamente")
print("  pytest tests/ -v")
print()
