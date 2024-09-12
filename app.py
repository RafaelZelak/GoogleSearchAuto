import aiohttp
import asyncio
from bs4 import BeautifulSoup
import random
import re
from tqdm.asyncio import tqdm_asyncio
from urllib.parse import urljoin
import phonenumbers
import requests
from collections import Counter
import json

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

    # Expressão regular para capturar redes sociais
    social_media_regex = r'(facebook|instagram|linkedin|twitter)\.com/[^\s\'"<>]+'

    try:
        # Verificar se o próprio URL é uma rede social
        social_media_profiles = []
        if re.search(social_media_regex, url):
            social_media_profiles.append(url)

        async with session.get(url, headers=headers) as response:
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")

            # Expressões regulares para capturar email, telefone e outros dados
            email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            phone_regex = r'\(?\+?[0-9]{1,4}\)?[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,9}'
            address_regex = r'\d+\s[\w\s.-]+,\s?[A-Za-z\s]+,\s?[A-Za-z\s]+,\s?\d{5}(-\d{4})?'

            # Extraindo emails, telefones, endereços e redes sociais do conteúdo da página
            emails = re.findall(email_regex, soup.text)
            phones = re.findall(phone_regex, soup.text)
            addresses = re.findall(address_regex, soup.text)
            social_media_profiles += re.findall(social_media_regex, soup.text)  # Adicionar redes sociais do conteúdo da página

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
                    '/contato', '/fale-conosco', '/contatos', '/suporte', '/informacoes-de-contato', '/email', '/telefone',
                    '/contato-e-mail', '/contato-telefone', '/contact', '/contact-us', '/contact-info', '/email-address',
                    '/phone-number', '/contact-details', '/customer-support', '/support-center', '/entre-em-contato',
                    '/fale-conosco-aqui', '/contato-para-suporte', '/enviar-mensagem', '/atendimento', '/informacoes-contato',
                    '/contato-comercial', '/contato-para-empresas', '/contato-para-clientes', '/suporte-tecnico',
                    '/assessoria', '/contato-empresa', '/contact-support', '/customer-service', '/help', '/contact-form',
                    '/contact-us-now', '/contact-us-page', '/connect-with-us', '/message-us', '/social', '/redes-sociais',
                    '/facebook', '/twitter', '/instagram', '/linkedin', '/youtube', '/social-media', '/follow-us'
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

# Função para formatar o horário de funcionamento
import re

# Função para formatar o horário de funcionamento
def formatar_horario_funcionamento(horarios_raw):
    if isinstance(horarios_raw, str):
        # Remover partes desnecessárias e formatar corretamente
        horarios_limp = re.sub(r"Horário de funcionamento: Aberto ⋅ ", "", horarios_raw)
        horarios_limp = re.sub(r"Sugerir novos horários.*$", "", horarios_limp)

        # Adicionar quebras de linha entre os dias da semana
        horarios_limp = re.sub(r'(segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|domingo)', r'\n\1', horarios_limp)

        # Remover prefixos como "00"
        horarios_limp = re.sub(r'00(\w+-feira)', r'\1', horarios_limp)

        # Separar "Fechado" corretamente dos dias da semana
        horarios_limp = re.sub(r'(Fechado)(\w+-feira)', r'\1\n\2', horarios_limp)

        # Dividir a string em linhas e processar cada linha
        linhas = horarios_limp.strip().split("\n")
        horarios_dict = {}

        for linha in linhas:
            # Encontrar dias da semana e horários usando regex
            match = re.match(r'(segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|domingo)\s*(\d{2}:\d{2}–\d{2}:\d{2}|Fechado)', linha)
            if match:
                dia, horario = match.groups()
                horarios_dict[dia] = horario

        return horarios_dict

    elif isinstance(horarios_raw, dict):
        # Se os horários já estiverem no formato de dicionário
        return horarios_raw

    return None  # Retorna None se o formato for desconhecido

# Função para consolidar as informações coletadas
def consolidar_informacoes(knowledge_data, contact_infos):
    # Inicializar os contadores para os dados
    emails_counter = Counter()
    phones_counter = Counter()
    addresses_counter = Counter()
    social_media_profiles = []

    # Preencher os contadores com as informações extraídas
    for contact_info in contact_infos:
        if 'emails' in contact_info:
            emails_counter.update(contact_info['emails'])
        if 'phones' in contact_info:
            phones_counter.update(contact_info['phones'])
        if 'addresses' in contact_info:
            addresses_counter.update(contact_info['addresses'])
        if 'social_media_profiles' in contact_info:
            social_media_profiles.extend(contact_info['social_media_profiles'])  # Redes sociais

    # Escolher os valores mais comuns ou usar os do Knowledge Graph
    email_final = knowledge_data.get('email') or (emails_counter.most_common(1)[0][0] if emails_counter else None)
    phone_final = knowledge_data.get('phone') or (phones_counter.most_common(1)[0][0] if phones_counter else None)
    address_final = knowledge_data.get('address') or (addresses_counter.most_common(1)[0][0] if addresses_counter else None)

    # Adicionar redes sociais do Knowledge Graph, se existirem
    if knowledge_data.get('social_media_profiles'):
        social_media_profiles.extend(knowledge_data['social_media_profiles'])

    # Remover duplicatas das redes sociais
    social_media_profiles = list(set(social_media_profiles))

    # Formatar o horário de funcionamento
    hours_final = None
    if 'hours' in knowledge_data:
        hours_final = formatar_horario_funcionamento(knowledge_data['hours'])

    # Retornar as informações consolidadas
    return {
        'email': email_final,
        'phone': phone_final,
        'address': address_final,
        'social_media_profiles': social_media_profiles,
        'hours': hours_final
    }


# Função principal para executar as buscas e raspagem de dados
async def main():
    query = "Setup Tecnologia"

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

            # Consolidação das informações
            knowledge_graph_data = None
            for resultado in resultados:
                if 'knowledge_data' in resultado:
                    knowledge_graph_data = resultado['knowledge_data']
                    break

            # Organizar o horário de funcionamento no próprio knowledge_graph
            if knowledge_graph_data and 'hours' in knowledge_graph_data:
                knowledge_graph_data['hours'] = formatar_horario_funcionamento(knowledge_graph_data['hours'])

            informacoes_consolidadas = consolidar_informacoes(knowledge_graph_data or {}, contact_infos)

            # Converter o resultado consolidado para JSON
            resultado_json = {
                "knowledge_graph": knowledge_graph_data,
                "consolidated_contact_info": informacoes_consolidadas
            }

            # Exibir o JSON formatado
            print(json.dumps(resultado_json, indent=4, ensure_ascii=False))
        else:
            print("Nenhum resultado encontrado.")

# Executar a função principal
if __name__ == "__main__":
    asyncio.run(main())