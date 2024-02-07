import datetime
import re
from urllib.parse import urlparse, urljoin
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
from selenium.webdriver.support.ui import WebDriverWait
import time

class SightmapScraper:
    def __init__(self, websites):
        self.websites = websites
        self.webdriver_service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.webdriver_service)
        self.driver.set_page_load_timeout(10)
        self.data = []

    def log_error(self, start_url, error_message):
        timestamp = datetime.datetime.now().replace(microsecond=0)
        self.data.append({
            'Website': start_url,
            'SightMap Integrated?': 'Error - ' + error_message,
            'Time': timestamp.time(),
            'Date': timestamp.date(),
        })
        self.to_csv('SightMap Tracker Results.csv', self.data)

    def normalize_url(self, url):
        return re.sub(r'www\.|/$', '', url.lower())

    def parse(self, soup, url, start_url):
        for iframe in soup.find_all('iframe', {'src': True}):
            if 'https://sightmap.com/embed/' in iframe['src']:
                return {
                    'sightmap_url': iframe['src'],
                    'api_usage': 'Yes' if '?enable' in iframe['src'] else 'No',
                    'closest_url_to_sightmap': url
                }
        return None

    def scrape(self):
        for start_url in tqdm(self.websites, desc="Scraping websites", unit="website"):
            sightmap_found = False
            if not start_url.strip():
                continue
            if not start_url.startswith(('http://', 'https://')):
                start_url = 'http://' + start_url

            visited_urls = set()
            sightmap_found = self.process_url(start_url, start_url, visited_urls, sightmap_found)

            timestamp = datetime.datetime.now().replace(microsecond=0)
            if sightmap_found:
                self.data.append({
                    'Website': start_url,
                    'SightMap Integrated?': 'Yes',
                    'SightMap Embed': sightmap_found['sightmap_url'],
                    'API Usage': sightmap_found['api_usage'],
                    'Closest URL to SightMap': sightmap_found['closest_url_to_sightmap'],
                    'Time': timestamp.time(),
                    'Date': timestamp.date(),
                })
            else:
                self.data.append({
                    'Website': start_url,
                    'SightMap Integrated?': 'No',
                    'Time': timestamp.time(),
                    'Date': timestamp.date(),
                })

        self.driver.quit()
        self.to_csv('SightMap Tracker Results.csv', self.data)

    def process_url(self, url, start_url, visited_urls, sightmap_found):
        normalized_url = self.normalize_url(url)
        if normalized_url in visited_urls or sightmap_found:
            return sightmap_found
        visited_urls.add(normalized_url)

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 3).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete')
            time.sleep(1)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            sightmap_data = self.parse(soup, url, start_url)
            if sightmap_data:
                return sightmap_data

            self.follow_links(soup, url, start_url, visited_urls, sightmap_found)
        except Exception as e:
            self.log_error(start_url, 'Error loading ' + url + ': ' + str(e))
        return sightmap_found

    def follow_links(self, soup, current_url, start_url, visited_urls, sightmap_found):
        if sightmap_found:
            return
        start_domain = urlparse(start_url).netloc
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(current_url, href)
            if urlparse(full_url).netloc == start_domain:
                path_depth = len(urlparse(full_url).path.strip('/').split('/'))
                if path_depth <= 1 and full_url not in visited_urls:
                    sightmap_found = self.process_url(full_url, start_url, visited_urls, sightmap_found)
                    if sightmap_found:
                        break

    def to_csv(self, filename, data):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

websites = [

]
scraper = SightmapScraper(websites)
scraper.scrape()
