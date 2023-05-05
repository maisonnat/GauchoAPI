from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/search/<search_query>', methods=['GET'])
def search_products(search_query):
    #here code to web scraping and save the data in to data base
    ...


if __name__ == '__main__':
    app.run(debug=True)