from scrapers.base_scraper import BaseScraper, ScraperError
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import tools_api
import logging

class GarbarinoScraper(BaseScraper):
    def __init__(self, query: str):
        self.query = self.format_query(query)
        self.products = []

    def format_query(self, query: str) -> str:
        return query.replace(" ", "%20")
    
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
        if not product_list:
            raise ScraperError("Garbarino: elements not found", self.__class__.__name__)
        
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