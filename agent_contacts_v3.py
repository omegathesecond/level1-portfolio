#!/usr/bin/env python3
"""
Agent d'enrichissement contacts CFA/OF v3.
Utilise DuckDuckGo pour trouver les vrais sites web,
puis extrait emails/tels publics par scraping.
"""

import requests
import csv
import json
import re
import time
import sys
import unicodedata
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False
    print("WARN: duckduckgo_search non disponible", file=sys.stderr)

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
API_BASE = "https://recherche-entreprises.api.gouv.fr/search"
OUTPUT = "/home/user/level1-portfolio/liste_contacts_cfa.csv"

# Domaines à ignorer dans les résultats de recherche
SKIP_DOMAINS = {
    "annuaire-entreprises.data.gouv.fr", "societe.com", "pappers.fr",
    "verif.com", "infogreffe.fr", "bodacc.fr", "sirene.fr",
    "manageo.fr", "score3.fr", "dirigeant.societe.com",
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "tiktok.com", "pinterest.com",
    "pagesjaunes.fr", "wikipedia.org", "wikidata.org",
    "google.com", "google.fr", "bing.com",
    "indeed.fr", "indeed.com", "pole-emploi.fr", "emploi-store.fr",
    "legalstart.fr", "legalplace.fr", "guichet-entreprises.fr",
    "economie.gouv.fr", "service-public.fr",
    "amazon.fr", "amazon.com", "ebay.fr",
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self._skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False
    def handle_data(self, data):
        if not self._skip:
            self.texts.append(data)
    def get_text(self):
        return " ".join(self.texts)


def extract_emails(text):
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    blocked = ["example.com", "sentry", "wixpress", "w3.org", "schema.org",
               "google", "gstatic", "jquery", "bootstrap", "wordpress",
               ".png", ".jpg", ".gif", ".svg", ".css", ".js", "webpack",
               "cloudflare", "facebook", "twitter", "instagram", "protection",
               "sentry.io", "gravatar", "unsplash", "placeholder", "test@"]
    return list(set(e.lower() for e in emails if not any(b in e.lower() for b in blocked)))


def extract_phones(text):
    patterns = [
        r'(?:0|\+33\s?|0033\s?)[1-9](?:[\s.\-]?\d{2}){4}',
        r'(?:0|\+33)[1-9]\d{8}',
    ]
    phones = []
    for pat in patterns:
        for m in re.findall(pat, text):
            clean = re.sub(r'[\s.\-]', '', m)
            if clean.startswith('+33'): clean = '0' + clean[3:]
            elif clean.startswith('0033'): clean = '0' + clean[4:]
            if len(clean) == 10 and clean.startswith('0'):
                formatted = f"{clean[:2]} {clean[2:4]} {clean[4:6]} {clean[6:8]} {clean[8:10]}"
                phones.append(formatted)
    return list(set(phones))


def fetch(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""


def is_valid_site(url):
    """Vérifie que l'URL n'est pas un annuaire/répertoire."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    return domain not in SKIP_DOMAINS


def search_website_ddg(nom, ville):
    """Cherche le site web officiel via DuckDuckGo."""
    if not HAS_DDG:
        return ""

    queries = [
        f'"{nom}" {ville} site officiel',
        f'"{nom}" contact email',
        f'{nom} {ville}',
    ]

    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="fr-fr", max_results=5))
            for r in results:
                url = r.get("href", "")
                if is_valid_site(url):
                    return url
            time.sleep(1.0)
        except Exception as e:
            time.sleep(2.0)
            continue

    return ""


def find_real_website(nom, siren, ville):
    """Cherche le vrai site web d'un CFA via multiple méthodes."""

    # Méthode 1: API annuaire-entreprises
    try:
        url = f"https://annuaire-entreprises.data.gouv.fr/api/entreprise/{siren}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            site = data.get("site_web") or data.get("url") or ""
            if site and is_valid_site(site):
                return site
    except:
        pass

    # Méthode 2: Recherche DuckDuckGo
    site = search_website_ddg(nom, ville)
    if site:
        return site

    # Méthode 3: Constructions courantes de domaines
    nom_clean = re.sub(r'[^a-z0-9\s]', '', nom.lower())
    parts = nom_clean.split()

    attempts = []
    if "cfa" in nom.lower():
        cfa_parts = [p for p in parts if p != "cfa"]
        if cfa_parts:
            slug = "-".join(cfa_parts[:3])
            attempts.extend([
                f"https://www.cfa-{slug}.fr",
                f"https://cfa-{slug}.fr",
                f"https://www.{slug}-cfa.fr",
            ])

    # Essayer les variantes
    for attempt_url in attempts[:4]:
        try:
            r = requests.head(attempt_url, headers=HEADERS, timeout=5, allow_redirects=True)
            if r.status_code < 400:
                return attempt_url
        except:
            continue

    return ""


def scrape_contacts(url):
    """Scrape un site web pour trouver emails et téléphones."""
    result = {"emails": [], "phones": [], "all_text": ""}

    if not url:
        return result

    base = url.rstrip("/")
    # Nettoyer l'URL de base (garder juste le domaine)
    parsed = urlparse(base)
    root = f"{parsed.scheme}://{parsed.netloc}"

    pages = [
        base,
        root + "/contact",
        root + "/contact/",
        root + "/nous-contacter",
        root + "/contactez-nous",
        root + "/equipe",
        root + "/notre-equipe",
        root + "/a-propos",
        root + "/qui-sommes-nous",
        root + "/mentions-legales",
    ]

    all_html = ""
    all_text = ""

    for page in pages:
        html = fetch(page, timeout=6)
        if html:
            all_html += html
            try:
                ext = TextExtractor()
                ext.feed(html)
                all_text += " " + ext.get_text()
            except:
                pass
        time.sleep(0.15)

    # Extraire emails (y compris mailto:)
    mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', all_html)
    result["emails"] = list(set(extract_emails(all_text + " " + " ".join(mailto))))

    # Extraire téléphones (y compris tel:)
    tel_links = re.findall(r'tel:([+0-9\s.\-]+)', all_html)
    phones_from_links = []
    for t in tel_links:
        phones_from_links.extend(extract_phones(t))
    result["phones"] = list(set(extract_phones(all_text) + phones_from_links))

    result["all_text"] = all_text[:5000]

    return result


def get_dirigeants(siren):
    """Récupère les dirigeants depuis l'API."""
    try:
        r = requests.get(f"{API_BASE}?q={siren}&page=1&per_page=1", timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                contacts = []
                for d in results[0].get("dirigeants", []):
                    if d.get("type_dirigeant") == "personne physique":
                        nom = d.get("nom", "") or ""
                        prenoms = d.get("prenoms", "") or ""
                        qualite = d.get("qualite", "") or ""
                        full = f"{prenoms.split()[0].capitalize()} {nom.capitalize()}" if prenoms else nom.capitalize()
                        contacts.append({"nom": full, "role": qualite})
                return contacts
    except:
        pass
    return []


def guess_emails(nom, domain):
    """Génère des patterns d'email possibles."""
    if not nom or not domain:
        return []
    def clean(s):
        return ''.join(c for c in unicodedata.normalize('NFKD', s.lower()) if not unicodedata.combining(c))
    parts = nom.strip().split()
    if len(parts) < 2:
        return []
    p, n = clean(parts[0]), clean(parts[-1])
    return [f"{p}.{n}@{domain}", f"{p[0]}.{n}@{domain}", f"{p}{n}@{domain}", f"contact@{domain}"]


def classify_email(email):
    """Classify an email as general, direction, partenariat, pedagogique."""
    e = email.lower()
    if any(x in e for x in ["partenariat", "partenaire", "commercial", "business", "entreprise", "btob", "b2b"]):
        return "partenariats"
    elif any(x in e for x in ["pedagog", "formation", "enseignement", "cours", "education", "academic"]):
        return "pedagogique"
    elif any(x in e for x in ["direction", "directeur", "directrice", "dg", "president", "gerant"]):
        return "direction"
    elif any(x in e for x in ["contact", "info", "accueil", "admin", "secretariat", "communication"]):
        return "general"
    else:
        return "other"


def process(row):
    """Traite un CFA/OF et cherche ses contacts."""
    siren = row.get("siren", "")
    nom = row.get("organisation_nom", "")
    ville = row.get("adresse_ville", "")

    res = {
        "persona": row.get("persona", ""),
        "siren": siren,
        "organisation_nom": nom,
        "organisation_nom_legal": row.get("organisation_nom_legal", ""),
        "adresse_ville": ville,
        "adresse_departement": row.get("adresse_departement", ""),
        "adresse_region": row.get("adresse_region", ""),
        "type_structure": row.get("type_structure", ""),
        "site_web_officiel": "",
        "dirigeant_nom": "", "dirigeant_role": "", "dirigeant_email": "", "dirigeant_tel": "",
        "dirigeant_source": "",
        "resp_partenariats_nom": "", "resp_partenariats_email": "", "resp_partenariats_tel": "",
        "resp_pedagogique_nom": "", "resp_pedagogique_email": "", "resp_pedagogique_tel": "",
        "email_general": "", "tel_general": "",
        "emails_trouves": "", "tels_trouves": "",
        "emails_patterns_suggeres": "",
        "source_enrichissement": "", "notes": "",
    }

    sources = []

    # 1. Dirigeants API
    dirigeants = get_dirigeants(siren) if siren else []
    if dirigeants:
        res["dirigeant_nom"] = dirigeants[0]["nom"]
        res["dirigeant_role"] = dirigeants[0]["role"]
        res["dirigeant_source"] = "Registre légal (API)"
        sources.append("API registre")
    elif row.get("contact_nom"):
        res["dirigeant_nom"] = row["contact_nom"]
        res["dirigeant_role"] = row.get("contact_role", "")
        res["dirigeant_source"] = "CSV initial"

    # 2. Trouver le vrai site web
    real_site = find_real_website(nom, siren, ville)
    if real_site:
        res["site_web_officiel"] = real_site
        sources.append("Site web trouvé")

        # 3. Scraper le site
        web = scrape_contacts(real_site)
        if web["emails"]:
            res["emails_trouves"] = " | ".join(web["emails"][:5])
            # Classifier les emails
            classified = {}
            for e in web["emails"]:
                cat = classify_email(e)
                if cat not in classified:
                    classified[cat] = e

            res["email_general"] = classified.get("general", "")
            if not res["email_general"] and "other" in classified:
                res["email_general"] = classified["other"]

            if "direction" in classified:
                res["dirigeant_email"] = classified["direction"]
            elif "other" in classified and res["email_general"] != classified.get("other", ""):
                res["dirigeant_email"] = classified["other"]

            if "partenariats" in classified:
                res["resp_partenariats_email"] = classified["partenariats"]
            if "pedagogique" in classified:
                res["resp_pedagogique_email"] = classified["pedagogique"]

            sources.append(f"{len(web['emails'])} emails")

        if web["phones"]:
            res["tels_trouves"] = " | ".join(web["phones"][:5])
            res["tel_general"] = web["phones"][0]
            if len(web["phones"]) > 1:
                res["dirigeant_tel"] = web["phones"][1]
            sources.append(f"{len(web['phones'])} tels")

    # 4. Patterns d'email suggérés
    domain = ""
    if res["site_web_officiel"]:
        domain = urlparse(res["site_web_officiel"]).netloc.replace("www.", "")
    elif res["email_general"]:
        domain = res["email_general"].split("@")[1] if "@" in res["email_general"] else ""

    if domain and res["dirigeant_nom"]:
        patterns = guess_emails(res["dirigeant_nom"], domain)
        res["emails_patterns_suggeres"] = " | ".join(patterns)

    res["source_enrichissement"] = " + ".join(sources) if sources else "API registre uniquement"

    return res


def main():
    print("=" * 60, file=sys.stderr)
    print("AGENT CONTACTS CFA/OF v3 (avec DuckDuckGo)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    all_rows = []
    for path in ["/home/user/level1-portfolio/liste_a_actifs.csv",
                 "/home/user/level1-portfolio/liste_b_difficulte.csv"]:
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                all_rows.append(row)

    print(f"Total: {len(all_rows)} CFA/OF", file=sys.stderr)
    print(f"DuckDuckGo: {'disponible' if HAS_DDG else 'NON disponible'}", file=sys.stderr)

    results = []
    for i, row in enumerate(all_rows):
        nom = row.get('organisation_nom', '')[:45]
        print(f"  [{i+1}/{len(all_rows)}] {row.get('persona','')} | {nom} | {row.get('siren','')}", file=sys.stderr, end="")
        r = process(row)
        results.append(r)

        # Afficher résultat inline
        found = []
        if r["site_web_officiel"]: found.append("WEB")
        if r["email_general"]: found.append("EMAIL")
        if r["tel_general"]: found.append("TEL")
        print(f" -> {', '.join(found) if found else '-'}", file=sys.stderr)

        time.sleep(0.1)
        if (i+1) % 25 == 0:
            e = sum(1 for x in results if x["email_general"])
            t = sum(1 for x in results if x["tel_general"])
            s = sum(1 for x in results if x["site_web_officiel"])
            print(f"    => {s} sites, {e} emails, {t} tels trouvés jusqu'ici", file=sys.stderr)

    # Écriture CSV
    fields = [
        "persona", "siren", "organisation_nom", "organisation_nom_legal",
        "adresse_ville", "adresse_departement", "adresse_region", "type_structure",
        "site_web_officiel",
        "dirigeant_nom", "dirigeant_role", "dirigeant_email", "dirigeant_tel", "dirigeant_source",
        "resp_partenariats_nom", "resp_partenariats_email", "resp_partenariats_tel",
        "resp_pedagogique_nom", "resp_pedagogique_email", "resp_pedagogique_tel",
        "email_general", "tel_general",
        "emails_trouves", "tels_trouves",
        "emails_patterns_suggeres",
        "source_enrichissement", "notes"
    ]

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)

    # Stats finales
    print("\n" + "=" * 60, file=sys.stderr)
    print("STATISTIQUES FINALES", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    total = len(results)
    d = sum(1 for x in results if x["dirigeant_nom"])
    s = sum(1 for x in results if x["site_web_officiel"])
    e = sum(1 for x in results if x["email_general"])
    t = sum(1 for x in results if x["tel_general"])
    de = sum(1 for x in results if x["dirigeant_email"])
    p = sum(1 for x in results if x["emails_patterns_suggeres"])

    print(f"Total: {total}", file=sys.stderr)
    print(f"Dirigeants identifiés: {d} ({d*100//total}%)", file=sys.stderr)
    print(f"Sites web officiels: {s} ({s*100//total}%)", file=sys.stderr)
    print(f"Emails généraux: {e} ({e*100//total}%)", file=sys.stderr)
    print(f"Tels généraux: {t} ({t*100//total}%)", file=sys.stderr)
    print(f"Emails dirigeants: {de}", file=sys.stderr)
    print(f"Patterns email suggérés: {p}", file=sys.stderr)
    print(f"\nFichier: {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
