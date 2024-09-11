import aiohttp
import asyncio
from bs4 import BeautifulSoup
import random
import re
from tqdm.asyncio import tqdm_asyncio
from urllib.parse import urljoin
import phonenumbers
import requests

# Função para capturar informações do Knowledge Graph
async def extract_knowledge_graph(soup):
    knowledge_data = {}

    # Capturando o título (nome do lugar)
    title_elem = soup.find('div', {'data-attrid': 'title'})
    if title_elem:
        knowledge_data['title'] = title_elem.get_text()

    # Capturando a nota
    rating_elem = soup.find('span', {'class': 'Aq14fc'})
    if rating_elem:
        knowledge_data['rating'] = rating_elem.get_text()

    # Capturando o número de avaliações
    review_count_elem = soup.find('span', {'class': 'hqzQac'})
    if review_count_elem:
        knowledge_data['review_count'] = review_count_elem.get_text()

    # Capturando a faixa de preço
    price_range_elem = soup.find('span', {'class': 'rRfnje'})
    if price_range_elem:
        knowledge_data['price_range'] = price_range_elem.get_text()

    # Capturando a descrição
    description_elem = soup.find('div', {'data-attrid': 'kc:/location/location:short_description'})
    if description_elem:
        knowledge_data['description'] = description_elem.get_text()

    # Capturando o endereço
    address_elem = soup.find('div', {'data-attrid': 'kc:/location/location:address'})
    if address_elem:
        knowledge_data['address'] = address_elem.get_text()

    # Capturando o telefone usando um seletor mais preciso
    phone_elem = soup.find('span', string=re.compile(r'^\(?\+?[0-9]{1,4}\)?[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,9}$'))
    if phone_elem:
        knowledge_data['phone'] = phone_elem.get_text()

    # Capturando o horário de funcionamento
    hours_elem = soup.find('div', {'data-attrid': 'kc:/location/location:hours'})
    if hours_elem:
        knowledge_data['hours'] = hours_elem.get_text()

    return knowledge_data

# Função para validar e formatar números de telefone
def validar_e_formatar_telefone(numero, regioes='BR'):
    try:
        numero_parseado = phonenumbers.parse(numero, regioes)
        if phonenumbers.is_valid_number(numero_parseado):
            formato_internacional = phonenumbers.format_number(numero_parseado, phonenumbers.PhoneNumberFormat.E164)
            formato_nacional = phonenumbers.format_number(numero_parseado, phonenumbers.PhoneNumberFormat.NATIONAL)
            return formato_internacional, formato_nacional
        else:
            return None, "Número inválido"
    except phonenumbers.NumberParseException as e:
        return None, str(e)

# Função para consultar e validar CEP
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

# Função assíncrona para realizar a busca no Google
async def google_search(query, session):
    google_search_url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ])
    }

    async with session.get(google_search_url, headers=headers) as response:
        text = await response.text()
        soup = BeautifulSoup(text, "html.parser")

        results = []

        # Captura do Knowledge Graph
        knowledge_graph_data = await extract_knowledge_graph(soup)
        if knowledge_graph_data:
            results.append({'title': knowledge_graph_data.get('title', 'No title'), 'link': 'Info do Knowledge Graph', 'knowledge_data': knowledge_graph_data})
        else:
            print("\nKnowledge Graph não encontrado.")

        # Extrair links dos resultados normais de busca
        for g in soup.find_all('div', class_='g'):
            title = g.find('h3').text if g.find('h3') else "No title"
            a_tag = g.find('a')
            link = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
            snippet = g.find('span', class_='aCOpRe').text if g.find('span', class_='aCOpRe') else "No snippet"
            results.append({'title': title, 'link': link, 'snippet': snippet})

        return results

# Função assíncrona para extrair informações de contato de uma página
async def scrape_contact_info(url, session, deep_scan=False):
    if not url:
        return {'error': 'No URL provided'}

    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ])
    }

    try:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")

            # Expressões regulares para capturar email, telefone e outros dados
            email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            phone_regex = r'\(?\+?[0-9]{1,4}\)?[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,9}'
            address_regex = r'\d+\s[\w\s.-]+,\s?[A-Za-z\s]+,\s?[A-Za-z\s]+,\s?\d{5}(-\d{4})?'
            social_media_regex = r'(facebook|instagram|linkedin|twitter)\.com/[^\s\'"<>]+'

            # Extraindo emails, telefones, endereços e redes sociais
            emails = re.findall(email_regex, soup.text)
            phones = re.findall(phone_regex, soup.text)
            addresses = re.findall(address_regex, soup.text)
            social_media_profiles = re.findall(social_media_regex, soup.text)

            # Remover duplicatas e validar números
            emails = list(set(emails))
            valid_phones = []
            for phone in set(phones):
                internacional, nacional = validar_e_formatar_telefone(phone)
                if internacional:
                    valid_phones.append(internacional)
            valid_phones = list(set(valid_phones))

            addresses = list(set(addresses))
            social_media_profiles = list(set(social_media_profiles))

            contact_info = {
                'emails': emails,
                'phones': valid_phones,
                'addresses': addresses,
                'social_media_profiles': social_media_profiles
            }

            # Realizar varredura profunda se habilitado
            if deep_scan and not any([emails, valid_phones, addresses, social_media_profiles]):
                possible_paths = [
                    '/contato',
                    '/fale-conosco',
                    '/contatos',
                    '/suporte',
                    '/informacoes-de-contato',
                    '/email',
                    '/telefone',
                    '/contato-e-mail',
                    '/contato-telefone',
                    '/contact',
                    '/contact-us',
                    '/contact-info',
                    '/email-address',
                    '/phone-number',
                    '/contact-details',
                    '/customer-support',
                    '/support-center',
                    '/entre-em-contato',
                    '/fale-conosco-aqui',
                    '/contato-para-suporte',
                    '/enviar-mensagem',
                    '/atendimento',
                    '/informacoes-contato',
                    '/contato-comercial',
                    '/contato-para-empresas',
                    '/contato-para-clientes',
                    '/suporte-tecnico',
                    '/assessoria',
                    '/contato-empresa',
                    '/contact-support',
                    '/customer-service',
                    '/help',
                    '/contact-form',
                    '/contact-us-now',
                    '/contact-us-page',
                    '/connect-with-us',
                    '/message-us',
                    '/social',
                    '/redes-sociais',
                    '/facebook',
                    '/twitter',
                    '/instagram',
                    '/linkedin',
                    '/youtube',
                    '/social-media',
                    '/follow-us'
                ]
                for path in possible_paths:
                    new_url = urljoin(url, path)
                    async with session.get(new_url, headers=headers) as sub_response:
                        if sub_response.status == 200:
                            sub_text = await sub_response.text()
                            sub_soup = BeautifulSoup(sub_text, "html.parser")

                            # Extraindo novamente
                            emails += re.findall(email_regex, sub_soup.text)
                            for phone in re.findall(phone_regex, sub_soup.text):
                                internacional, nacional = validar_e_formatar_telefone(phone)
                                if internacional:
                                    valid_phones.append(internacional)
                            addresses += re.findall(address_regex, sub_soup.text)
                            social_media_profiles += re.findall(social_media_regex, sub_soup.text)

                            # Remover duplicatas novamente
                            emails = list(set(emails))
                            valid_phones = list(set(valid_phones))
                            addresses = list(set(addresses))
                            social_media_profiles = list(set(social_media_profiles))

                            # Para se encontrar dados
                            if any([emails, valid_phones, addresses, social_media_profiles]):
                                break

            return contact_info
    except Exception as e:
        return {'error': str(e)}

# Função principal para executar as buscas e raspagem de dados
async def main():
    query = "buda lanches"

    async with aiohttp.ClientSession() as session:
        resultados = await google_search(query, session)

        tasks = []
        for resultado in resultados:
            link = resultado.get('link', '')
            if link and "http" in link:
                # Habilitar deep_scan conforme a necessidade
                tasks.append(scrape_contact_info(link, session, deep_scan=True))

        # Somente tenta raspar se houver tarefas
        if tasks:
            # Usar tqdm para barra de progresso
            contact_infos = await tqdm_asyncio.gather(*tasks, total=len(tasks))

            # Exibição dos resultados
            print("\nResultados da Busca:\n")
            for i, resultado in enumerate(resultados):
                # Verificar e imprimir informações do Knowledge Graph
                if 'knowledge_data' in resultado:
                    knowledge_data = resultado['knowledge_data']
                    print("\nInformações do Knowledge Graph:")
                    for key, value in knowledge_data.items():
                        print(f"{key.capitalize()}: {value}")
                    print()  # Adicionar uma linha em branco para separar as seções

                print(f"Resultado {i + 1}:")
                print(f"Link: {resultado.get('link', '')}")

                # Verificar se o índice existe em contact_infos
                if i < len(contact_infos):
                    print(f"Informações de Contato: {contact_infos[i]}")
                else:
                    print("Informações de Contato: Não disponível")

                print()
        else:
            print("Nenhum resultado encontrado.")

# Executar a função principal
if __name__ == "__main__":
    asyncio.run(main())