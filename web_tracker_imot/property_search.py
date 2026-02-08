import requests
from bs4 import BeautifulSoup

BASE_URL="https://www.imot.bg"
HEADERS= {"User-Agent": "Mozilla/5.0"}

def search_properties(search_url:str, base_url:str, link_selector:str, limit=20) -> list[str]:
    response=requests.get(search_url, headers=HEADERS)
    soup=BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")

    links=[]

    for a in soup.select(link_selector):
        href=a.get("href")

        if href.startswith("//"):
            full_url="https:" + href
        elif href.startswith("/"):
            full_url=base_url + href
        else:
            full_url=href

        full_url=full_url.split("#")[0]

        if full_url not in links:
            links.append(full_url)

        if (len(links)>limit):
            break

    return links