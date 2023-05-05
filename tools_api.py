import json
def save_html_to_file(html_content, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f'Archivo creado')

def scroll_to_bottom(page):
    last_position = -1
    while True:
        current_position = page.evaluate("() => window.pageYOffset")
        if current_position == last_position:
            break
        last_position = current_position
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)



def load_json_file(file_name):
    with open(file_name,'r') as file:
        data = json.load(file)
    return data