from scraper import FravegaScraper, GarbarinoScraper, PerozziScraper
from models import initialize_database

#SEARCH_QUERY = "celular+samsung+a23"
SEARCH_QUERY = "celular%20samsung%20galaxy%20a23"


if __name__ == "__main__":
    initialize_database()

    fravega_scraper = FravegaScraper(SEARCH_QUERY)
    fravega_scraper.run()

    garbarino_scraper = GarbarinoScraper(SEARCH_QUERY)
    garbarino_scraper.run()

    perozzi_scraper = PerozziScraper("celular+samsung+a23")
    perozzi_scraper.run()
    