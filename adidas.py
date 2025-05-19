import requests
from bs4 import BeautifulSoup
import os
import time

STEP = 48
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edge/123.0.0.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.adidas.fr/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "Pragma": "no-cache",
    "DNT": "1",
}

URL_MAP = {
    "fr": {
        "mens": {
            "shoes": "https://www.adidas.fr/chaussures-hommes",
            "clothes": "https://www.adidas.fr/vetements-hommes",
            "accessories": "https://www.adidas.fr/accessoires-hommes",
        },
        "womens": {
            "shoes": "https://www.adidas.fr/chaussures-femmes",
            "clothes": "https://www.adidas.fr/vetements-femmes",
            "accessories": "https://www.adidas.fr/accessoires-femmes",
        }
    },
    "us": {
        "mens": {
            "shoes": "https://www.adidas.com/us/shoes-men",
            "clothes": "https://www.adidas.com/us/clothing-men",
            "accessories": "https://www.adidas.com/us/accessories-men",
        },
        "womens": {
            "shoes": "https://www.adidas.com/us/shoes-women",
            "clothes": "https://www.adidas.com/us/clothing-women",
            "accessories": "https://www.adidas.com/us/accessories-women",
        }
    },
    "uk": {
        "mens": {
            "shoes": "https://www.adidas.co.uk/shoes-men",
            "clothes": "https://www.adidas.co.uk/clothing-men",
            "accessories": "https://www.adidas.co.uk/accessories-men",
        },
        "womens": {
            "shoes": "https://www.adidas.co.uk/shoes-women",
            "clothes": "https://www.adidas.co.uk/clothing-women",
            "accessories": "https://www.adidas.co.uk/accessories-women",
        }
    },
}

def get_soup(url, retries=3, timeout=10, backoff=2):
    for attempt in range(1, retries + 1):
        try:
            print(f"📥 Requête vers {url} (tentative {attempt}/{retries})")
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.ReadTimeout:
            print(f"⏳ Timeout sur {url}, tentative {attempt}/{retries}...")
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ Erreur connexion sur {url} : {e}, tentative {attempt}/{retries}...")
        if attempt < retries:
            time.sleep(backoff * attempt)
    print(f"❌ Échec après {retries} tentatives pour {url}")
    return None

def get_max_pages(soup):
    page_indicator = soup.find("div", {"class": "pagination_progress-bar__sWWOn"})
    if page_indicator:
        style = page_indicator.get("style", "")
        if "--page-count" in style:
            try:
                return int(style.split("--page-count:")[1].split(";")[0].strip())
            except ValueError:
                return None
    return None

def extract_links(soup):
    links = []
    product_divs = soup.find_all("div", class_="product-card_product-card-content___bjeq")
    for div in product_divs:
        header = div.find("header", {"data-testid": "product-card-assets"})
        if header:
            a_tag = header.find("a", href=True)
            if a_tag:
                links.append("https://www.adidas.fr" + a_tag["href"])
    return links

def save_links_codes(links, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    codes = [link.replace('.', '/').split('/')[-2] for link in links]

    with open(output_path + "_links.txt", "a", encoding="utf-8") as f_link, \
         open(output_path + "_codes.txt", "a", encoding="utf-8") as f_code:
        for link, code in zip(links, codes):
            print(f"➕ Ajout : {code}")
            f_link.write(link + "\n")
            f_code.write(code + "\n")

    print(f"📦 {len(links)} liens ajoutés (doublons inclus)")

def scrape_all():
    for country, genders in URL_MAP.items():
        for gender, categories in genders.items():
            for category, base_url in categories.items():
                print(f"\n🚀 Scraping {country}/{gender}/{category}")
                soup = get_soup(base_url)
                if soup is None:
                    print(f"⛔️ Impossible de récupérer la page {base_url}, passage à la suivante.")
                    continue
                max_pages = get_max_pages(soup)

                if not max_pages:
                    print(f"⚠️ Aucune pagination détectée pour {base_url}")
                    continue

                all_links = []
                for page in range(max_pages):
                    start = page * STEP
                    paged_url = base_url if start == 0 else f"{base_url}?start={start}"
                    soup = get_soup(paged_url)
                    if soup is None:
                        print(f"⛔️ Impossible de récupérer la page {paged_url}, passage à la suivante.")
                        continue
                    page_links = extract_links(soup)
                    print(f"🔗 {len(page_links)} liens trouvés page {page + 1}/{max_pages}")
                    all_links.extend(page_links)
                    time.sleep(1)

                output_base = f"adidas_data/{country}/{gender}/{category}"
                save_links_codes(all_links, output_base)

if __name__ == "__main__":
    scrape_all()
