import datetime
import re
from urllib.parse import urlparse, urljoin
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.error import URLError, HTTPError
from requests.exceptions import RequestException
from tqdm import tqdm
from selenium.webdriver.support.ui import WebDriverWait
import time
import traceback

class SightmapScraper:
    def __init__(self, websites):
        self.websites = websites
        self.webdriver_service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.webdriver_service)
        self.driver.set_page_load_timeout(10)
        self.data = []
        self.sightmap_found = False

    def log_error(self, start_url, error_message):
        timestamp = datetime.datetime.now().replace(microsecond=0)
        self.data.append({
            'Website': start_url,
            'SightMap Integrated?': error_message,
            'Time': timestamp.time(),
            'Date': timestamp.date(),
        })
        self.to_csv('SightMap Tracker Results.csv', self.data)

    def normalize_url(self, url):
        return re.sub(r'www\.|/$', '', url.lower())

    def parse(self, soup, url, start_url):
        for iframe in soup.find_all('iframe', {'src': True}):
            if 'https://sightmap.com/embed/' in iframe['src']:
                self.sightmap_found = True
                return {
                    'sightmap_url': iframe['src'],
                    'api_usage': 'Yes' if '?enable' in iframe['src'] else 'No',
                    'closest_url_to_sightmap': url
                }
        return None

    def scrape(self):
        for start_url in tqdm(self.websites, desc="Scraping websites", unit="website"):
            self.sightmap_found = False
            if not start_url.strip(): 
                continue
            if not start_url.startswith(('http://', 'https://')):
                start_url = 'http://' + start_url

            visited_urls = set()
            self.process_url(start_url, start_url, visited_urls)

            timestamp = datetime.datetime.now().replace(microsecond=0)
            if self.sightmap_found:
                self.data.append({
                    'Website': start_url,
                    'SightMap Integrated?': 'Yes',
                    'SightMap Embed': self.sightmap_found['sightmap_url'],
                    'API Usage': self.sightmap_found['api_usage'],
                    'Closest URL to SightMap': self.sightmap_found['closest_url_to_sightmap'],
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

    def process_url(self, url, start_url, visited_urls):
        normalized_url = self.normalize_url(url)
        if normalized_url in visited_urls or self.sightmap_found:
            return
        visited_urls.add(normalized_url)

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 3).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete')
            time.sleep(1)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            sightmap_data = self.parse(soup, url, start_url)
            if sightmap_data:
                self.sightmap_found = sightmap_data

            if not self.sightmap_found:
                self.follow_links(soup, url, start_url, visited_urls)
        except Exception as e:
            self.log_error(start_url, f'Error loading {url}: {str(e)}')

    def follow_links(self, soup, current_url, start_url, visited_urls):
        start_domain = urlparse(start_url).netloc
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(current_url, href)
            normalized_full_url = self.normalize_url(full_url)
            if urlparse(full_url).netloc == urlparse(start_url).netloc:
                path_depth = len(urlparse(full_url).path.strip('/').split('/'))
                if path_depth == 1 and normalized_full_url not in visited_urls:
                    self.process_url(full_url, start_url, visited_urls)

    def to_csv(self, filename, data):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

# List of websites to scrape
websites = [
    'http://www.indigo301.com/',
     'https://www.loneoakapartments.com/',
        'https://crosstownatx.com/',
        'https://presidiumparkapts.com/',
        'https://presidiumregalapts.com/',
        'https://www.livingatthecameron.com/',
        'https://prosedistrictwest.com/',
        'https://www.livetheithacan.com/',
        'http://www.valleyridgeliving.com',
        'https://www.baileyscrossing.com/'   
     
        
]

# Instantiate and run the scraper
scraper = SightmapScraper(websites)
scraper.scrape()
