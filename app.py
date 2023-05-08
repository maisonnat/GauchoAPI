from flask import Flask, request, jsonify
from scraper import FravegaScraper, GarbarinoScraper, PerozziScraper
"""
excluding GarbarinoScraper, becouse need Playwright, and need to fix TimeoutError, 
but with the rest of the scraper like FravegaScraper, and PerozziScraper work great with request
"""
app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    query = request.json.get('query', '')
    send_notifications = request.json.get('send_notifications', False)
    

    if not query:
        return jsonify({"error": "Query is missing"}), 400

    fravega_scraper = FravegaScraper(query)
    #garbarino_scraper = GarbarinoScraper(query)
    perozzi_scraper = PerozziScraper(query)

    fravega_scraper.run(send_notifications=send_notifications)
    #garbarino_scraper.run(send_notifications=send_notifications)
    perozzi_scraper.run(send_notifications=send_notifications)

    all_results = {
        'Fravega': fravega_scraper.products,
        #'Garbarino': garbarino_scraper.products,
        'Perozzi': perozzi_scraper.products
    }

    return jsonify(all_results), 200

if __name__ == '__main__':
    app.run(debug=True)
