from flask import Flask, request, jsonify
from scraper import FravegaScraper, GarbarinoScraper, PerozziScraper

app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    store = request.args.get('store')

    if not query or not store:
        return jsonify({"error": "Both 'query' and 'store' parameters are required"}), 400

    if store.lower() == 'fravega':
        scraper = FravegaScraper(query)
    elif store.lower() == 'garbarino':
        scraper = GarbarinoScraper(query)
    elif store.lower() == 'perozzi':
        scraper = PerozziScraper(query)
