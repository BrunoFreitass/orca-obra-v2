"""
OrçaObra AI — Remove duplicação do app.py
==========================================
O merge anterior deixou o arquivo app.py completamente duplicado
(versão antiga + versão nova, uma em cima da outra).

Este script detecta a segunda ocorrência de 'import streamlit as st'
e remove tudo a partir dela, mantendo apenas a primeira metade.

Execute na pasta raiz do projeto.
"""
import os

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("❌ ERRO: execute na pasta raiz do projeto (onde está app.py)")
    exit(1)

app_path = os.path.join(RAIZ, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Encontra a segunda ocorrência de "import streamlit as st"
primeira = conteudo.find("import streamlit as st")
if primeira == -1:
    print("❌ Não encontrou 'import streamlit as st' no arquivo")
    exit(1)

segunda = conteudo.find("import streamlit as st", primeira + 1)
if segunda == -1:
    print("ℹ️  Não detectou duplicação — apenas uma ocorrência de 'import streamlit as st'")
    exit(0)

# Corta tudo a partir da segunda ocorrência
conteudo_limpo = conteudo[:segunda]

# Remove linhas em branco extras no final
conteudo_limpo = conteudo_limpo.rstrip() + "\n"

with open(app_path, "w", encoding="utf-8") as f:
    f.write(conteudo_limpo)

print("=" * 60)
print("  ✅ DUPLICAÇÃO REMOVIDA!")
print("=" * 60)
print()
print(f"O arquivo tinha {len(conteudo)} caracteres.")
print(f"Agora tem {len(conteudo_limpo)} caracteres.")
print()
print("Próximo passo: rode o app")
print("  streamlit run app.py")
print()
