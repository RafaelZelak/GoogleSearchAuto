#TESTE PARA WEBSCRAP FACEBOOK

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

# Configurações do Selenium para o modo headless (sem abrir janelas)
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa em segundo plano
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Função para fechar o pop-up de login, se presente
def close_popup(driver):
    try:
        # Espera até que o botão de "Fechar" esteja presente e clica nele
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Fechar']"))
        )
        close_button.click()
        print("Pop-up de login fechado.")
    except Exception as e:
        print("Nenhum pop-up de login encontrado, ou erro ao tentar fechar:", e)

# Função para simular rolagem com 'Page Down'
def scroll_down(driver):
    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(5):  # Rola várias vezes com pequenas pausas
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(1)  # Espera mais para permitir o carregamento dos posts

# Função para capturar posts da página do Facebook com rolagem infinita até parar de carregar novos posts
def scrape_facebook(driver, max_scrolls=10):
    driver.get('https://www.facebook.com/setuptecnologia')  # Página específica do Facebook
    time.sleep(5)  # Tempo para carregar a página inicial

    # Fecha o pop-up de login, se presente
    close_popup(driver)

    facebook_data = []
    scrolls = 0
    last_post_count = 0

    while scrolls < max_scrolls:
        # Captura os elementos dos posts visíveis no momento
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-ad-preview="message"]')))
        posts = driver.find_elements(By.CSS_SELECTOR, 'div[data-ad-preview="message"]')

        # Adiciona o conteúdo dos posts à lista, verificando duplicatas
        for post in posts:
            content = post.text.strip()
            if content and content not in facebook_data:  # Evita duplicatas e conteúdos vazios
                facebook_data.append(content)

        # Se a contagem de posts não aumentar, encerra o loop
        if len(facebook_data) == last_post_count:
            print(f"Nenhum novo post encontrado após {scrolls + 1} rolagens. Encerrando.")
            break

        last_post_count = len(facebook_data)
        scrolls += 1

        # Simula a rolagem da página
        scroll_down(driver)
        print(f"Rolagem {scrolls}: {len(facebook_data)} posts capturados até agora.")

    return facebook_data

def main():
    driver = setup_driver()

    # Faz o scraping no Facebook
    print("Facebook Posts:")
    facebook_posts = scrape_facebook(driver, max_scrolls=2)  # Define o número máximo de rolagens
    for idx, post in enumerate(facebook_posts, 1):
        print(f"\nPost {idx}: {post}\n")

    driver.quit()

if __name__ == "__main__":
    main()
