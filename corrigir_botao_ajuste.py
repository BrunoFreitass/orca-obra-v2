
import os

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("ERRO: execute na pasta raiz do projeto (onde esta app.py)")
    exit(1)

app_path = os.path.join(RAIZ, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

antigo = '                if st.button(f"⚡ Ajustar para {sugestao_parede} m", key="btn_ajuste_parede"):\n                    st.session_state["dados_extraidos"]["metros_parede"] = sugestao_parede\n                    st.rerun()'

novo = '                if st.button(f"⚡ Ajustar para {sugestao_parede} m", key="btn_ajuste_parede"):\n                    st.session_state["dados_extraidos"]["metros_parede"] = sugestao_parede\n                    st.session_state["input_metros_parede"] = float(sugestao_parede)\n                    st.rerun()'

if antigo in conteudo:
    conteudo = conteudo.replace(antigo, novo)
    print("✅ app.py corrigido: botao de ajuste agora atualiza o widget tambem")
else:
    print("⚠️  Bloco do botao nao encontrado exatamente como esperado.")
    print("   Verifique se o app.py esta com a versao mais recente.")
    exit(1)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print()
print("Rode o app novamente:")
print("  streamlit run app.py")
print()
