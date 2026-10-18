def gerar_crc16(dados: str) -> str:
    """Calcula o CRC16-CCITT (XModem) em Python puro para o padrão Pix."""
    crc = 0xFFFF
    for char in dados:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
            
    return f"{crc:04X}"

def gerar_payload_pix(chave: str, nome: str, cidade: str, valor: float, identificador: str) -> str:
    """Gera a string Pix Copia e Cola (BR Code) oficial do Banco Central."""
    def campo(id_val: str, valor_val: str) -> str:
        tamanho = len(valor_val)
        return f"{id_val}{tamanho:02d}{valor_val}"

    # Formatação dos dados conforme padrão EMV
    gui = campo("00", "br.gov.bcb.pix")
    chave_field = campo("01", chave)
    merchant_account = campo("26", gui + chave_field)
    
    merchant_category_code = campo("52", "0000")
    transaction_currency = campo("53", "986") # BRL
    valor_str = f"{valor:.2f}"
    transaction_amount = campo("54", valor_str)
    country_code = campo("58", "BR")
    merchant_name = campo("59", nome[:25])
    merchant_city = campo("60", cidade[:15])
    
    additional_data = campo("62", campo("05", identificador))

    payload_sem_crc = (
        campo("00", "01") +
        merchant_account +
        merchant_category_code +
        transaction_currency +
        transaction_amount +
        country_code +
        merchant_name +
        merchant_city +
        additional_data
    )

    payload_para_crc = payload_sem_crc + "6304"
    crc = gerar_crc16(payload_para_crc)
    
    return payload_para_crc + crc
