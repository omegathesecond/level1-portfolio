#!/usr/bin/env python3
"""
Agent d'enrichissement de contacts CFA/OF.
Recherche les numéros de téléphone et emails publics des :
- Dirigeants / Directeurs
- Responsables partenariats
- Responsables pédagogiques

Sources utilisées :
1. API recherche-entreprises.api.gouv.fr (dirigeants légaux)
2. Recherche du site web officiel via Google
3. Scraping des pages contact/équipe des sites officiels
4. Annuaire-entreprises.data.gouv.fr
"""

import requests
import csv
import json
import re
import time
import sys
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

# ============================================================
# CONFIGURATION
# ============================================================

API_BASE = "https://recherche-entreprises.api.gouv.fr/search"
OUTPUT_PATH = "/home/user/level1-portfolio/liste_contacts_cfa.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CFAContactAgent/1.0; research)"
}

# ============================================================
# UTILITAIRES
# ============================================================

class TextExtractor(HTMLParser):
    """Extrait le texte brut d'un HTML."""
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
    """Extrait les emails d'un texte."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # Filtrer les emails indésirables
    blocked = ["example.com", "sentry.io", "wixpress.com", "w3.org", "schema.org",
               "googleusercontent", "gstatic", "googleapis", "jquery", "bootstrap",
               "wordpress", "wp-json", ".png", ".jpg", ".gif", ".svg", ".css", ".js"]
    return [e.lower() for e in emails if not any(b in e.lower() for b in blocked)]


def extract_phones(text):
    """Extrait les numéros de téléphone français d'un texte."""
    patterns = [
        r'(?:0|\+33\s?|0033\s?)[1-9](?:[\s.\-]?\d{2}){4}',  # Format FR standard
        r'(?:0|\+33)[1-9]\d{8}',  # Format compact
    ]
    phones = []
    for pat in patterns:
        matches = re.findall(pat, text)
        for m in matches:
            clean = re.sub(r'[\s.\-]', '', m)
            if clean.startswith('+33'):
                clean = '0' + clean[3:]
            elif clean.startswith('0033'):
                clean = '0' + clean[4:]
            if len(clean) == 10 and clean.startswith('0'):
                # Format lisible
                formatted = f"{clean[:2]} {clean[2:4]} {clean[4:6]} {clean[6:8]} {clean[8:10]}"
                phones.append(formatted)
    return list(set(phones))


def fetch_page(url, timeout=10):
    """Récupère le contenu d'une page web."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return ""


def search_website_google(query):
    """Tente de trouver le site web d'une entreprise via une recherche."""
    # On ne peut pas utiliser Google directement, mais on peut essayer
    # d'accéder à l'annuaire-entreprises pour trouver le site web
    return ""


# ============================================================
# RECHERCHE DE CONTACTS VIA API
# ============================================================

def get_dirigeants_api(siren):
    """Récupère les dirigeants depuis l'API."""
    try:
        resp = requests.get(f"{API_BASE}?q={siren}&page=1&per_page=1", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                entity = results[0]
                dirigeants = entity.get("dirigeants", [])
                contacts = []
                for d in dirigeants:
                    if d.get("type_dirigeant") == "personne physique":
                        nom = d.get("nom", "")
                        prenoms = d.get("prenoms", "")
                        qualite = d.get("qualite", "") or ""
                        if prenoms:
                            first = prenoms.split()[0].capitalize()
                            full_name = f"{first} {nom.capitalize()}"
                        else:
                            full_name = nom.capitalize()
                        contacts.append({
                            "nom": full_name,
                            "role": qualite,
                            "source": "API recherche-entreprises (registre légal)"
                        })
                return contacts
    except Exception:
        pass
    return []


def search_contact_on_website(url, org_name):
    """Cherche des contacts sur le site web d'une organisation."""
    contacts = {"emails": [], "phones": [], "people": []}

    if not url or "annuaire-entreprises" in url:
        return contacts

    # Pages à explorer
    pages_to_check = [
        url,
        urljoin(url, "/contact"),
        urljoin(url, "/contact/"),
        urljoin(url, "/equipe"),
        urljoin(url, "/equipe/"),
        urljoin(url, "/notre-equipe"),
        urljoin(url, "/qui-sommes-nous"),
        urljoin(url, "/a-propos"),
        urljoin(url, "/about"),
        urljoin(url, "/mentions-legales"),
    ]

    all_text = ""
    for page_url in pages_to_check:
        html = fetch_page(page_url)
        if html:
            # Extract text
            extractor = TextExtractor()
            try:
                extractor.feed(html)
                text = extractor.get_text()
                all_text += " " + text
            except Exception:
                all_text += " " + html

            # Also check raw HTML for mailto: links
            mailto_pattern = r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})'
            mailto_emails = re.findall(mailto_pattern, html)
            contacts["emails"].extend([e.lower() for e in mailto_emails])

            # Check for tel: links
            tel_pattern = r'tel:([+0-9\s.\-]+)'
            tel_matches = re.findall(tel_pattern, html)
            for t in tel_matches:
                phones = extract_phones(t)
                contacts["phones"].extend(phones)

        time.sleep(0.3)

    # Extract from all collected text
    contacts["emails"].extend(extract_emails(all_text))
    contacts["phones"].extend(extract_phones(all_text))

    # Deduplicate
    contacts["emails"] = list(set(contacts["emails"]))
    contacts["phones"] = list(set(contacts["phones"]))

    # Search for role-specific people in text
    role_patterns = [
        (r"directeur[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Directeur"),
        (r"directrice[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Directrice"),
        (r"responsable\s+(?:des\s+)?partenariat[s]?[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Responsable partenariats"),
        (r"responsable\s+pédagogique[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Responsable pédagogique"),
        (r"directeur\s+pédagogique[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Directeur pédagogique"),
        (r"président[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Président"),
        (r"gérant[:\s]+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)", "Gérant"),
    ]

    for pattern, role in role_patterns:
        matches = re.findall(pattern, all_text)
        for m in matches:
            contacts["people"].append({"nom": m.strip(), "role": role, "source": f"Site web ({urlparse(url).netloc})"})

    return contacts


def guess_email_patterns(nom_complet, domain):
    """Génère des patterns d'email possibles (pour indication, pas de vérification)."""
    if not nom_complet or not domain:
        return []

    parts = nom_complet.lower().strip().split()
    if len(parts) < 2:
        return []

    prenom = parts[0]
    nom = parts[-1]

    # Remove accents (basic)
    import unicodedata
    def remove_accents(s):
        nfkd = unicodedata.normalize('NFKD', s)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    prenom_clean = remove_accents(prenom)
    nom_clean = remove_accents(nom)

    patterns = [
        f"{prenom_clean}.{nom_clean}@{domain}",
        f"{prenom_clean[0]}.{nom_clean}@{domain}",
        f"{prenom_clean}@{domain}",
        f"{prenom_clean}{nom_clean}@{domain}",
        f"{nom_clean}.{prenom_clean}@{domain}",
        f"contact@{domain}",
        f"direction@{domain}",
    ]
    return patterns[:4]


# ============================================================
# TRAITEMENT PRINCIPAL
# ============================================================

def process_cfa(row):
    """Traite un CFA et cherche ses contacts."""
    siren = row.get("siren", "")
    nom = row.get("organisation_nom", "")
    site_web = row.get("site_web_url", "")
    contact_existant = row.get("contact_nom", "")
    contact_role = row.get("contact_role", "")

    result = {
        "siren": siren,
        "organisation_nom": nom,
        "organisation_nom_legal": row.get("organisation_nom_legal", ""),
        "adresse_ville": row.get("adresse_ville", ""),
        "adresse_departement": row.get("adresse_departement", ""),
        "adresse_region": row.get("adresse_region", ""),
        "type_structure": row.get("type_structure", ""),
        "persona": row.get("persona", ""),
        "site_web": site_web,
        # Dirigeant
        "dirigeant_nom": "",
        "dirigeant_role": "",
        "dirigeant_email": "",
        "dirigeant_tel": "",
        "dirigeant_linkedin": "",
        "dirigeant_source": "",
        # Responsable partenariats
        "resp_partenariats_nom": "",
        "resp_partenariats_role": "",
        "resp_partenariats_email": "",
        "resp_partenariats_tel": "",
        "resp_partenariats_linkedin": "",
        "resp_partenariats_source": "",
        # Responsable pédagogique
        "resp_pedagogique_nom": "",
        "resp_pedagogique_role": "",
        "resp_pedagogique_email": "",
        "resp_pedagogique_tel": "",
        "resp_pedagogique_linkedin": "",
        "resp_pedagogique_source": "",
        # Contacts génériques
        "email_general": "",
        "tel_general": "",
        "emails_patterns_suggeres": "",
        "source_enrichissement": "",
        "notes": "",
    }

    sources = []

    # 1. Dirigeants via API
    if siren:
        dirigeants = get_dirigeants_api(siren)
        if dirigeants:
            # Premier dirigeant = le plus important
            d = dirigeants[0]
            result["dirigeant_nom"] = d["nom"]
            result["dirigeant_role"] = d["role"]
            result["dirigeant_source"] = d["source"]
            sources.append("API registre")
        elif contact_existant:
            result["dirigeant_nom"] = contact_existant
            result["dirigeant_role"] = contact_role
            result["dirigeant_source"] = "CSV initial"

    # 2. Contacts sur site web
    if site_web and "annuaire-entreprises" not in site_web:
        web_contacts = search_contact_on_website(site_web, nom)

        if web_contacts["emails"]:
            # Trier : emails de contact général en premier
            general_emails = [e for e in web_contacts["emails"] if any(x in e for x in ["contact", "info", "accueil", "direction"])]
            other_emails = [e for e in web_contacts["emails"] if e not in general_emails]

            if general_emails:
                result["email_general"] = general_emails[0]
            if other_emails:
                # Essayer de deviner si c'est un email personnel
                result["dirigeant_email"] = other_emails[0] if not result.get("email_general") else ""
            elif general_emails:
                result["email_general"] = general_emails[0]

            sources.append("Site web")

        if web_contacts["phones"]:
            result["tel_general"] = web_contacts["phones"][0]
            sources.append("Site web (tel)")

        # People found on website
        for person in web_contacts.get("people", []):
            role_lower = person["role"].lower()
            if "partenariat" in role_lower:
                result["resp_partenariats_nom"] = person["nom"]
                result["resp_partenariats_role"] = person["role"]
                result["resp_partenariats_source"] = person["source"]
            elif "pédagogique" in role_lower:
                result["resp_pedagogique_nom"] = person["nom"]
                result["resp_pedagogique_role"] = person["role"]
                result["resp_pedagogique_source"] = person["source"]
            elif "directeur" in role_lower or "directrice" in role_lower or "président" in role_lower or "gérant" in role_lower:
                if not result["dirigeant_nom"]:
                    result["dirigeant_nom"] = person["nom"]
                    result["dirigeant_role"] = person["role"]
                    result["dirigeant_source"] = person["source"]

    # 3. Email patterns suggestions
    domain = ""
    if site_web and "annuaire-entreprises" not in site_web:
        parsed = urlparse(site_web)
        domain = parsed.netloc.replace("www.", "")
    elif result.get("email_general"):
        domain = result["email_general"].split("@")[1] if "@" in result["email_general"] else ""

    if domain and result["dirigeant_nom"]:
        patterns = guess_email_patterns(result["dirigeant_nom"], domain)
        result["emails_patterns_suggeres"] = " | ".join(patterns)

    result["source_enrichissement"] = " + ".join(sources) if sources else "API registre uniquement"

    return result


def main():
    print("=" * 60, file=sys.stderr)
    print("AGENT D'ENRICHISSEMENT CONTACTS CFA/OF", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Charger les deux listes
    all_rows = []

    for csv_path in ["/home/user/level1-portfolio/liste_a_actifs.csv",
                     "/home/user/level1-portfolio/liste_b_difficulte.csv"]:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_rows.append(row)

    print(f"\nTotal CFA/OF à traiter: {len(all_rows)}", file=sys.stderr)

    # Traiter chaque CFA
    results = []
    for i, row in enumerate(all_rows):
        nom = row.get("organisation_nom", "")[:50]
        siren = row.get("siren", "")
        persona = row.get("persona", "")

        print(f"  [{i+1}/{len(all_rows)}] {persona} | {nom} (SIREN {siren})", file=sys.stderr)

        result = process_cfa(row)
        results.append(result)

        # Rate limiting
        time.sleep(0.2)

        if (i + 1) % 20 == 0:
            print(f"    -> Progression: {i+1}/{len(all_rows)}", file=sys.stderr)

    # Écrire le CSV final
    fieldnames = [
        "persona", "siren", "organisation_nom", "organisation_nom_legal",
        "adresse_ville", "adresse_departement", "adresse_region", "type_structure",
        "site_web",
        "dirigeant_nom", "dirigeant_role", "dirigeant_email", "dirigeant_tel", "dirigeant_linkedin", "dirigeant_source",
        "resp_partenariats_nom", "resp_partenariats_role", "resp_partenariats_email", "resp_partenariats_tel", "resp_partenariats_linkedin", "resp_partenariats_source",
        "resp_pedagogique_nom", "resp_pedagogique_role", "resp_pedagogique_email", "resp_pedagogique_tel", "resp_pedagogique_linkedin", "resp_pedagogique_source",
        "email_general", "tel_general",
        "emails_patterns_suggeres",
        "source_enrichissement", "notes"
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Statistiques
    print("\n" + "=" * 60, file=sys.stderr)
    print("STATISTIQUES", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    total = len(results)
    dirigeants = sum(1 for r in results if r.get("dirigeant_nom"))
    emails_gen = sum(1 for r in results if r.get("email_general"))
    tels_gen = sum(1 for r in results if r.get("tel_general"))
    dirigeant_emails = sum(1 for r in results if r.get("dirigeant_email"))
    resp_part = sum(1 for r in results if r.get("resp_partenariats_nom"))
    resp_peda = sum(1 for r in results if r.get("resp_pedagogique_nom"))
    patterns = sum(1 for r in results if r.get("emails_patterns_suggeres"))

    print(f"\nTotal: {total} CFA/OF traités", file=sys.stderr)
    print(f"Dirigeants identifiés: {dirigeants} ({dirigeants*100//total}%)", file=sys.stderr)
    print(f"Emails généraux trouvés: {emails_gen} ({emails_gen*100//total}%)", file=sys.stderr)
    print(f"Tels généraux trouvés: {tels_gen} ({tels_gen*100//total}%)", file=sys.stderr)
    print(f"Emails dirigeants: {dirigeant_emails}", file=sys.stderr)
    print(f"Resp. partenariats: {resp_part}", file=sys.stderr)
    print(f"Resp. pédagogiques: {resp_peda}", file=sys.stderr)
    print(f"Patterns emails suggérés: {patterns}", file=sys.stderr)

    print(f"\nFichier généré: {OUTPUT_PATH}", file=sys.stderr)
    print("\n--- IMPORTANT ---", file=sys.stderr)
    print("Les emails/tels trouvés proviennent uniquement de sources PUBLIQUES.", file=sys.stderr)
    print("Pour enrichir davantage, utilisez:", file=sys.stderr)
    print("  - Clay (agrégateur 15+ outils) -> emails cascade", file=sys.stderr)
    print("  - Lusha -> emails + tels directs", file=sys.stderr)
    print("  - Dropcontact -> emails vérifiés", file=sys.stderr)
    print("  - Sales Navigator -> profils LinkedIn des contacts", file=sys.stderr)
    print("  - Les 'patterns suggérés' peuvent être vérifiés via Dropcontact/Hunter", file=sys.stderr)


if __name__ == "__main__":
    main()
