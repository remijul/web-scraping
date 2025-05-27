from textwrap import dedent
from typing import Dict, List, Optional, Any
import asyncio
import time
from datetime import datetime

from agno.agent import Agent
from agno.models.mistral import MistralChat
from pydantic import BaseModel, Field
from rich.pretty import pprint
from rich.console import Console
from crawl4ai import AsyncWebCrawler

from dotenv import load_dotenv
load_dotenv()

console = Console()

class ContentSection(BaseModel):
    heading: Optional[str] = Field(default=None, description="Section heading")
    content: str = Field(..., description="Section content text")
    subsections: Optional[List[str]] = Field(default=None, description="Subsections or bullet points")

class LinkInfo(BaseModel):
    url: str = Field(..., description="Link URL")
    text: str = Field(..., description="Link text/title")
    category: Optional[str] = Field(default=None, description="Link category (navigation, article, external, etc.)")

class ContactInfo(BaseModel):
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    address: Optional[str] = Field(default=None, description="Physical address")
    
class ExtractionDiagnostics(BaseModel):
    """Informations de diagnostic pour l'extraction."""
    crawl_time_seconds: float = Field(..., description="Temps de crawling en secondes")
    processing_time_seconds: float = Field(..., description="Temps de traitement LLM en secondes")
    content_length: int = Field(..., description="Longueur du contenu brut")
    extraction_timestamp: str = Field(..., description="Timestamp de l'extraction")
    crawl4ai_version: str = Field(default="0.6.3", description="Version de Crawl4AI utilisée")
    success: bool = Field(..., description="Succès de l'extraction")
    errors: Optional[List[str]] = Field(default=None, description="Erreurs rencontrées")

class PageInformation(BaseModel):
    """Modèle complet pour l'extraction de pages web."""
    
    # Informations de base
    url: str = Field(..., description="URL of the page")
    title: str = Field(..., description="Main page title")
    description: Optional[str] = Field(default=None, description="Meta description or page summary")
    
    # Contenu principal
    main_content: str = Field(..., description="Primary page content as clean text")
    content_sections: Optional[List[ContentSection]] = Field(default=None, description="Organized content sections")
    
    # Navigation et liens
    navigation_links: Optional[List[LinkInfo]] = Field(default=None, description="Main navigation links")
    article_links: Optional[List[LinkInfo]] = Field(default=None, description="Links to articles or main content")
    external_links: Optional[List[LinkInfo]] = Field(default=None, description="External links")
    
    # Contenu structuré
    headlines: Optional[List[str]] = Field(default=None, description="Major headlines found on the page")
    categories: Optional[List[str]] = Field(default=None, description="Content categories or topics")
    dates: Optional[List[str]] = Field(default=None, description="Publication dates found")
    authors: Optional[List[str]] = Field(default=None, description="Author names found")
    
    # Métadonnées
    page_type: Optional[str] = Field(default=None, description="Type of page (news, business, blog, etc.)")
    language: Optional[str] = Field(default=None, description="Primary language")
    contact_info: Optional[ContactInfo] = Field(default=None, description="Contact information")
    social_media: Optional[Dict[str, str]] = Field(default=None, description="Social media links")
    
    # Données additionnelles
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional structured data")
    
    # Diagnostic
    diagnostics: ExtractionDiagnostics = Field(..., description="Extraction diagnostics")

# Agent d'extraction optimisé
extraction_agent = Agent(
    model=MistralChat(id="mistral-large-2411"),
    instructions=dedent("""
        You are an expert web content analyzer specializing in comprehensive information extraction.

        **EXTRACTION MISSION:**
        Extract ALL meaningful information from the provided webpage content with maximum completeness and accuracy.

        **CORE EXTRACTION AREAS:**
        
        1. **Content Analysis:**
           - Main page title and meta description
           - Primary content (clean, readable text without navigation clutter)
           - All major headlines, article titles, and news items
           - Content organized into logical sections with headings
           
        2. **Link Classification:**
           - Navigation links (main menu, breadcrumbs)
           - Article/content links (links to individual articles or pages)
           - External links (pointing to other domains)
           - Include both URL and descriptive text for each link
           
        3. **Structured Data:**
           - Publication dates, timestamps
           - Author names and bylines
           - Content categories, tags, topics
           - Any structured data like prices, locations, events
           
        4. **Page Metadata:**
           - Page type classification (news, business, blog, e-commerce, etc.)
           - Primary language
           - Contact information if present
           - Social media links
           
        **QUALITY STANDARDS:**
        - Be comprehensive but precise - include everything meaningful
        - Clean and organize content for readability
        - Categorize links accurately
        - Extract dates in recognizable formats
        - Only include contact info if explicitly found
        - Set optional fields to null if no relevant data exists
        
        **CRITICAL RULES:**
        - Never fabricate information
        - If a field cannot be determined, set it to null
        - Prioritize accuracy over completeness
        - Clean text of navigation artifacts and ads
    """).strip(),
    response_model=PageInformation,
)

async def crawl_webpage(url: str) -> tuple[str, float]:
    """
    Crawl une page web avec Crawl4AI optimisé.
    Retourne le contenu et le temps de crawling.
    """
    start_time = time.time()
    
    async with AsyncWebCrawler(
        verbose=True,
        headless=True,
    ) as crawler:
        result = await crawler.arun(
            url=url,
            # Configuration optimisée pour extraction complète
            word_count_threshold=3,  # Inclusif pour capturer plus de contenu
            exclude_external_links=False,  # Garder tous les liens
            exclude_social_media_links=False,  # Garder les réseaux sociaux
            remove_overlay_elements=True,  # Supprimer popups et overlays
            process_iframes=True,  # Traiter les iframes
            remove_forms=False,  # Garder les formulaires pour l'analyse
            delay_before_return_html=2.0,  # Attendre le rendu JavaScript
            
            # Options avancées
            css_selector=None,  # Pas de restriction de sélecteur
            screenshot=False,  # Pas besoin de screenshot
            pdf=False,  # Pas besoin de PDF
        )
        
        crawl_time = time.time() - start_time
        
        if result.success:
            return result.markdown, crawl_time
        else:
            raise Exception(f"Crawl4AI failed: {result.error_message}")

def extract_page_information(url: str) -> PageInformation:
    """
    Fonction principale d'extraction complète et robuste.
    """
    console.print(f"🚀 [bold blue]Extraction de:[/bold blue] {url}")
    
    errors = []
    
    try:
        # Phase 1: Crawling
        console.print("📡 [yellow]Phase 1:[/yellow] Crawling avec Crawl4AI...")
        raw_content, crawl_time = asyncio.run(crawl_webpage(url))
        
        console.print(f"✅ [green]Crawl réussi:[/green] {len(raw_content):,} caractères en {crawl_time:.2f}s")
        
        # Phase 2: Traitement LLM
        console.print("🧠 [yellow]Phase 2:[/yellow] Traitement par LLM...")
        processing_start = time.time()
        
        # Limitation du contenu pour éviter les timeouts
        content_for_llm = raw_content[:25000] if len(raw_content) > 25000 else raw_content
        if len(raw_content) > 25000:
            console.print(f"⚠️  [orange]Contenu tronqué:[/orange] {len(raw_content):,} → {len(content_for_llm):,} caractères")
        
        # Appel à l'agent d'extraction
        extraction_prompt = f"""
Analyze and extract comprehensive information from this webpage.

URL: {url}
Content Length: {len(content_for_llm):,} characters

WEBPAGE CONTENT:
{content_for_llm}

Extract all meaningful information following the detailed guidelines provided in your instructions.
"""
        
        structured_data = extraction_agent.run(extraction_prompt)
        processing_time = time.time() - processing_start
        
        console.print(f"✅ [green]Traitement réussi[/green] en {processing_time:.2f}s")
        
        # Création des diagnostics
        diagnostics = ExtractionDiagnostics(
            crawl_time_seconds=crawl_time,
            processing_time_seconds=processing_time,
            content_length=len(raw_content),
            extraction_timestamp=datetime.now().isoformat(),
            success=True,
            errors=errors if errors else None
        )
        
        # Ajout des diagnostics au résultat
        result = structured_data.content
        result.diagnostics = diagnostics
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        errors.append(error_msg)
        console.print(f"❌ [red]Erreur:[/red] {error_msg}")
        
        # Création d'un résultat d'erreur avec diagnostics
        diagnostics = ExtractionDiagnostics(
            crawl_time_seconds=0.0,
            processing_time_seconds=0.0,
            content_length=0,
            extraction_timestamp=datetime.now().isoformat(),
            success=False,
            errors=errors
        )
        
        return PageInformation(
            url=url,
            title="ERREUR D'EXTRACTION",
            main_content=f"Erreur lors de l'extraction: {error_msg}",
            diagnostics=diagnostics
        )

def print_extraction_summary(result: PageInformation):
    """Affiche un résumé détaillé de l'extraction."""
    
    console.print("\n" + "="*80)
    console.print(f"📊 [bold cyan]RÉSUMÉ D'EXTRACTION[/bold cyan]")
    console.print("="*80)
    
    # Informations de base
    console.print(f"🌐 [bold]URL:[/bold] {result.url}")
    console.print(f"📰 [bold]Titre:[/bold] {result.title}")
    console.print(f"🏷️  [bold]Type:[/bold] {result.page_type or 'Non déterminé'}")
    console.print(f"🌍 [bold]Langue:[/bold] {result.language or 'Non déterminée'}")
    
    # Contenu extrait
    console.print(f"\n📝 [bold yellow]CONTENU EXTRAIT:[/bold yellow]")
    console.print(f"  • Contenu principal: {len(result.main_content):,} caractères")
    console.print(f"  • Headlines: {len(result.headlines or [])}")
    console.print(f"  • Sections: {len(result.content_sections or [])}")
    console.print(f"  • Dates trouvées: {len(result.dates or [])}")
    console.print(f"  • Auteurs: {len(result.authors or [])}")
    
    # Liens
    console.print(f"\n🔗 [bold blue]LIENS EXTRAITS:[/bold blue]")
    console.print(f"  • Navigation: {len(result.navigation_links or [])}")
    console.print(f"  • Articles: {len(result.article_links or [])}")
    console.print(f"  • Externes: {len(result.external_links or [])}")
    
    # Diagnostics
    diag = result.diagnostics
    console.print(f"\n⚡ [bold green]PERFORMANCE:[/bold green]")
    console.print(f"  • Crawling: {diag.crawl_time_seconds:.2f}s")
    console.print(f"  • Traitement LLM: {diag.processing_time_seconds:.2f}s")
    console.print(f"  • Total: {diag.crawl_time_seconds + diag.processing_time_seconds:.2f}s")
    console.print(f"  • Contenu brut: {diag.content_length:,} caractères")
    console.print(f"  • Succès: {'✅' if diag.success else '❌'}")
    
    if diag.errors:
        console.print(f"\n⚠️  [bold red]ERREURS:[/bold red]")
        for error in diag.errors:
            console.print(f"  • {error}")
    
    # Aperçu du contenu
    if result.headlines:
        console.print(f"\n📰 [bold]PREMIERS HEADLINES:[/bold]")
        for i, headline in enumerate(result.headlines[:5], 1):
            console.print(f"  {i}. {headline}")
    
    console.print("\n" + "="*80)

def batch_extract_pages(urls: List[str]) -> Dict[str, PageInformation]:
    """Extraction en lot pour plusieurs URLs."""
    
    console.print(f"🚀 [bold]Extraction en lot:[/bold] {len(urls)} URLs")
    
    results = {}
    
    for i, url in enumerate(urls, 1):
        console.print(f"\n[bold cyan]>>> {i}/{len(urls)}[/bold cyan]")
        
        try:
            result = extract_page_information(url)
            results[url] = result
            
            # Résumé rapide
            status = "✅" if result.diagnostics.success else "❌"
            headlines_count = len(result.headlines or [])
            console.print(f"{status} [green]{result.title}[/green] - {headlines_count} headlines")
            
        except Exception as e:
            console.print(f"❌ [red]Erreur pour {url}:[/red] {e}")
            results[url] = None
    
    # Statistiques finales
    successful = len([r for r in results.values() if r and r.diagnostics.success])
    console.print(f"\n🎯 [bold]Résultats:[/bold] {successful}/{len(urls)} extractions réussies")
    
    return results

# Interface principale
def main():
    """Interface principale du script."""
    
    console.print("🕷️  [bold blue]EXTRACTEUR WEB CRAWL4AI + AGNO[/bold blue]")
    console.print("="*60)
    
    # URLs de test
    test_urls = [
        #"https://www.nbcnews.com/business",
        #"https://www.agno.com",
        #"https://github.com/unclecode/crawl4ai",
        #"https://techcrunch.com",
        "https://www.lemonde.fr/"
    ]
    
    # Test sur une URL
    console.print("\n🎯 [bold]Test sur une URL:[/bold]")
    result = extract_page_information(test_urls[0])
    print_extraction_summary(result)
    
    # Option: extraction détaillée
    console.print(f"\n🔍 [bold]Résultat détaillé disponible[/bold]")
    console.print("Pour voir le résultat complet, décommentez la ligne ci-dessous:")
    # pprint(result)  # Décommenter pour voir le résultat complet
    
    # Test en lot
    console.print(f"\n📦 [bold]Test en lot sur {len(test_urls)} URLs:[/bold]")
    batch_results = batch_extract_pages(test_urls)
    
    return result, batch_results

if __name__ == "__main__":
    # Lancement du script
    single_result, batch_results = main()
    
    console.print("\n✨ [bold green]Extraction terminée![/bold green]")
    console.print("Les résultats sont disponibles dans les variables 'single_result' et 'batch_results'")