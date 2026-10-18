from utils.pix import gerar_payload_pix

def test_gerar_pix():
    payload = gerar_payload_pix(
        chave="12345678909",
        nome="BRAVO STUDIO",
        cidade="SAO PAULO",
        valor=49.90,
        identificador="BRAVO-TST1234"
    )
    assert payload is not None
    assert "BRAVO STUDIO" in payload
    assert "SAO PAULO" in payload
    print("✅ Teste do gerador Pix passou com sucesso!")

if __name__ == "__main__":
    test_gerar_pix()