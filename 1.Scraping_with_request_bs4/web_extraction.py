import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin, urlparse

class WebScraper:
    def __init__(self, base_url, headers=None):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Headers par défaut pour éviter d'être bloqué
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        if headers:
            default_headers.update(headers)
        
        self.session.headers.update(default_headers)
    
    def get_page(self, url):
        """Récupère le contenu d'une page web"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Lève une exception si erreur HTTP
            return response
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération de {url}: {e}")
            return None
    
    def parse_html(self, html_content):
        """Parse le contenu HTML avec Beautiful Soup"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def extract_links(self, soup, base_url):
        """Extrait tous les liens d'une page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convertit les liens relatifs en liens absolus
            absolute_url = urljoin(base_url, href)
            links.append({
                'text': link.get_text(strip=True),
                'url': absolute_url
            })
        return links
    
    def extract_images(self, soup, base_url):
        """Extrait toutes les images d'une page"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        return images
    
    def scrape_article_content(self, url):
        """Exemple d'extraction d'articles de blog"""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = self.parse_html(response.content)
        
        # Adaptation selon la structure du site
        article_data = {
            'title': '',
            'content': '',
            'author': '',
            'date': '',
            'url': url
        }
        
        # Extraire le titre (plusieurs sélecteurs possibles)
        title_selectors = ['h1', '.title', '#title', '[class*="title"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                article_data['title'] = title_elem.get_text(strip=True)
                break
        
        # Extraire le contenu
        content_selectors = ['.content', '#content', 'article', '.post-content']
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                article_data['content'] = content_elem.get_text(strip=True)
                break
        
        # Extraire l'auteur
        author_selectors = ['.author', '.by-author', '[class*="author"]']
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                article_data['author'] = author_elem.get_text(strip=True)
                break
        
        return article_data
    
    def scrape_table_data(self, url, table_selector='table'):
        """Extrait les données d'un tableau HTML"""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = self.parse_html(response.content)
        table = soup.select_one(table_selector)
        
        if not table:
            print("Aucun tableau trouvé")
            return None
        
        data = []
        
        # Extraire les en-têtes
        headers = []
        header_row = table.find('thead')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
        
        # Extraire les données
        tbody = table.find('tbody') or table
        for row in tbody.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells:  # Ignorer les lignes vides
                row_data = {}
                for i, cell in enumerate(cells):
                    header = headers[i] if i < len(headers) else f'column_{i}'
                    row_data[header] = cell.get_text(strip=True)
                data.append(row_data)
        
        return data
    
    def save_to_csv(self, data, filename):
        """Sauvegarde les données dans un fichier CSV"""
        if not data:
            print("Aucune donnée à sauvegarder")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if isinstance(data[0], dict):
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(csvfile)
                writer.writerows(data)
        
        print(f"Données sauvegardées dans {filename}")

# Exemples d'utilisation
def exemple_scraping_simple(url):
    """Exemple simple de scraping"""
    scraper = WebScraper("https://example.com")
    
    # Scraper une page
    
    response = scraper.get_page(url) #("https://httpbin.org/html")
    if response:
        soup = scraper.parse_html(response.content)
        
        # Extraire le titre
        title = soup.find('title')
        if title:
            print(f"Titre de la page: {title.get_text()}")
        
        # Extraire tous les liens
        links = scraper.extract_links(soup, url)
        print(f"Nombre de liens trouvés: {len(links)}")
        print(f"5ers liens trouvés: {links[0:5]}")
        
        # A configurer ici pour intégrer d'autres informations utiles.
        # Voir les méthodes disponibles :
        # - extract_links
        # - extract_images
        # - scrape_article_content
        # - scrape_table_data

def exemple_scraping_avec_delai():
    """Exemple avec gestion des délais pour éviter la surcharge"""
    scraper = WebScraper("https://example.com")
    
    urls_to_scrape = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        # Ajouter d'autres URLs
    ]
    
    results = []
    
    for url in urls_to_scrape:
        print(f"Scraping: {url}")
        response = scraper.get_page(url)
        
        if response:
            soup = scraper.parse_html(response.content)
            # Traitement des données...
            results.append({"url": url, "status": "success"})
        else:
            results.append({"url": url, "status": "failed"})
        
        # Délai entre les requêtes pour être respectueux
        time.sleep(1)
    
    return results

# Utilisation
if __name__ == "__main__":
    exemple_scraping_simple(url="https://www.lemonde.fr/")