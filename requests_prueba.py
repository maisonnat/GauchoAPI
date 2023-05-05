import requests
from bs4 import BeautifulSoup

def fetch_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error al obtener la página: {response.status_code}")
        return None

url = 'https://www.garbarino.com/celular%20samsung%20galaxy%20a23?_q=celular%20samsung%20galaxy%20a23&map=ft'
html = fetch_page_content(url)

if html:
    soup = BeautifulSoup(html, 'html.parser')
    container = soup.find('section', {'class': 'vtex-product-summary-2-x-container'})

    if container:
        print(container.prettify())
    else:
        print("No se encontró el elemento especificado.")
else:
    print("No se pudo obtener el contenido de la página.")
