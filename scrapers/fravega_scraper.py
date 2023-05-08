import logging
from scrapers.base_scraper import BaseScraper, ScraperError
from bs4 import BeautifulSoup

class FravegaScraper(BaseScraper):
    
    def __init__(self, query: str):
        self.query = self.format_query(query)
        self.products = []

    def format_query(self, query: str) -> str:
        return query.replace(" ", "%20")
    

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
        if not product_list:
            raise ScraperError("Fravega: elements not found", self.__class__.__name__)
        
        logging.info('Fravega: Quantity of products found: %i', len(product_list))

        for product in product_list:
            product_data = {
                'name': product.find('span', class_='sc-6321a7c8-0').text.strip(),
                'price': float(product.find('span', class_='sc-ad64037f-0').text.replace('$', '').replace('.', '').replace(',', '.')),
                'url': 'https://www.fravega.com' + product.find('a')['href'],
                'image_url': product.find('img', class_='sc-3c31b0ed-0')['src']
            }
            self.products.append(product_data)