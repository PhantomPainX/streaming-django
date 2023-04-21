import requests
from bs4 import BeautifulSoup

def ultimas_noticias():

    url = "https://somoskudasai.com/categoria/noticias/anime/"
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    ultimas_noticias = []
    for ultima_noticia in soup.find_all('article', class_='ar por'):
        titulo = ultima_noticia.find('header').find('h2').text
        tipo = ultima_noticia.find('header').find('span').text
        fecha = ultima_noticia.find('header').find('div', class_='ar-mt').find('span').text
        imagen = ultima_noticia.find('figure').find('img').get('src')
        url_page = ultima_noticia.find('a').get('href')

        ultimas_noticias.append({
            'titulo': titulo,
            'tipo': tipo,
            'fecha': fecha,
            'imagen': imagen,
            'url_page': url_page
        })

    return ultimas_noticias

        