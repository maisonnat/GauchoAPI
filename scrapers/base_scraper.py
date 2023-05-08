import datetime
import logging
import os
import random
import smtplib
import time
from abc import ABC, abstractmethod
from email.message import EmailMessage
from requests.exceptions import RequestException
from models import Product, create_tables
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
from diskcache import Cache
from tenacity import retry, wait_fixed, stop_after_attempt

from tools_api import load_json_file

load_dotenv()
cache = Cache("/cache_directory/")
PROXIES = load_json_file('proxies.json')
USER_AGENT = load_json_file('user_agents.json')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", mode="w")
    ]
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)


def send_email_notification(subject, body):
    """
    Set your .env with this information
    YOUR_USERNAME=
    YOUR_PASSWORD=

    and then setting your From and To
    """
    your_username = os.getenv("YOUR_USERNAME")
    your_password = os.getenv("YOUR_PASSWORD")
    msg = EmailMessage()
    msg.set_content(body)

    msg['Subject'] = subject
    msg['From'] = 'from_email@example.com'
    msg['To'] = 'to_email@example.com'

    
    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login(your_username, your_password)
        server.send_message(msg)




class BaseScraper(ABC):
    """
    Class base for all scrapers of sites.
    Provides common method for all sub-class
    
    """
    def __init__(self, query):
        self.query = query
        self.products = []

    
    def format_query(self,query:str)->str:
        """
        Format the query string for the target website.
        
        :param query: The search query.
        :type query: str
        :return: The formatted search query.
        :rtype: str
        """
        return query

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
        cached_html = cache.get(url)
        if cached_html is not None:
            logging.info("Retrieved cache HTML for URL: %s", url)
            return cached_html
        
        headers = {"User-Agent": self.get_user_agent()}
        try:
            session = requests.Session()
            response = session.get(url, headers=headers)
            cache.set(url,response.text, expire=86400) #expire cache 1 day(in seconds)
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


    def run(self, send_notifications=False):
        """
        Run the scraper, fetch the HTML content, parse the results, and save the product data. If the structure change and have error,
        then send email notification if send_notifications is set to True.
        Create your .env and put: 
        YOUR_USERNAME=
        YOUR_PASSWORD=
        :param send_notifications: If True, send email notifications on error. Default is False.
        :type send_notifications: bool
        """
        try:
            start_time = time.time()
            logging.info("Starting scraper: %s", self.__class__.__name__)
            html = self.fetch_results()
            self.parse_results(html)
            for product in self.products:
                self.save_product(product)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logging.info("Scraper finished: %s, elapsed time: %.2f seconds", self.__class__.__name__, elapsed_time)
        except ScraperError as e:
            logging.error("Error on run() scraper: %s", e.scraper)
            logging.error("Message error: %s", e.message)
            if send_notifications:
                send_email_notification(f"Error trying to run: {e.scraper}", f"Message error: {e.message}")


class ScraperError(Exception):
    def __init__(self, message, scraper):
        self.message = message
        self.scraper = scraper
        super().__init__(message)