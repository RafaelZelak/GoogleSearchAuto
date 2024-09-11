import requests

def consultar_cep(cep):
    url = f'https://viacep.com.br/ws/{cep}/json/'
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        if 'erro' in dados:
            return False, "CEP não encontrado"
        return True, dados
    else:
        return False, "Erro ao consultar CEP"

cep = '80730-480'  # Exemplo de CEP
valido, resultado = consultar_cep(cep)
if valido:
    print(f"O CEP {cep} é válido.")
    print(f"Endereço: {resultado['logradouro']}, {resultado['bairro']}, {resultado['localidade']}-{resultado['uf']}")
else:
    print(f"Validação do CEP falhou: {resultado}")
