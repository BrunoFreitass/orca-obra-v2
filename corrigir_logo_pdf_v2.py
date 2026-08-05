"""
OrçaObra AI — Correção: adiciona 'import os' em proposta_pdf.py
"""
import os

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("❌ ERRO: execute na pasta raiz do projeto (onde está app.py)")
    exit(1)

pdf_path = os.path.join(RAIZ, "core", "proposta_pdf.py")
with open(pdf_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# 1. Adiciona 'import os' se ainda não existir
if "import os" not in conteudo:
    # Insere após a primeira linha de imports
    conteudo = "import os\n" + conteudo
    print("✅ Adicionado 'import os' no topo")

# 2. Garante que a condição do logo está correta
conteudo = conteudo.replace(
    'if caminho_logo:',
    'if caminho_logo and os.path.exists(caminho_logo):'
)

with open(pdf_path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("✅ core/proposta_pdf.py corrigido!")
print()
print("Rode os testes:")
print("  pytest tests/ -v")
