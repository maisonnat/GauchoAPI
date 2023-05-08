from scrapers.base_scraper import BaseScraper, ScraperError
from bs4 import BeautifulSoup
import logging

class PerozziScraper(BaseScraper):
    def __init__(self, query: str):
        self.query = self.format_query(query)
        self.products = []

    def format_query(self, query: str) -> str:
        return query.replace(" ", "%20")

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
        if not product_list:
            raise ScraperError("Perozzi: elements not found", self.__class__.__name__)
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