import crcmod

def gerar_crc16(dados: str) -> str:
    # CRC16-CCITT padrão Pix (XModem / 0x1021)
    crc_func = crcmod.mkCrcFun(0x1021, rev=False, initCrc=0xFFFF, xorOut=0x0000)
    
    # Se o crcmod exigir o polinômio com o tamanho em bits explícito, usamos a função padrão do XModem:
    # Caso prefira garantir 100%, vamos usar o crcmod com polinomio nativo:
    # Adiciona o ID do CRC ('6304') ao final para o cálculo
    byte_array = (payload + "6304").encode("utf-8")
    crc = crc_func(byte_array)
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

    crc = gerar_crc16(payload_sem_crc)
    return payload_sem_crc + "6304" + crc
