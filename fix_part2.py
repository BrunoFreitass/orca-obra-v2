from pathlib import Path

# 1. app.py - remove noqa: BLE001
p = Path("app.py")
p.write_text(p.read_text(encoding="utf-8").replace(
    "except (ValueError, KeyError, RuntimeError) as e:  # noqa: BLE001",
    "except (ValueError, KeyError, RuntimeError) as e:"
), encoding="utf-8")
print("✅ app.py")

# 2. proposta_pdf.py - remove noqa: BLE001 e noqa: S110
p = Path("core/proposta_pdf.py")
txt = p.read_text(encoding="utf-8")
txt = txt.replace("except (OSError, ValueError):  # noqa: BLE001", "except (OSError, ValueError):")
txt = txt.replace("pass  # noqa: S110", "pass")
p.write_text(txt, encoding="utf-8")
print("✅ core/proposta_pdf.py")

# 3. test_tabela_precos.py - reverte _avisos para avisos onde é usado depois
p = Path("tests/test_tabela_precos.py")
txt = p.read_text(encoding="utf-8")
# Reverte as 3 ocorrências que usam avisos depois
txt = txt.replace(
    "atualizados, _avisos = tp.importar_tabela_excel(str(caminho))\n        assert atualizados == {}\n        assert any(\"desconhecida\" in a for a in avisos)",
    "atualizados, avisos = tp.importar_tabela_excel(str(caminho))\n        assert atualizados == {}\n        assert any(\"desconhecida\" in a for a in avisos)"
)
txt = txt.replace(
    "atualizados, _avisos = tp.importar_tabela_excel(str(caminho))\n        assert atualizados == {}\n        assert any(\"não numérico\" in a for a in avisos)",
    "atualizados, avisos = tp.importar_tabela_excel(str(caminho))\n        assert atualizados == {}\n        assert any(\"não numérico\" in a for a in avisos)"
)
txt = txt.replace(
    "atualizados, _avisos = tp.importar_tabela_excel(str(caminho))\n        assert atualizados == {}\n        assert any(\"zero ou negativo\" in a for a in avisos)",
    "atualizados, avisos = tp.importar_tabela_excel(str(caminho))\n        assert atualizados == {}\n        assert any(\"zero ou negativo\" in a for a in avisos)"
)
p.write_text(txt, encoding="utf-8")
print("✅ tests/test_tabela_precos.py")

# 4. Deleta fix_lint.py
Path("fix_lint.py").unlink(missing_ok=True)
print("✅ fix_lint.py deletado")

print("\n🎉 Pronto! Rode: python -m ruff check .")