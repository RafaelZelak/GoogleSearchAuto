import phonenumbers
from phonenumbers import NumberParseException, is_valid_number, format_number, PhoneNumberFormat

def validar_e_formatar(numero, regioes='BR'):
    try:
        numero_parseado = phonenumbers.parse(numero, regioes)

        if is_valid_number(numero_parseado):
            formato_internacional = format_number(numero_parseado, PhoneNumberFormat.E164)
            formato_nacional = format_number(numero_parseado, PhoneNumberFormat.NATIONAL)
            return formato_internacional, formato_nacional
        else:
            return None, "Número inválido"
    except NumberParseException as e:
        return None, str(e)

numero_telefone = "55(41)99795-9399"
internacional, nacional = validar_e_formatar(numero_telefone)
if internacional:
    print(f"Número formatado internacionalmente: {internacional}")
    print(f"Número formatado nacionalmente: {nacional}")
else:
    print(f"Erro: {nacional}")
