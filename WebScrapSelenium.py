from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter
import time
import re

# Função para extrair informações de uma página da web
# Função para extrair informações de uma página da web
def extract_info_from_page(driver, current_url):
    data = {
        "email": "",
        "phone": "",
        "address": "",
        "social_media_profiles": []
    }

    # Verificar se estamos em uma rede social
    if any(platform in current_url for platform in ["linkedin.com", "facebook.com", "instagram.com", "twitter.com"]):
        # Se for rede social, define apenas o próprio URL como perfil de mídia social
        data["social_media_profiles"] = [current_url]
        return data

    # Capturando email
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", driver.page_source)
    if emails:
        data["email"] = emails[0]  # Pegando o primeiro email encontrado

    # Capturando telefone
    phones = re.findall(r'\(?\d{2}\)?\s?\d{4,5}-\d{4}', driver.page_source)
    if phones:
        data["phone"] = phones[0]  # Pegando o primeiro telefone encontrado

    # Tentativa de capturar endereço (simplificado, pode ser ajustado)
    address = re.search(r"\d{5}-\d{3}", driver.page_source)
    if address:
        data["address"] = address.group(0)  # Pegando o primeiro CEP encontrado

    # Capturando links de perfis de redes sociais
    social_links = re.findall(r'(https?://(?:www\.)?(?:facebook|instagram|linkedin|twitter)\.com/[^\s]+)', driver.page_source)
    data["social_media_profiles"] = social_links

    return data


# Configurando o driver do Selenium
def configure_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-blink-features=AutomationControlled")  # Evita detecção de automação
    options.add_argument("--disable-images")
    options.add_argument("--disable-plugins")
    options.add_argument("window-size=100x300")
    options.add_argument("--disable-javascript")  # Desabilita JavaScript, pode acelerar algumas páginas simples
    options.add_argument("--blink-settings=imagesEnabled=false")  # Reforço de desabilitação de imagens
    options.add_argument("--disable-background-timer-throttling")  # Melhora performance em execução headless
    options.add_argument("--disable-backgrounding-occluded-windows")  # Evita que páginas em background percam foco


    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Realizando a busca no Google
def search_google(driver, query):
    driver.get('https://www.google.com/')

    # Aceitar os cookies do Google, se necessário
    time.sleep(1)  # Aguardar o carregamento da página
    try:
        accept_button = driver.find_element(By.XPATH, '//*[@id="L2AGLb"]/div')
        accept_button.click()
    except:
        pass  # Caso o botão de aceitar cookies não apareça

    search_box = driver.find_element(By.NAME, 'q')
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    time.sleep(3)  # Aguardar a página de resultados carregar

# Adiciona função para rolar até o final da página para carregar mais resultados
def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Aguardar o carregamento de mais resultados

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # Verifica se mais resultados foram carregados
            break
        last_height = new_height

# Coletando URLs dos resultados
def get_google_results(driver):
    urls = []

    while True:
        time.sleep(2)  # Dar tempo para os resultados carregarem
        # Seleciona os links de resultados visíveis na página
        links = driver.find_elements(By.XPATH, '//a[@href]')
        page_urls = [link.get_attribute('href') for link in links if "google.com" not in link.get_attribute('href')]

        # Adiciona os novos URLs encontrados
        urls.extend(page_urls)

        # Tenta carregar mais resultados rolando a página
        scroll_to_bottom(driver)

        # Tenta avançar para a próxima página
        try:
            next_button = driver.find_element(By.ID, 'pnnext')  # Localiza o botão "Próxima Página"
            next_button.click()  # Clica no botão para ir para a próxima página de resultados
        except:
            break  # Se o botão "Próxima Página" não for encontrado, sair do loop

    return urls[:7]  # Limitar a coleta a 20 URLs (ajustável)

import re
from collections import Counter

# Função para validar emails com extensões válidas
def validate_email(email):
    valid_domains = ['.com', '.org', '.net', '.gov', '.edu', '.info', '.biz', '.name', '.tv', '.co', '.page', '.xyz', '.tech', '.store', '.br', '.com.br', '.org.br', '.net.br', '.gov.br', '.edu.br', '.mil.br', '.jus.br', '.soc.br', '.blog.br', '.eco.br', '.arq.br', '.tur.br']
  # Adicione outros se necessário
    domain_pattern = re.compile(r"\.[a-zA-Z]{2,}$")  # Verifica a parte final do domínio (e.g., .com, .org)

    domain = domain_pattern.search(email)
    if domain and any(email.endswith(ext) for ext in valid_domains):
        return True
    return False

# Função para verificar se o link é uma rede social válida da empresa
def is_company_social_link(link):
    # Verifica LinkedIn, Facebook e Instagram com padrão de empresa
    social_patterns = [
        r"https?://(www\.)?linkedin\.com/company/[^/]+",   # LinkedIn empresa
        r"https?://(www\.)?facebook\.com/(pages|company|[^/]+/?locale=[^/]+)",  # Facebook empresa
        r"https?://(www\.)?instagram\.com/[^/]+"  # Instagram empresa
    ]

    for pattern in social_patterns:
        if re.match(pattern, link):
            return True
    return False

# Função para limpar links de redes sociais
def clean_social_links(links):
    cleaned_links = []
    for link in links:
        # Remove caracteres extra indesejados
        link = re.sub(r'[\"<>\']', '', link)
        if link not in cleaned_links:
            cleaned_links.append(link)
    return cleaned_links

# Função para consolidar os resultados
# Consolida os resultados
def consolidate_results(results):
    final_data = {
        "email": [],
        "phone": "",
        "social_media_profiles": []
    }

    phones = []
    social_media_profiles = set()  # Usaremos um set para evitar duplicatas

    for result in results:
        info = result['info']

        if info['email'] and validate_email(info['email']):
            final_data['email'].append(info['email'])

        if info['phone']:
            phones.append(info['phone'])

        for profile in info['social_media_profiles']:
            if is_company_social_link(profile):
                social_media_profiles.add(profile)

    if phones:
        most_common_phone = Counter(phones).most_common(1)[0][0]
        final_data['phone'] = most_common_phone

    final_data['social_media_profiles'] = clean_social_links(list(social_media_profiles))

    return final_data

def run_scraping(query):
    driver = configure_driver()

    try:
        search_google(driver, query)
        urls = get_google_results(driver)

        results = []
        for url in urls:
            try:
                driver.get(url)
                time.sleep(3)
                info = extract_info_from_page(driver, url)
                results.append({"url": url, "info": info})
            except Exception as e:
                pass
        consolidated_info = consolidate_results(results)
        return consolidated_info

    finally:
        driver.quit()

# Função para rodar o scraping em múltiplas queries
def run_scraping_multiple(queries):
    all_results = {}
    for query in queries:
        all_results[query] = run_scraping(query)
    return all_results