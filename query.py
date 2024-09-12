import asyncio
from app import process_queries

async def main():
    # Lista de queries a serem processadas
    queries = [
        "Setup Tecnologia",
        "OpenAI",
        "Python Programação",
        "Google Cloud"
    ]

    # Executa o processamento das queries
    await process_queries(queries)

# Executa o script
if __name__ == "__main__":
    asyncio.run(main())
