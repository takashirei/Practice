import requests
from bs4 import BeautifulSoup


def get_lyrics_azlyrics(song_name: str):
    search_url = "https://search.azlyrics.com/search.php?q=" + song_name
    results = requests.get(search_url)
    html = BeautifulSoup(results.text, "html.parser")
    if html.body.tr is None:
        return "Sorry we don't have text for this track :("
    url = html.body.tr.a["href"]
    lyrics_page = BeautifulSoup(requests.get(url).text, "html.parser")
    lyrics = lyrics_page.find("div", class_=None, id=None)
    return lyrics.get_text()
