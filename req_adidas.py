import os
import json
import requests
from pathlib import Path
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
from tqdm import tqdm  # Importation de tqdm pour la barre de chargement

# Chemins
BASE_INPUT = Path("adidas_data")
BASE_OUTPUT = Path("adidas_products")
IMAGES_DIR = BASE_OUTPUT / "images"

# Création des dossiers nécessaires
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Headers pour requête vers l'API produit
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

BASE_API_URL = "https://www.adidas.fr/plp-app/api/product/"

CATEGORY_TRANSLATIONS = {
    "vetements": "clothing",
    "chaussures": "shoes",
    "accessoires": "accessories"
}

CURRENCY_BY_COUNTRY = {
    "fr": "EUR",
    "us": "USD",
    "uk": "GBP"
}

def sanitize_filename(name):
    return name.replace("/", "_").replace("\\", "_").replace("?", "_").replace("&", "_")

def download_image(url, local_path):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            img.save(local_path)
            print(f"🖼️ Image téléchargée : {local_path}")
        else:
            print(f"❌ Erreur image {url}: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception image {url}: {e}")

def process_product(code, country, gender, category):
    json_output_path = BASE_OUTPUT / country / gender / f"{code}.json"

    url = BASE_API_URL + code
    print(f"🔎 Traitement du produit : {code} ({country}/{gender}/{category})")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"❌ Requête échouée pour {code} : {response.status_code}")
            return

        data = response.json()
        product = data.get("product", {})

        product_id = product.get("id")
        name = product.get("title")
        url_suffix = product.get("url")
        full_url = f"https://www.adidas.{country}/{url_suffix.lstrip('/')}"
        image_main = product.get("image")
        image_hover = product.get("hoverImage")

        price_data = product.get("priceData", {})
        current_price = price_data.get("salePrice", price_data.get("price"))
        original_price = price_data.get("price")
        is_discount = current_price != original_price

        translated_category = CATEGORY_TRANSLATIONS.get(category, category)
        currency = CURRENCY_BY_COUNTRY.get(country, "EUR")

        output = {
            "id": product_id,
            "name": name,
            "brand": "adidas",
            "color": "",
            "category": translated_category,
            "section": gender,
            "country": country,
            "price": {
                "value_original": original_price,
                "current_price": current_price,
                "is_Discount": is_discount,
                "currency": currency
            },
            "url": full_url,
            "product_code": product_id,
            "images": []
        }

        img_dir = IMAGES_DIR / product_id
        img_dir.mkdir(parents=True, exist_ok=True)

        if image_main:
            local_main = img_dir / "main.jpg"
            download_image(image_main, str(local_main))
            output["images"].append({
                "type": "main",
                "url": image_main,
                "local_path": str(local_main).replace("\\", "/")
            })

        if image_hover:
            local_hover = img_dir / "hover.jpg"
            download_image(image_hover, str(local_hover))
            output["images"].append({
                "type": "hover",
                "url": image_hover,
                "local_path": str(local_hover).replace("\\", "/")
            })

        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        print(f"✅ Données sauvegardées : {json_output_path}")

    except Exception as e:
        print(f"❌ Exception pour {code} : {e}")

def run_all(test_mode=False):
    for country_dir in BASE_INPUT.iterdir():
        if not country_dir.is_dir():
            continue
        country = country_dir.name

        for gender_dir in country_dir.iterdir():
            if not gender_dir.is_dir():
                continue
            gender = gender_dir.name

            for file in gender_dir.glob("*_codes.txt"):
                category = file.stem.replace("_codes", "")
                print(f"📁 Lecture fichier : {file}")
                with open(file, "r", encoding="utf-8") as f:
                    codes = [line.strip() for line in f if line.strip()]

                # Ajout de la barre de chargement avec tqdm
                total_codes = len(codes)
                if test_mode:
                    codes = codes[:100]  # Limite à 100 produits pour le test

                print(f"📊 Traitement des produits {category} ({len(codes)} codes)")
                for code in tqdm(codes, desc=f"{country} / {gender} / {category}", ncols=100):
                    process_product(code, country, gender, category)

if __name__ == "__main__":
    run_all(test_mode=False)  # Passer test_mode=True pour tester sur 100 produits
