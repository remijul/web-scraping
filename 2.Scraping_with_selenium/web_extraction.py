from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import json

class SeleniumScraper:
    def __init__(self, headless=True, window_size="1920,1080"):
        """Initialise le driver Selenium"""
        self.options = Options()
        
        if headless:
            self.options.add_argument('--headless')
        
        self.options.add_argument(f'--window-size={window_size}')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = None
        self.wait = None
    
    def start_driver(self):
        """Démarre le driver Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 10)
            print("Driver Selenium démarré avec succès")
        except Exception as e:
            print(f"Erreur lors du démarrage du driver: {e}")
            print("Assurez-vous que ChromeDriver est installé et dans le PATH")
    
    def close_driver(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            print("Driver fermé")
    
    def get_page(self, url, wait_time=10):
        """Charge une page et attend qu'elle soit prête"""
        try:
            self.driver.get(url)
            # Attendre que la page soit entièrement chargée
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)  # Délai supplémentaire pour le JavaScript
            return True
        except TimeoutException:
            print(f"Timeout lors du chargement de {url}")
            return False
        except Exception as e:
            print(f"Erreur lors du chargement de {url}: {e}")
            return False
    
    def wait_for_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Attend qu'un élément soit présent"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            print(f"Élément {selector} non trouvé après {timeout}s")
            return None
    
    def click_element(self, selector, by=By.CSS_SELECTOR):
        """Clique sur un élément"""
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except TimeoutException:
            print(f"Impossible de cliquer sur {selector}")
            return False
    
    def scroll_to_bottom(self, pause_time=1):
        """Fait défiler jusqu'en bas de la page"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll vers le bas
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Attendre que la page charge
            time.sleep(pause_time)
            
            # Calculer la nouvelle hauteur de scroll
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height
    
    def scrape_infinite_scroll(self, item_selector, max_items=None):
        """Scraper une page avec scroll infini"""
        items = []
        seen_items = set()
        
        while True:
            # Scroll vers le bas
            self.scroll_to_bottom()
            
            # Récupérer tous les éléments actuels
            current_items = self.driver.find_elements(By.CSS_SELECTOR, item_selector)
            
            new_items_found = False
            
            for item in current_items:
                # Utiliser le texte ou un attribut unique comme identifiant
                item_id = item.text or item.get_attribute('innerHTML')
                
                if item_id not in seen_items:
                    seen_items.add(item_id)
                    
                    # Extraire les données de l'élément
                    item_data = self.extract_item_data(item)
                    items.append(item_data)
                    new_items_found = True
                    
                    if max_items and len(items) >= max_items:
                        return items[:max_items]
            
            # Si aucun nouvel élément n'est trouvé, arrêter
            if not new_items_found:
                break
            
            print(f"Éléments trouvés: {len(items)}")
        
        return items
    
    def extract_item_data(self, element):
        """Extrait les données d'un élément (à personnaliser selon le site)"""
        try:
            data = {
                'text': element.text,
                'html': element.get_attribute('innerHTML')
            }
            
            # Exemple: extraire des données spécifiques
            try:
                title = element.find_element(By.CSS_SELECTOR, 'h2, h3, .title')
                data['title'] = title.text
            except NoSuchElementException:
                data['title'] = ''
            
            try:
                link = element.find_element(By.CSS_SELECTOR, 'a')
                data['link'] = link.get_attribute('href')
            except NoSuchElementException:
                data['link'] = ''
            
            return data
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
            return {'error': str(e)}
    
    def handle_popup(self, popup_selector, close_button_selector):
        """Gère les popups (cookies, newsletters, etc.)"""
        try:
            popup = self.driver.find_element(By.CSS_SELECTOR, popup_selector)
            if popup.is_displayed():
                close_button = self.driver.find_element(By.CSS_SELECTOR, close_button_selector)
                close_button.click()
                print("Popup fermé")
                time.sleep(1)
        except NoSuchElementException:
            pass  # Pas de popup trouvé
    
    def scrape_spa_content(self, url, content_selector, navigation_links=None):
        """Scraper une Single Page Application"""
        if not self.get_page(url):
            return None
        
        results = []
        
        # Gérer les popups si nécessaire
        self.handle_popup('.popup, .modal', '.close, .dismiss')
        
        if navigation_links:
            # Naviguer à travers différentes sections
            for link_selector in navigation_links:
                try:
                    if self.click_element(link_selector):
                        # Attendre que le contenu se charge
                        time.sleep(3)
                        
                        # Extraire le contenu
                        content = self.wait_for_element(content_selector)
                        if content:
                            results.append({
                                'section': link_selector,
                                'content': content.text,
                                'html': content.get_attribute('innerHTML')
                            })
                except Exception as e:
                    print(f"Erreur lors de la navigation vers {link_selector}: {e}")
        else:
            # Extraire le contenu de la page actuelle
            content = self.wait_for_element(content_selector)
            if content:
                results.append({
                    'content': content.text,
                    'html': content.get_attribute('innerHTML')
                })
        
        return results
    
    def fill_form_and_submit(self, form_data):
        """Remplit et soumet un formulaire"""
        try:
            for field_selector, value in form_data.items():
                field = self.wait_for_element(field_selector)
                if field:
                    field.clear()
                    field.send_keys(value)
            
            # Soumettre le formulaire
            submit_button = self.wait_for_element('input[type="submit"], button[type="submit"], .submit')
            if submit_button:
                submit_button.click()
                return True
            
        except Exception as e:
            print(f"Erreur lors du remplissage du formulaire: {e}")
        
        return False

# Exemple d'utilisation
def exemple_scraping_dynamique():
    scraper = SeleniumScraper(headless=False)  # Mode visible pour débogage
    
    try:
        scraper.start_driver()
        
        # Exemple: scraper un site avec contenu dynamique
        if scraper.get_page("https://www.youtube.com/"):
            #("https://www.tours.fr/")
            #("https://example.com")
            
            # Attendre qu'un élément spécifique soit chargé
            element = scraper.wait_for_element('.dynamic-content')
            if element:
                print("Contenu dynamique trouvé:", element.text)
            
            # Exemple de scroll infini
            items = scraper.scrape_infinite_scroll('.item', max_items=50)
            print(f"Nombre d'éléments récupérés: {len(items)}")
            
    finally:
        scraper.close_driver()

def exemple_scraping_avec_interaction():
    """Exemple avec interactions (clics, formulaires)"""
    scraper = SeleniumScraper()
    
    try:
        scraper.start_driver()
        
        if scraper.get_page("https://www.tours.fr/"): #("https://example.com/search"):
            # Remplir un formulaire de recherche
            form_data = {
                '#search-input': 'python web scraping',
                '#category-select': 'technology'
            }
            
            if scraper.fill_form_and_submit(form_data):
                # Attendre les résultats
                results = scraper.wait_for_element('.search-results')
                if results:
                    print("Résultats de recherche:", results.text)
    
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    print("Exemples de scraping dynamique avec Selenium")
    exemple_scraping_dynamique()