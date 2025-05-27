import asyncio
from crawl4ai import AsyncWebCrawler
from agno.agent import Agent
from agno.models.mistral import MistralChat
from pydantic import BaseModel
from typing import List

class WebPageData(BaseModel):
    title: str
    main_content: str
    headlines: List[str]
    page_type: str

def extract_webpage(url: str) -> WebPageData:
    """Version ultra-simple et robuste."""
    
    async def get_content():
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url, word_count_threshold=1)
            return result.markdown if result.success else ""
    
    # Récupération du contenu
    content = asyncio.run(get_content())
    print(f"✅ {len(content)} caractères extraits")
    
    # Agent simple
    agent = Agent(
        model=MistralChat(id="mistral-large-2411"),
        instructions="Extract the title, main content, headlines, and determine page type from this webpage.",
        response_model=WebPageData,
    )
    
    # Structuration
    result = agent.run(f"Analyze this webpage from {url}:\n\n{content[:10000]}")
    return result.content

# Test ultra-simple
if __name__ == "__main__":
    result = extract_webpage("https://www.lemonde.fr/") #"https://www.nbcnews.com/business")
    print("\n🎯 RÉSULTAT FINAL:")
    print(f"Titre: {result.title}")
    print(f"Type: {result.page_type}")
    print(f"Headlines trouvées: {len(result.headlines)}")
    print(f"Contenu: {len(result.main_content)} caractères")