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
        "hommes": {
            "chaussures": "https://www.adidas.fr/chaussures-hommes",
            "vetements": "https://www.adidas.fr/vetements-hommes",
            "accessoires": "https://www.adidas.fr/accessoires-hommes",
        },
        "femmes": {
            "chaussures": "https://www.adidas.fr/chaussures-femmes",
            "vetements": "https://www.adidas.fr/vetements-femmes",
            "accessoires": "https://www.adidas.fr/accessoires-femmes",
        }
    },
    "us": {
        "hommes": {
            "chaussures": "https://www.adidas.com/us/shoes-men",
            "vetements": "https://www.adidas.com/us/clothing-men",
            "accessoires": "https://www.adidas.com/us/accessories-men",
        },
        "femmes": {
            "chaussures": "https://www.adidas.com/us/shoes-women",
            "vetements": "https://www.adidas.com/us/clothing-women",
            "accessoires": "https://www.adidas.com/us/accessories-women",
        }
    },
    "uk": {
        "hommes": {
            "chaussures": "https://www.adidas.co.uk/shoes-men",
            "vetements": "https://www.adidas.co.uk/clothing-men",
            "accessoires": "https://www.adidas.co.uk/accessories-men",
        },
        "femmes": {
            "chaussures": "https://www.adidas.co.uk/shoes-women",
            "vetements": "https://www.adidas.co.uk/clothing-women",
            "accessoires": "https://www.adidas.co.uk/accessories-women",
        }
    },
}

def get_soup(url):
    print(f"📥 Requête vers {url}")
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.encoding = 'utf-8'
    return BeautifulSoup(response.text, "html.parser")

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

    # lire les existants
    existing_links = set()
    if os.path.exists(output_path + "_links.txt"):
        with open(output_path + "_links.txt", "r", encoding="utf-8") as f:
            existing_links.update(line.strip() for line in f)

    with open(output_path + "_links.txt", "a", encoding="utf-8") as f_link, \
         open(output_path + "_codes.txt", "a", encoding="utf-8") as f_code:
        for link, code in zip(links, codes):
            if link not in existing_links:
                f_link.write(link + "\n")
                f_code.write(code + "\n")

    print(f"✅ {len(links)} liens traités pour {output_path}")

def scrape_all():
    for country, genders in URL_MAP.items():
        for gender, categories in genders.items():
            for category, base_url in categories.items():
                soup = get_soup(base_url)
                max_pages = get_max_pages(soup)
                if not max_pages:
                    print(f"⚠️ Aucune pagination détectée pour {base_url}")
                    continue

                all_links = []
                for page in range(1, max_pages + 1):
                    start = (page - 1) * STEP
                    paged_url = base_url + f"?start={start}" if start else base_url
                    soup = get_soup(paged_url)
                    page_links = extract_links(soup)
                    print(f"🔗 {len(page_links)} liens trouvés page {page}/{max_pages} [{country}/{gender}/{category}]")
                    all_links.extend(page_links)
                    time.sleep(1)

                output_base = f"adidas_data/{country}/{gender}/{category}"
                save_links_codes(all_links, output_base)

if __name__ == "__main__":
    scrape_all()
