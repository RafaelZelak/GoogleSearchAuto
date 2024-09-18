import asyncio
import json
from WebScrapSelenium import run_scraping_multiple
from WebScrapBeautifulSoup import run_beautifulsoup_scraping
from tqdm.asyncio import tqdm_asyncio
import time

async def combine_results(selenium_data, beautifulsoup_data):
    # Verificar se os dados do BeautifulSoup são válidos
    if beautifulsoup_data is None:
        bs_data = {}
    else:
        try:
            # Tentar carregar diretamente o beautifulsoup_data
            bs_data = json.loads(beautifulsoup_data)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Erro ao carregar BeautifulSoup data: {e}")
            bs_data = {}

    # Garantir que bs_data seja um dicionário e não None
    if not isinstance(bs_data, dict):
        bs_data = {}

    # Garantir que bs_data sempre tenha um dicionário para knowledge_graph e consolidated_contact_info
    knowledge_graph = bs_data.get("knowledge_graph", {})
    consolidated_contact_info = bs_data.get("consolidated_contact_info", {})

    # Garantir que knowledge_graph e consolidated_contact_info não sejam None
    if not isinstance(knowledge_graph, dict):
        knowledge_graph = {}
    if not isinstance(consolidated_contact_info, dict):
        consolidated_contact_info = {}

    # Combinar redes sociais de Selenium e BeautifulSoup e remover duplicatas
    combined_social_media = list(set(selenium_data.get("social_media_profiles", []) + consolidated_contact_info.get("social_media_profiles", [])))

    # Normalizar URLs de redes sociais, removendo trailing slashes ou subpaths desnecessários
    normalized_social_media = []
    for profile in combined_social_media:
        # Normaliza URLs removendo subpaths como "/img" ou barras extras
        profile = profile.split("?")[0]  # Remove parâmetros
        profile = profile.rstrip("/")  # Remove barras extras no final
        if profile not in normalized_social_media:
            normalized_social_media.append(profile)

    # Criar o dicionário consolidado usando os dados disponíveis
    consolidated_data = {
        "name": knowledge_graph.get("title", ""),
        "rating": knowledge_graph.get("rating", ""),
        "review_count": knowledge_graph.get("review_count", ""),
        "address": consolidated_contact_info.get("address", ""),
        "phone": selenium_data.get("phone", consolidated_contact_info.get("phone", "")),
        "email": selenium_data.get("email", consolidated_contact_info.get("email", [])),
        "hours": consolidated_contact_info.get("hours", {}),
        "social_media_profiles": normalized_social_media
    }

    # Exibir o resultado consolidado para depuração
    print(f"Consolidated Data: {json.dumps(consolidated_data, indent=4, ensure_ascii=False)}")

    return consolidated_data

async def main():
    queries = [
        "Setup Tecnologia",
        "openix solucoes belo horizonte"
    ]

    start_time = time.time()  # Registrar o tempo no início da execução

    # Rodar o scraping com Selenium e BeautifulSoup em paralelo para todas as queries
    selenium_task = asyncio.to_thread(run_scraping_multiple, queries)  # Converter função síncrona para assíncrona
    beautifulsoup_task = run_beautifulsoup_scraping(queries)  # Já é assíncrona

    # Exibir uma barra de progresso enquanto as tarefas estão em execução
    selenium_results, beautifulsoup_results = await tqdm_asyncio.gather(
        selenium_task,
        beautifulsoup_task,
        desc="Processando scraping",
        total=2
    )

    # Combinar os resultados de cada query
    for query, selenium_result in selenium_results.items():
        beautifulsoup_result = beautifulsoup_results[queries.index(query)]
        combined_result = await combine_results(selenium_result, beautifulsoup_result)

        # Exibir o resultado combinado para cada empresa
        print(f"\nResultado Combinado para '{query}':")

    # Calcular o tempo total de execução
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTempo total de execução: {total_time:.2f} segundos")

if __name__ == "__main__":
    asyncio.run(main())