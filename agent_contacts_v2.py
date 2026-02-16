#!/usr/bin/env python3
"""
Agent d'enrichissement contacts CFA/OF v2.
Recherche les vrais sites web puis extrait emails/tels publics.
"""

import requests
import csv
import json
import re
import time
import sys
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
API_BASE = "https://recherche-entreprises.api.gouv.fr/search"
OUTPUT = "/home/user/level1-portfolio/liste_contacts_cfa.csv"


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
               "cloudflare", "facebook", "twitter", "instagram"]
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


def find_real_website(nom, siren, ville):
    """Cherche le vrai site web d'un CFA via l'annuaire-entreprises API."""
    # Méthode 1: Chercher via l'API si elle retourne un site web
    try:
        url = f"https://annuaire-entreprises.data.gouv.fr/api/entreprise/{siren}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            site = data.get("site_web") or data.get("url") or ""
            if site and "annuaire" not in site:
                return site
    except:
        pass

    # Méthode 2: Essayer des constructions courantes
    nom_clean = nom.lower().replace(" ", "").replace("'", "").replace("(", "").replace(")", "")
    nom_parts = nom.lower().split()

    # Essayer quelques variantes de domaines
    attempts = []
    if "cfa" in nom.lower():
        cfa_name = nom.lower().replace("cfa ", "").replace(" cfa", "").strip()
        cfa_name_slug = cfa_name.replace(" ", "-").replace("'", "")
        attempts.extend([
            f"https://www.cfa-{cfa_name_slug}.fr",
            f"https://www.{cfa_name_slug}-cfa.fr",
            f"https://cfa-{cfa_name_slug}.fr",
        ])

    for attempt_url in attempts[:3]:
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

    # Pages à vérifier
    base = url.rstrip("/")
    pages = [
        base,
        base + "/contact",
        base + "/contact/",
        base + "/nous-contacter",
        base + "/equipe",
        base + "/notre-equipe",
        base + "/a-propos",
        base + "/mentions-legales",
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
        time.sleep(0.2)

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
                        nom = d.get("nom", "")
                        prenoms = d.get("prenoms", "")
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
    import unicodedata
    def clean(s):
        return ''.join(c for c in unicodedata.normalize('NFKD', s.lower()) if not unicodedata.combining(c))
    parts = nom.strip().split()
    if len(parts) < 2:
        return []
    p, n = clean(parts[0]), clean(parts[-1])
    return [f"{p}.{n}@{domain}", f"{p[0]}.{n}@{domain}", f"{p}{n}@{domain}", f"contact@{domain}"]


def process(row):
    """Traite un CFA/OF et cherche ses contacts."""
    siren = row.get("siren", "")
    nom = row.get("organisation_nom", "")
    ville = row.get("adresse_ville", "")
    site_csv = row.get("site_web_url", "")

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
            gen = [e for e in web["emails"] if any(x in e for x in ["contact", "info", "accueil", "direction", "admin", "secretariat"])]
            perso = [e for e in web["emails"] if e not in gen]
            res["email_general"] = gen[0] if gen else (perso[0] if perso else "")
            if perso and gen:
                res["dirigeant_email"] = perso[0]
            sources.append(f"{len(web['emails'])} emails")

        if web["phones"]:
            res["tels_trouves"] = " | ".join(web["phones"][:5])
            res["tel_general"] = web["phones"][0]
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
    print("AGENT CONTACTS CFA/OF v2", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    all_rows = []
    for path in ["/home/user/level1-portfolio/liste_a_actifs.csv",
                 "/home/user/level1-portfolio/liste_b_difficulte.csv"]:
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                all_rows.append(row)

    print(f"Total: {len(all_rows)} CFA/OF", file=sys.stderr)

    results = []
    for i, row in enumerate(all_rows):
        print(f"  [{i+1}/{len(all_rows)}] {row.get('persona','')} | {row.get('organisation_nom','')[:45]} | {row.get('siren','')}", file=sys.stderr)
        r = process(row)
        results.append(r)
        time.sleep(0.15)
        if (i+1) % 25 == 0:
            # Stats intermédiaires
            e = sum(1 for x in results if x["email_general"])
            t = sum(1 for x in results if x["tel_general"])
            print(f"    => {e} emails, {t} tels trouvés jusqu'ici", file=sys.stderr)

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
    rp = sum(1 for x in results if x["resp_partenariats_nom"])
    rpd = sum(1 for x in results if x["resp_pedagogique_nom"])

    print(f"Total: {total}", file=sys.stderr)
    print(f"Dirigeants identifiés: {d} ({d*100//total}%)", file=sys.stderr)
    print(f"Sites web officiels: {s} ({s*100//total}%)", file=sys.stderr)
    print(f"Emails généraux: {e} ({e*100//total}%)", file=sys.stderr)
    print(f"Tels généraux: {t} ({t*100//total}%)", file=sys.stderr)
    print(f"Emails dirigeants: {de}", file=sys.stderr)
    print(f"Resp. partenariats: {rp}", file=sys.stderr)
    print(f"Resp. pédagogiques: {rpd}", file=sys.stderr)
    print(f"Patterns email suggérés: {p}", file=sys.stderr)
    print(f"\nFichier: {OUTPUT}", file=sys.stderr)

    print("\n--- RECOMMANDATION ---", file=sys.stderr)
    print("Pour trouver les Responsables partenariats et pédagogiques,", file=sys.stderr)
    print("les outils suivants sont nécessaires :", file=sys.stderr)
    print("  1. Sales Navigator -> recherche par titre de poste dans chaque CFA", file=sys.stderr)
    print("  2. Clay -> enrichissement en cascade (15+ sources)", file=sys.stderr)
    print("  3. Lusha / Dropcontact -> vérification emails", file=sys.stderr)
    print("  4. Phantombuster -> scraping LinkedIn automatisé", file=sys.stderr)


if __name__ == "__main__":
    main()
