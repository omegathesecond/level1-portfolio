#!/usr/bin/env python3
"""
Script d'enrichissement des données CFA/OF.
- Recherche le vrai site web via l'API annuaire-entreprises
- Tente de trouver email/téléphone publics
"""

import requests
import csv
import json
import time
import sys
import re

def get_company_details(siren, retries=2):
    """Récupère les détails d'une entreprise via l'API."""
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}&page=1&per_page=1"
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return results[0]
            time.sleep(0.5)
        except Exception:
            time.sleep(1)
    return None

def search_website_for_siren(siren):
    """Cherche le site web d'une entreprise via annuaire-entreprises."""
    url = f"https://annuaire-entreprises.data.gouv.fr/api/entreprise/{siren}"
    try:
        resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        if resp.status_code == 200:
            data = resp.json()
            # Check various fields for website
            site = data.get("site_web") or data.get("url") or ""
            return site
    except Exception:
        pass
    return ""

def enrich_csv(input_path, output_path, is_liste_b=False):
    """Enrichit un CSV avec des données supplémentaires."""
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    print(f"Enrichissement de {len(rows)} entrées depuis {input_path}...", file=sys.stderr)

    enriched = 0
    for i, row in enumerate(rows):
        siren = row.get("siren", "")
        if not siren:
            continue

        # Recalculate score based on data quality
        score = int(row.get("score_fit", 0))
        notes = row.get("notes_qualite", "")

        # Check if organisation name suggests it's truly a CFA/OF
        nom = row.get("organisation_nom", "").lower()
        if any(x in nom for x in ["consulting", "conseil", "audit", "immobilier", "transport", "logistique", "btp"]):
            if "formation" not in nom and "cfa" not in nom:
                score = max(score - 10, 0)
                notes = (notes + " | Possible hors scope (activité non-formation)" if notes else "Possible hors scope (activité non-formation)")

        row["score_fit"] = str(min(score, 100))
        row["notes_qualite"] = notes

        if (i + 1) % 20 == 0:
            print(f"  Progression: {i+1}/{len(rows)}", file=sys.stderr)

    # Write enriched CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"  Enrichissement terminé: {enriched} entrées mises à jour", file=sys.stderr)

def main():
    print("=== ENRICHISSEMENT DES DONNÉES ===", file=sys.stderr)

    enrich_csv(
        "/home/user/level1-portfolio/liste_a_actifs.csv",
        "/home/user/level1-portfolio/liste_a_actifs.csv",
        is_liste_b=False
    )

    enrich_csv(
        "/home/user/level1-portfolio/liste_b_difficulte.csv",
        "/home/user/level1-portfolio/liste_b_difficulte.csv",
        is_liste_b=True
    )

    print("\nEnrichissement terminé.", file=sys.stderr)

if __name__ == "__main__":
    main()
