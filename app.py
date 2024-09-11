import aiohttp
import asyncio
from bs4 import BeautifulSoup
import random
import re
from tqdm.asyncio import tqdm_asyncio

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

        # Tentar capturar informações do Knowledge Graph (caixa lateral do Google)
        knowledge_graph = soup.find('div', {'data-attrid': 'kc:/local:onebox'})
        if knowledge_graph:
            title_elem = knowledge_graph.find('span', {'class': 'BNeawe tAd8D AP7Wnd'})
            contact_elem = knowledge_graph.find('span', {'class': 'BNeawe s3v9rd AP7Wnd'})
            business_info = {
                'title': title_elem.text if title_elem else "No title",
                'contact': contact_elem.text if contact_elem else "No contact info"
            }
            results.append(business_info)
        else:
            print("Knowledge Graph não encontrado.")

        # Extrair links dos resultados normais de busca
        for g in soup.find_all('div', class_='g'):
            title = g.find('h3').text if g.find('h3') else "No title"
            a_tag = g.find('a')
            link = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
            snippet = g.find('span', class_='aCOpRe').text if g.find('span', class_='aCOpRe') else "No snippet"
            results.append({'title': title, 'link': link, 'snippet': snippet})

        return results

# Função assíncrona para extrair informações de contato de uma página
async def scrape_contact_info(url, session):
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
            email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            phone_regex = r'\(?\+?[0-9]{1,4}?\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}'
            address_regex = r'[\w\s,-]+,\s?[A-Za-z]{2,}\s?\d{5}-?\d{3}'
            social_media_regex = r'(facebook|instagram|linkedin|twitter)\.com/[^\'"\s]+'

            # Extraindo emails, telefones, endereços e redes sociais
            emails = re.findall(email_regex, soup.text)
            phones = re.findall(phone_regex, soup.text)
            addresses = re.findall(address_regex, soup.text)
            social_media_profiles = re.findall(social_media_regex, soup.text)

            # Remover duplicatas
            emails = list(set(emails))
            phones = list(set(phones))
            addresses = list(set(addresses))
            social_media_profiles = list(set(social_media_profiles))

            return {
                'emails': emails,
                'phones': phones,
                'addresses': addresses,
                'social_media_profiles': social_media_profiles
            }
    except Exception as e:
        return {'error': str(e)}

# Função principal para executar as buscas e raspagem de dados
async def main():
    query = "rentcars"

    async with aiohttp.ClientSession() as session:
        resultados = await google_search(query, session)

        tasks = []
        for resultado in resultados:
            link = resultado.get('link', '')
            if link and "http" in link:
                tasks.append(scrape_contact_info(link, session))

        # Somente tenta raspar se houver tarefas
        if tasks:
            # Usar tqdm para barra de progresso
            contact_infos = await tqdm_asyncio.gather(*tasks, total=len(tasks))

            # Verifica o tamanho de contact_infos para evitar erro de indexação
            for i, resultado in enumerate(resultados):
                if i < len(contact_infos):
                    contact_info = contact_infos[i]
                    print(f"Título: {resultado.get('title')}")
                    print(f"Link: {resultado.get('link', 'Info do Knowledge Graph')}")
                    print(f"Emails: {contact_info.get('emails', 'No emails found')}")
                    print(f"Phones: {contact_info.get('phones', 'No phones found')}")
                    print(f"Addresses: {contact_info.get('addresses', 'No addresses found')}")
                    print(f"Social Media Profiles: {contact_info.get('social_media_profiles', 'No profiles found')}")
                    print("-" * 60)
                else:
                    print(f"Título: {resultado.get('title')}")
                    print(f"Link: {resultado.get('link', 'No link')}")
                    print("Nenhuma informação de contato disponível.")
                    print("-" * 60)

# Rodando o código
asyncio.run(main())
