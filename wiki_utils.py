# wiki_utils.py
import requests
from bs4 import BeautifulSoup

WIKI_API = "https://en.wikipedia.org/w/api.php"

def fetch_wikipedia_list(page_title: str) -> list[str]:
    """Fetch the rendered HTML of a Wikipedia page and
       return every top-level <li> as a Python list of strings."""
    resp = requests.get(
        WIKI_API,
        params={
            "action": "parse",
            "page": page_title,
            "format": "json",
            "prop": "text"
        },
        headers={"User-Agent": "Guess.ai Quiz/1.0"}
    )
    resp.raise_for_status()
    html = resp.json()["parse"]["text"]["*"]

    soup = BeautifulSoup(html, "html.parser")
    items = []
    # grab only top-level list items (you can adjust the selector if you need tables)
    for li in soup.select("ul > li"):
        text = li.get_text().split("–")[0].strip()
        if text:
            items.append(text)
    return items

