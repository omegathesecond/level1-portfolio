#!/usr/bin/env python3
"""
Scraper pour récupérer la liste des CFA depuis letudiant.fr
puis fusionner avec les données de lapprenti.com
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json

BASE_LIST_URL = "https://www.letudiant.fr/etudes/annuaire-alternance/etablissement/type-etablissement-cfa-centre-de-formation-d-apprentis"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "20": "Corse",
    "2A": "Corse-du-Sud", "2B": "Haute-Corse",
    "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde",
    "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire",
    "38": "Isère", "39": "Jura", "40": "Landes", "41": "Loir-et-Cher",
    "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique", "45": "Loiret",
    "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire",
    "50": "Manche", "51": "Marne", "52": "Haute-Marne", "53": "Mayenne",
    "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan", "57": "Moselle",
    "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire",
    "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort",
    "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion",
    "976": "Mayotte",
}

DEPT_REGIONS = {
    "01": "Auvergne-Rhône-Alpes", "03": "Auvergne-Rhône-Alpes", "07": "Auvergne-Rhône-Alpes",
    "15": "Auvergne-Rhône-Alpes", "26": "Auvergne-Rhône-Alpes", "38": "Auvergne-Rhône-Alpes",
    "42": "Auvergne-Rhône-Alpes", "43": "Auvergne-Rhône-Alpes", "63": "Auvergne-Rhône-Alpes",
    "69": "Auvergne-Rhône-Alpes", "73": "Auvergne-Rhône-Alpes", "74": "Auvergne-Rhône-Alpes",
    "21": "Bourgogne-Franche-Comté", "25": "Bourgogne-Franche-Comté", "39": "Bourgogne-Franche-Comté",
    "58": "Bourgogne-Franche-Comté", "70": "Bourgogne-Franche-Comté", "71": "Bourgogne-Franche-Comté",
    "89": "Bourgogne-Franche-Comté", "90": "Bourgogne-Franche-Comté",
    "22": "Bretagne", "29": "Bretagne", "35": "Bretagne", "56": "Bretagne",
    "18": "Centre-Val de Loire", "28": "Centre-Val de Loire", "36": "Centre-Val de Loire",
    "37": "Centre-Val de Loire", "41": "Centre-Val de Loire", "45": "Centre-Val de Loire",
    "2A": "Corse", "2B": "Corse", "20": "Corse",
    "08": "Grand-Est", "10": "Grand-Est", "51": "Grand-Est", "52": "Grand-Est",
    "54": "Grand-Est", "55": "Grand-Est", "57": "Grand-Est", "67": "Grand-Est", "68": "Grand-Est", "88": "Grand-Est",
    "02": "Hauts-de-France", "59": "Hauts-de-France", "60": "Hauts-de-France",
    "62": "Hauts-de-France", "80": "Hauts-de-France",
    "75": "Ile-de-France", "77": "Ile-de-France", "78": "Ile-de-France",
    "91": "Ile-de-France", "92": "Ile-de-France", "93": "Ile-de-France",
    "94": "Ile-de-France", "95": "Ile-de-France",
    "14": "Normandie", "27": "Normandie", "50": "Normandie", "61": "Normandie", "76": "Normandie",
    "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine", "19": "Nouvelle-Aquitaine",
    "23": "Nouvelle-Aquitaine", "24": "Nouvelle-Aquitaine", "33": "Nouvelle-Aquitaine",
    "40": "Nouvelle-Aquitaine", "47": "Nouvelle-Aquitaine", "64": "Nouvelle-Aquitaine",
    "79": "Nouvelle-Aquitaine", "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
    "09": "Occitanie", "11": "Occitanie", "12": "Occitanie", "30": "Occitanie",
    "31": "Occitanie", "32": "Occitanie", "34": "Occitanie", "46": "Occitanie",
    "48": "Occitanie", "65": "Occitanie", "66": "Occitanie", "81": "Occitanie", "82": "Occitanie",
    "44": "Pays de la Loire", "49": "Pays de la Loire", "53": "Pays de la Loire",
    "72": "Pays de la Loire", "85": "Pays de la Loire",
    "04": "Provence-Alpes-Côte d'Azur", "05": "Provence-Alpes-Côte d'Azur",
    "06": "Provence-Alpes-Côte d'Azur", "13": "Provence-Alpes-Côte d'Azur",
    "83": "Provence-Alpes-Côte d'Azur", "84": "Provence-Alpes-Côte d'Azur",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "La Réunion", "976": "Mayotte",
}


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                time.sleep(5 * (attempt + 1))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  ERREUR: {url}: {e}")
    return None


def get_dept_from_postal(postal_code):
    """Extract department code from postal code."""
    if not postal_code:
        return "", ""
    pc = postal_code.strip()
    if pc.startswith("97"):
        dep = pc[:3]
    elif pc.startswith("20"):
        num = int(pc)
        dep = "2A" if num < 20200 else "2B"
    else:
        dep = pc[:2]
    dep_name = DEPT_NAMES.get(dep, "")
    return dep, dep_name


def parse_listing_article(art):
    """Parse a single article from a listing page."""
    cfa = {}

    # 1. Get name from the favorite button's data-layer-event-lab attribute
    fav_btn = art.find('button', attrs={'data-layer-event-lab': True})
    if fav_btn:
        cfa['name'] = fav_btn.get('data-layer-event-lab', '').strip()

    # 2. Get profile URL - check both /fiches/ and /etablissement/ links
    profile_url = ""
    all_links = art.find_all('a', href=True)
    for a in all_links:
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not text or 'Ajouter' in text or 'favoris' in text.lower():
            continue
        if '/fiches/' in href or '/etablissement/' in href:
            if href.startswith('/'):
                href = 'https://www.letudiant.fr' + href
            profile_url = href
            # If we don't have a name yet, get it from the link text
            if not cfa.get('name') and text:
                cfa['name'] = text
            break

    cfa['profile_url'] = profile_url

    # 3. Status (Public/Privé/Privé sous contrat/Consulaire)
    for p in art.find_all('p'):
        text = p.get_text(strip=True)
        if text in ['Public', 'Privé', 'Privé sous contrat', 'Consulaire']:
            cfa['statut'] = text
            break
    if 'statut' not in cfa:
        cfa['statut'] = ''

    # 4. City - find <p> tags that contain just a city name
    name = cfa.get('name', '')
    for p in art.find_all('p'):
        text = p.get_text(strip=True)
        if (text and
            text not in ['Public', 'Privé', 'Privé sous contrat', 'Consulaire'] and
            text != name and
            not re.match(r'^[\d,]', text) and
            '(' not in text and
            'avis' not in text.lower() and
            len(text) < 60 and len(text) > 1):
            cfa['city'] = text
            break

    if not cfa.get('name'):
        return None

    return cfa


def scrape_listing_pages():
    """Scrape all listing pages to get CFA basic info + profile URLs."""
    all_cfas = []
    total_pages = 43

    for page in range(1, total_pages + 1):
        if page == 1:
            url = f"{BASE_LIST_URL}.html"
        else:
            url = f"{BASE_LIST_URL}/page-{page}.html"

        print(f"  Page {page}/{total_pages}...", end=" ", flush=True)
        html = fetch_page(url)
        if not html:
            print("ERREUR")
            continue

        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.find_all('article', class_='tw-group/gan-card')

        page_count = 0
        for art in articles:
            cfa = parse_listing_article(art)
            if cfa:
                all_cfas.append(cfa)
                page_count += 1

        print(f"{page_count} CFA")
        time.sleep(0.3)

    return all_cfas


def scrape_profile(cfa):
    """Scrape a CFA profile page for detailed info (address, phone)."""
    url = cfa.get('profile_url', '')
    if not url:
        return cfa

    html = fetch_page(url)
    if not html:
        return cfa

    soup = BeautifulSoup(html, 'html.parser')

    # Strategy 1: /etablissement/ pages have address in <ul><li> structure
    # Structure: <ul><li>City</li><li>Street</li><li>PostalCode City</li></ul>
    for ul in soup.find_all('ul'):
        items = ul.find_all('li', recursive=False)
        if len(items) >= 2:
            # Check if one of the items contains a postal code
            for li in items:
                text = li.get_text(strip=True)
                m = re.match(r'^(\d{5})\s+(.+)$', text)
                if m:
                    cfa['postal_code'] = m.group(1)
                    cfa['city_full'] = m.group(2).strip()
                    # Get the address from the previous li
                    idx = items.index(li)
                    if idx > 0:
                        addr_parts = []
                        for j in range(max(0, idx - 2), idx):
                            t = items[j].get_text(strip=True)
                            # Skip if it's just the city name repeated
                            if t and t != cfa.get('city_full', '') and t != cfa.get('city', ''):
                                addr_parts.append(t)
                        cfa['address'] = ', '.join(addr_parts) if addr_parts else ''
                    break
            if cfa.get('postal_code'):
                break

    # Strategy 2: /fiches/ pages have address in <p class="tw-mb-4 ... lg:tw-text-2xl">
    if not cfa.get('postal_code'):
        for p in soup.find_all('p', class_=lambda c: c and 'lg:tw-text-2xl' in c):
            text = p.get_text(strip=True)
            m = re.search(r'(\d{5})\s+(.+?)$', text)
            if m:
                cfa['postal_code'] = m.group(1)
                cfa['city_full'] = m.group(2).strip()
                cfa['address'] = text[:m.start()].strip().rstrip('-').rstrip(',').strip()
                break

    # Phone number
    for a in soup.find_all('a', href=re.compile(r'tel:')):
        phone_raw = a.get('href', '').replace('tel:', '').strip()
        phone_text = a.get_text(strip=True)
        phone = phone_text if phone_text else phone_raw
        if phone and len(phone) >= 10:
            # Format phone number
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) == 10:
                phone = f"{phone[0:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]} {phone[8:10]}"
            cfa['phone'] = phone
            break

    return cfa


def main():
    print("=" * 60)
    print("ÉTAPE 1: Scraping des pages de listing letudiant.fr")
    print("=" * 60)
    cfas = scrape_listing_pages()
    print(f"\nTotal CFA trouvés dans les listings: {len(cfas)}")

    print("\n" + "=" * 60)
    print("ÉTAPE 2: Scraping des fiches individuelles (adresses)")
    print("=" * 60)

    total = len(cfas)
    for i, cfa in enumerate(cfas, 1):
        if i % 50 == 0 or i == total:
            print(f"  Progression: {i}/{total} ({i*100//total}%)")
        scrape_profile(cfa)
        time.sleep(0.3)

    # Enrich with department info
    for cfa in cfas:
        pc = cfa.get('postal_code', '')
        if pc:
            dep_code, dep_name = get_dept_from_postal(pc)
            cfa['dep_code'] = dep_code
            cfa['dep_name'] = dep_name
            cfa['region'] = DEPT_REGIONS.get(dep_code, '')
        else:
            cfa['dep_code'] = ''
            cfa['dep_name'] = ''
            cfa['region'] = ''

    # Save
    output_path = "/home/user/level1-portfolio/liste_cfa_letudiant.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cfas, f, ensure_ascii=False, indent=2)
    print(f"\nFichier JSON sauvegardé: {output_path}")

    # Stats
    with_address = sum(1 for c in cfas if c.get('postal_code'))
    with_phone = sum(1 for c in cfas if c.get('phone'))
    print(f"Total: {len(cfas)} CFA")
    print(f"Avec adresse complète: {with_address}")
    print(f"Avec téléphone: {with_phone}")

    # Examples
    print("\n=== Exemples ===")
    for c in cfas[:10]:
        print(f"  {c.get('name', '?')[:50]} | {c.get('statut', '?')} | {c.get('address', '')[:30]} | {c.get('postal_code', '?')} {c.get('city_full', c.get('city', '?'))} | Tel: {c.get('phone', '-')}")


if __name__ == "__main__":
    main()
