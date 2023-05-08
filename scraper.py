# scraper.py

import tools_api
from bs4 import BeautifulSoup
import datetime
from abc import ABC, abstractmethod
from models import Product, create_tables
import requests
from requests.exceptions import RequestException
from playwright.sync_api import sync_playwright
from tenacity import retry, wait_fixed,stop_after_attempt
import random
import logging


logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)


PROXIES = tools_api.load_json_file('proxies.json')
USER_AGENT = tools_api.load_json_file('user_agents.json')


class BaseScraper(ABC):
    """
    Class base for all scrapers of sites.
    Provides common method for all sub-class
    
    """
    def __init__(self, query):
        self.query = query
        self.products = []

    def get_proxy(self):
        """
        Get a random proxy from the list of proxies.

        :return: A random proxy.
        :rtype: str
        """
        return random.choice(PROXIES)
    

    def get_user_agent(self):
        """
        Get a random User-Agent from the list of User-Agents.

        :return: A random User-Agent.
        :rtype: str
        """
        return random.choice(USER_AGENT)
    
    @retry(wait=wait_fixed(3), stop=stop_after_attempt(3))
    def get_html_from_url(self,url):
        """
        Gets the HTML content of a URL using the 'requests' library.

        :param url: URL of site in order to get the content.
        :type url: str
        :return: The HTML content of the web page, if it could be obtained successfuly.
                    Otherwise, None.
        :rtype: str, None
        """
        headers = {"User-Agent": self.get_user_agent()}
        try:
            session = requests.Session()
            response = session.get(url, headers=headers)
            return response.text
        except requests.RequestException as e:
            logging.error("Error fetching the page: %i", response.status_code)
            raise e


    def save_product(self, product_data):
        """
        Save the product data into the database.

        :param product_data: Dictionary containing product data.
        :type product_data: dict
        """
        product, created = Product.get_or_create(url=product_data['url'], defaults=product_data)

        if not created:
            product.price = product_data['price']
            product.image_url = product_data['image_url']
            product.timestamp = datetime.datetime.now()
            product.save()

        

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(3))
    def fetch_results(self):
        """
        Fetch the HTML content of the search results page.

        :return: The HTML content of the search results page.
        :rtype: str
        """
        try:
            response = requests.get(self.url, headers=self.get_user_agent, proxies={"http": self.get_proxy(), "https": self.get_proxy()})
            response.raise_for_status()
            return response.text
        except RequestException as e:
            logging.error("Error fetching HTML content of the search results page: %s", e)
            raise e


    @abstractmethod
    def parse_results(self,html):
        """
        Parse the HTML content of the search results page and extract the product data.

        :param html: The HTML content of the search results page.
        :type html: str
        """
        pass


    def run(self):
        """
        Run the scraper, fetch the HTML content, parse the results, and save the product data.
        """
        logging.info("Starting scraper: %s", self.__class__.__name__ )
        html = self.fetch_results()
        self.parse_results(html)
        for product in self.products:
            self.save_product(product)
        logging.info("Scraper finished: %s", self.__class__.__name__ )




class FravegaScraper(BaseScraper):
    def fetch_results(self):
        """
        Fetch the HTML content of the Fravega search results page.

        :return: The HTML content of the Fravega search results page.
        :rtype: str
        """
        url = f'https://www.fravega.com/l/?keyword={self.query}'
        return self.get_html_from_url(url)
    

    def parse_results(self, html):
        """
        Parse the HTML content of the Fravega search results page and extract the product data.

        :param html: The HTML content of the Fravega search results page.
        :type html: str
        """
        soup = BeautifulSoup(html, 'html.parser')
        product_list = soup.find_all('article', {'data-test-id': 'result-item'})
        logging.info('Fravega: Quantity of products found: %i', len(product_list))

        for product in product_list:
            product_data = {
                'name': product.find('span', class_='sc-6321a7c8-0').text.strip(),
                'price': float(product.find('span', class_='sc-ad64037f-0').text.replace('$', '').replace('.', '').replace(',', '.')),
                'url': 'https://www.fravega.com' + product.find('a')['href'],
                'image_url': product.find('img', class_='sc-3c31b0ed-0')['src']
            }
            self.products.append(product_data)
    

class GarbarinoScraper(BaseScraper):
    def fetch_results(self):
        """
        Fetch the HTML content of the Garbarino search results page.

        :return: The HTML content of the Garbarino search results page.
        :rtype: str
        """
        url = f'https://www.garbarino.com/{self.query}?_q={self.query}&map=ft'

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle")
            tools_api.scroll_to_bottom(page)
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()

        return html


    def parse_results(self, html):
        """
        Parse the HTML content of the Garbarino search results page and extract the product data.

        :param html: The HTML content of the Garbarino search results page.
        :type html: str
        """
        soup = BeautifulSoup(html, 'html.parser')
        product_list = soup.find_all('section', {'class': 'vtex-product-summary-2-x-container'})
        logging.info('Garbarino: Quantity of products found: %i', len(product_list))
        
        for product in product_list:
            # Name and URL
            link = product.find('a', class_='vtex-product-summary-2-x-clearLink')
            if link:
                href = link['href']
                url = f'https://www.garbarino.com{href}'
                
            else:
                continue

            # Price
            # Price
            price_element = product.find('span', {'class': 'vtex-product-price-1-x-sellingPrice'})
            if price_element:
                integer_spans = price_element.find_all('span', {'class': 'vtex-product-price-1-x-currencyInteger'})
                integer_part = ''.join([span.text for span in integer_spans])
                decimal_separator = price_element.find('span', {'class': 'vtex-product-price-1-x-currencyGroup'}).text
                space = price_element.find('span', {'class': 'vtex-product-price-1-x-currencyLiteral'}).text
                decimal_part = price_element.find('span', {'class': 'vtex-product-price-1-x-currencyFraction'})
                if decimal_part:
                    decimal_part = decimal_part.text
                else:
                    decimal_part = '00'
                price_string = f"{integer_part}{decimal_separator}{decimal_part}"
                price = float(price_string)


            # Image URL
            image = product.find('img', class_='vtex-product-summary-2-x-imageNormal')
            if image:
                image_url = image['src']
                name = image['alt']
            else:
                name_element = product.find('h2') or product.find('h3')
                if name_element:
                    name = name_element.text.strip()
                else:
                    name = 'Unknown'

            product_data = {
                'name': name,
                'price': price,
                'url': url,
                'image_url': image_url
            }

            self.products.append(product_data)


class PerozziScraper(BaseScraper):

    def fetch_results(self):
        """
        Parse the HTML content of the Garbarino search results page and extract the product data.

        :param html: The HTML content of the Garbarino search results page.
        :type html: str
        """
        url = f'https://www.perozzi.com.ar/module/iqitsearch/searchiqit?order=product.position.desc&resultsPerPage=9999999&s={self.query}'
        return self.get_html_from_url(url)
    

    def parse_results(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        product_list = soup.find_all('div', {'class': 'js-product-miniature-wrapper'})
        logging.info('Perozzi: Quantity of products found: %i', len(product_list))

        for product in product_list:
            # Name and URL
            title_element = product.find('h2', {'class': 'h3 product-title'})
            name = title_element.get_text(strip=True)
            url = title_element.find('a')['href']

            # Price
            price_element = product.find('span', {'class': 'product-price'})
            price_text = price_element.get_text(strip=True)
            price = float(price_text.replace('$', '').replace('.', '').replace(',', '.'))

            # Image URL
            img_element = product.find('img', {'class': 'img-fluid'})
            image_url = img_element['data-src'] if 'data-src' in img_element.attrs else img_element['src']

            product_data = {
                'name': name,
                'price': price,
                'url': url,
                'image_url': image_url
            }

            self.products.append(product_data)