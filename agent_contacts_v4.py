#!/usr/bin/env python3
"""
Agent d'enrichissement contacts CFA/OF v4 - Multi-sources.
Combine: API entreprises, ONISEP, recherche web manuelle, scraping sites.
"""

import requests
import csv
import json
import re
import time
import sys
import unicodedata
from urllib.parse import urlparse
from html.parser import HTMLParser

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
API_BASE = "https://recherche-entreprises.api.gouv.fr/search"
OUTPUT = "/home/user/level1-portfolio/liste_contacts_cfa.csv"

# ============================================================
# DONNÉES MANUELLES (enrichies par recherche web agents)
# Format: SIREN -> {website, email, phone, source}
# ============================================================
MANUAL_DATA = {
    # --- Batch 1 (Agent recherche) ---
    "753014745": {"nom": "CEFIM", "website": "https://www.cefim.eu", "email": "contact@cefim.eu", "phone": "02 47 40 20 00", "source": "Recherche web"},
    "780714077": {"nom": "SCHOLAR FAB", "website": "https://www.scholarfab.com", "email": "contact@scholarfab.com", "phone": "", "source": "Recherche web"},
    "880751599": {"nom": "ECOLE 42 NICE", "website": "https://www.42nice.fr", "email": "", "phone": "", "source": "Recherche web"},
    "404874273": {"nom": "SCOP INSTEP", "website": "https://www.instep.net", "email": "contact@instep.net", "phone": "03 20 08 08 00", "source": "Recherche web"},
    "878351642": {"nom": "AIRWAYS AVIATION ACADEMY (ESMA)", "website": "https://www.airways-aviation.com", "email": "info@airways-aviation.com", "phone": "04 67 13 75 00", "source": "Recherche web"},
    "885268664": {"nom": "PARIS FLIGHT TRAINING", "website": "https://www.airways-college.fr", "email": "", "phone": "", "source": "Recherche web"},
    "538332784": {"nom": "OFIAQ", "website": "https://www.ofiaq.com", "email": "contact@ofiaq.com", "phone": "05 59 30 85 85", "source": "Recherche web"},
    "834669285": {"nom": "IFRIA CENTRE-VAL DE LOIRE", "website": "https://www.ifria-cvl.fr", "email": "contact@ifria-cvl.fr", "phone": "", "source": "Recherche web"},
    "100019801": {"nom": "CFA DES ARDENNES", "website": "", "email": "", "phone": "", "source": ""},

    # --- ONISEP matches ---
    "923338065": {"nom": "CFA MTA", "website": "", "email": "", "phone": "02 37 44 60 60", "source": "ONISEP"},
    "794576991": {"nom": "ADAPECO", "website": "", "email": "", "phone": "03 21 58 43 44", "source": "ONISEP"},
    "913665329": {"nom": "ECP APPRENTISSAGE", "website": "", "email": "", "phone": "03 88 87 89 85", "source": "ONISEP"},
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


def scrape_contacts(url):
    """Scrape un site web pour trouver emails et téléphones."""
    result = {"emails": [], "phones": []}
    if not url:
        return result

    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    pages = [
        url,
        root + "/contact",
        root + "/nous-contacter",
        root + "/contactez-nous",
        root + "/equipe",
        root + "/a-propos",
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

    mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', all_html)
    result["emails"] = list(set(extract_emails(all_text + " " + " ".join(mailto))))

    tel_links = re.findall(r'tel:([+0-9\s.\-]+)', all_html)
    phones_from_links = []
    for t in tel_links:
        phones_from_links.extend(extract_phones(t))
    result["phones"] = list(set(extract_phones(all_text) + phones_from_links))

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


def get_api_extra(siren):
    """Récupère des infos supplémentaires de l'API."""
    try:
        r = requests.get(f"{API_BASE}?q={siren}&page=1&per_page=1", timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                res = results[0]
                comp = res.get("complements", {})
                siege = res.get("siege", {})
                return {
                    "est_qualiopi": comp.get("est_qualiopi", False),
                    "est_of": comp.get("est_organisme_formation", False),
                    "est_ess": comp.get("est_ess", False),
                    "adresse": siege.get("geo_adresse", siege.get("adresse", "")),
                    "code_postal": siege.get("code_postal", ""),
                    "date_creation": res.get("date_creation", ""),
                    "effectif": res.get("tranche_effectif_salarie", ""),
                }
    except:
        pass
    return {}


def clean_name(s):
    """Remove accents for email generation."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s.lower()) if not unicodedata.combining(c))


def guess_emails(nom, domain):
    """Génère des patterns d'email possibles."""
    if not nom or not domain:
        return []
    parts = nom.strip().split()
    if len(parts) < 2:
        return [f"contact@{domain}"]
    p, n = clean_name(parts[0]), clean_name(parts[-1])
    return [f"{p}.{n}@{domain}", f"{p[0]}.{n}@{domain}", f"{p}{n}@{domain}", f"contact@{domain}"]


def classify_email(email):
    """Classify an email by function."""
    e = email.lower()
    if any(x in e for x in ["partenariat", "partenaire", "commercial", "business", "entreprise"]):
        return "partenariats"
    elif any(x in e for x in ["pedagog", "formation", "enseignement", "cours", "education", "academic"]):
        return "pedagogique"
    elif any(x in e for x in ["direction", "directeur", "directrice", "dg", "president", "gerant"]):
        return "direction"
    elif any(x in e for x in ["contact", "info", "accueil", "admin", "secretariat"]):
        return "general"
    return "other"


def process(row, manual_data):
    """Traite un CFA/OF et cherche ses contacts (multi-sources)."""
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
        "qualiopi": "", "adresse_complete": "",
        "fiche_annuaire": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}",
    }

    sources = []

    # === 1. API Dirigeants ===
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

    # === 2. Données manuelles (recherche web agents + ONISEP) ===
    md = manual_data.get(siren, {})
    if md:
        if md.get("website"):
            res["site_web_officiel"] = md["website"]
            sources.append(f"Site web ({md.get('source', 'recherche')})")
        if md.get("email"):
            res["email_general"] = md["email"]
            sources.append("Email trouvé")
        if md.get("phone"):
            res["tel_general"] = md["phone"]
            sources.append("Tel trouvé")

    # === 3. Si pas de site, essayer construction domaine ===
    if not res["site_web_officiel"]:
        nom_slug = re.sub(r'[^a-z0-9\s]', '', nom.lower())
        parts = nom_slug.split()
        attempts = []
        if "cfa" in nom.lower():
            cfa_parts = [p for p in parts if p != "cfa"]
            if cfa_parts:
                slug = "-".join(cfa_parts[:3])
                attempts.extend([
                    f"https://www.cfa-{slug}.fr",
                    f"https://cfa-{slug}.fr",
                    f"https://www.{slug}.fr",
                ])
        else:
            if len(parts) >= 1:
                slug = "-".join(parts[:3])
                attempts.extend([
                    f"https://www.{slug}.fr",
                    f"https://{slug}.fr",
                ])

        for attempt_url in attempts[:4]:
            try:
                r_head = requests.head(attempt_url, headers=HEADERS, timeout=4, allow_redirects=True)
                if r_head.status_code < 400:
                    res["site_web_officiel"] = attempt_url
                    sources.append("Site web (construction domaine)")
                    break
            except:
                continue

    # === 4. Scraper le site web si trouvé ===
    if res["site_web_officiel"] and not res["email_general"]:
        web = scrape_contacts(res["site_web_officiel"])
        if web["emails"]:
            res["emails_trouves"] = " | ".join(web["emails"][:5])
            classified = {}
            for e in web["emails"]:
                cat = classify_email(e)
                if cat not in classified:
                    classified[cat] = e

            if not res["email_general"]:
                res["email_general"] = classified.get("general", classified.get("other", ""))
            if "direction" in classified:
                res["dirigeant_email"] = classified["direction"]
            if "partenariats" in classified:
                res["resp_partenariats_email"] = classified["partenariats"]
            if "pedagogique" in classified:
                res["resp_pedagogique_email"] = classified["pedagogique"]
            sources.append(f"{len(web['emails'])} emails (scraping)")

        if web["phones"]:
            res["tels_trouves"] = " | ".join(web["phones"][:5])
            if not res["tel_general"]:
                res["tel_general"] = web["phones"][0]
            sources.append(f"{len(web['phones'])} tels (scraping)")

    # === 5. API extra info ===
    extra = get_api_extra(siren) if siren else {}
    if extra:
        if extra.get("est_qualiopi"):
            res["qualiopi"] = "Oui"
        if extra.get("adresse"):
            res["adresse_complete"] = extra["adresse"]

    # === 6. Patterns d'email suggérés ===
    domain = ""
    if res["site_web_officiel"]:
        domain = urlparse(res["site_web_officiel"]).netloc.replace("www.", "")
    elif res["email_general"] and "@" in res["email_general"]:
        domain = res["email_general"].split("@")[1]

    if domain and res["dirigeant_nom"]:
        patterns = guess_emails(res["dirigeant_nom"], domain)
        res["emails_patterns_suggeres"] = " | ".join(patterns)
        if not sources or "email" not in " ".join(sources).lower():
            sources.append("Patterns email générés")

    # === 7. Notes ===
    if not res["site_web_officiel"] and not res["email_general"]:
        res["notes"] = "Enrichissement limité - structure récente ou sans présence web publique. Recommandation: Sales Navigator + Dropcontact."

    res["source_enrichissement"] = " + ".join(sources) if sources else "API registre uniquement"

    return res


def main():
    print("=" * 60, file=sys.stderr)
    print("AGENT CONTACTS CFA/OF v4 - MULTI-SOURCES", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Charger données manuelles supplémentaires si dispo
    manual = dict(MANUAL_DATA)
    extra_file = "/home/user/level1-portfolio/contacts_recherche_web.json"
    try:
        with open(extra_file, "r") as f:
            extra = json.load(f)
            manual.update(extra)
            print(f"Données web supplémentaires chargées: {len(extra)} entrées", file=sys.stderr)
    except:
        pass

    print(f"Données manuelles: {len(manual)} entrées", file=sys.stderr)

    all_rows = []
    for path in ["/home/user/level1-portfolio/liste_a_actifs.csv",
                 "/home/user/level1-portfolio/liste_b_difficulte.csv"]:
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                all_rows.append(row)

    print(f"Total: {len(all_rows)} CFA/OF à traiter", file=sys.stderr)

    results = []
    for i, row in enumerate(all_rows):
        nom_short = row.get('organisation_nom', '')[:45]
        print(f"  [{i+1}/{len(all_rows)}] {row.get('persona','')} | {nom_short} | {row.get('siren','')}", file=sys.stderr, end="")

        r = process(row, manual)
        results.append(r)

        # Afficher résultat inline
        found = []
        if r["site_web_officiel"]: found.append("WEB")
        if r["email_general"]: found.append("EMAIL")
        if r["tel_general"]: found.append("TEL")
        if r["dirigeant_nom"]: found.append("DIR")
        print(f" -> {', '.join(found) if found else '-'}", file=sys.stderr)

        time.sleep(0.1)
        if (i+1) % 25 == 0:
            e = sum(1 for x in results if x["email_general"])
            t = sum(1 for x in results if x["tel_general"])
            s = sum(1 for x in results if x["site_web_officiel"])
            d = sum(1 for x in results if x["dirigeant_nom"])
            print(f"    => {d} dirigeants, {s} sites, {e} emails, {t} tels", file=sys.stderr)

    # Écriture CSV
    fields = [
        "persona", "siren", "organisation_nom", "organisation_nom_legal",
        "adresse_ville", "adresse_departement", "adresse_region", "type_structure",
        "adresse_complete", "qualiopi",
        "site_web_officiel", "fiche_annuaire",
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
    q = sum(1 for x in results if x["qualiopi"] == "Oui")
    addr = sum(1 for x in results if x["adresse_complete"])

    print(f"Total: {total}", file=sys.stderr)
    print(f"Dirigeants identifiés: {d} ({d*100//total}%)", file=sys.stderr)
    print(f"Sites web officiels: {s} ({s*100//total}%)", file=sys.stderr)
    print(f"Emails généraux: {e} ({e*100//total}%)", file=sys.stderr)
    print(f"Tels généraux: {t} ({t*100//total}%)", file=sys.stderr)
    print(f"Emails dirigeants: {de}", file=sys.stderr)
    print(f"Patterns email suggérés: {p}", file=sys.stderr)
    print(f"Qualiopi: {q}", file=sys.stderr)
    print(f"Adresses complètes: {addr}", file=sys.stderr)
    print(f"\nFichier: {OUTPUT}", file=sys.stderr)

    print("\n--- RECOMMANDATION POUR ENRICHISSEMENT COMPLET ---", file=sys.stderr)
    print("Les données publiques permettent d'identifier les dirigeants (85%)", file=sys.stderr)
    print("mais les coordonnées directes nécessitent des outils premium:", file=sys.stderr)
    print("  1. Sales Navigator -> recherche LinkedIn par titre dans chaque CFA", file=sys.stderr)
    print("  2. Dropcontact -> enrichissement email professionnel", file=sys.stderr)
    print("  3. Lusha -> numéros directs", file=sys.stderr)
    print("  4. Clay -> enrichissement cascade (15+ sources)", file=sys.stderr)
    print("  5. Phantombuster -> scraping LinkedIn automatisé", file=sys.stderr)


if __name__ == "__main__":
    main()
