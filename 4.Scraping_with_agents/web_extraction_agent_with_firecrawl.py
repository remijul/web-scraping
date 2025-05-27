from textwrap import dedent
from typing import Dict, List, Optional, Any, Union

from agno.agent import Agent
from agno.models.mistral import MistralChat
from agno.tools.firecrawl import FirecrawlTools
from pydantic import BaseModel, Field
from rich.pretty import pprint
import json

from dotenv import load_dotenv
load_dotenv()

class ContentSection(BaseModel):
    heading: Optional[str] = Field(None, description="Section heading")
    content: str = Field(..., description="Section content text")

class PageInformation(BaseModel):
    """Modèle flexible pour gérer des structures complexes."""
    
    url: str = Field(..., description="URL of the page")
    title: str = Field(..., description="Title of the page")
    description: Optional[str] = Field(None, description="Meta description or summary of the page")
    features: Optional[List[str]] = Field(None, description="Key feature list")
    content_sections: Optional[List[ContentSection]] = Field(None, description="Main content sections of the page")
    links: Optional[Dict[str, str]] = Field(None, description="Important links found on the page with description")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Contact information if available")
    
    # Changement clé : metadata peut contenir n'importe quel type de données
    metadata: Optional[Dict[str, Any]] = Field(None, description="Important metadata from the page - can contain strings, lists, or objects")

# Étape 1 : Agent scraper (inchangé)
scraper_agent = Agent(
    model=MistralChat(id="mistral-large-2411"),
    tools=[FirecrawlTools(scrape=True, crawl=True)],
    instructions=dedent("""
        You are a web scraper. Your job is to scrape the provided URL and return the raw content.
        Use the firecrawl tool to get the webpage content and return it as clean text.
        Focus on getting all the important content from the page.
    """).strip(),
)

# Étape 2 : Agent structureur avec instructions plus précises
structure_agent = Agent(
    model=MistralChat(id="mistral-large-2411"),
    instructions=dedent("""
        You are an expert content analyzer. Take the provided webpage content and structure it 
        according to the specified format. Extract:
        
        1. Page title and description
        2. Key features as a list of strings
        3. Main content sections with headings
        4. Important links as key-value pairs
        5. Contact information if available
        6. Relevant metadata - this can include complex data structures like:
           - Lists of items
           - Nested objects for pricing, features, etc.
           - Timeline information
           - Any other structured data from the page
        
        Be thorough and accurate. The metadata field can contain complex nested structures.
    """).strip(),
    response_model=PageInformation,
)

def extract_page_info(url: str) -> PageInformation:
    """Fonction pour extraire les informations de page en deux étapes."""
    
    # Étape 1 : Scraper le contenu
    print("🔍 Étape 1 : Récupération du contenu...")
    raw_content = scraper_agent.run(f"Scrape all content from {url}")
    
    print("✅ Contenu récupéré, structuration en cours...")
    
    # Étape 2 : Structurer le contenu
    print("📊 Étape 2 : Structuration des données...")
    structured_data = structure_agent.run(
        f"Structure this webpage content from {url}:\n\n{raw_content.content}"
    )
    
    return structured_data.content

# Test avec gestion d'erreur améliorée
try:
    #result = extract_page_info("https://www.agno.com")
    result = extract_page_info("https://vivatechnology.com/get-your-pass?ca=FPR887Y6&utm_source=google&utm_medium=cpc&utm_campaign=sea_campaign_brand_FR&esl-k=GOOGLEADS|ng|c733737405817|mp|kvivatech%202025|p|t|dc|a173107040577|g22264576927&gad_source=1&gad_campaignid=22264576927&gbraid=0AAAAADMaCLbO7B4nyTklr7j1OQUMNO6Hc&gclid=Cj0KCQjwotDBBhCQARIsAG5pinNYzYtw7nydQuxoFMgh4X-Jwov0ROjXldn4UbUCmsVf1VlUutaUG4oaAvbwEALw_wcB")
    #result = extract_page_info("https://www.lemonde.fr/")
    print("\n🎉 Extraction réussie !")
    pprint(result)
    
    # Affichage plus lisible des métadonnées complexes
    if result.metadata:
        print("\n📋 Métadonnées détaillées :")
        for key, value in result.metadata.items():
            if isinstance(value, (dict, list)):
                print(f"  {key}:")
                pprint(value, indent_guides=False)
            else:
                print(f"  {key}: {value}")
                
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()