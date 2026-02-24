#!/usr/bin/env python3
"""
Recherche le site web de chaque CFA sur DuckDuckGo par son nom + ville.
Sauvegarde la progression dans cfa_website_cache.json.
Met à jour Liste_CFA_Combinée.xlsx à la fin (et toutes les 100 CFAs).
"""

import json
import os
import time
import random
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from ddgs import DDGS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_IN  = os.path.join(BASE_DIR, "Liste_CFA_Combinée.xlsx")
EXCEL_OUT = os.path.join(BASE_DIR, "Liste_CFA_Combinée.xlsx")
CACHE_FILE = os.path.join(BASE_DIR, "cfa_website_cache.json")

# Domaines à exclure des résultats de recherche
EXCLUDED_DOMAINS = {
    "wikipedia.org", "wikimedia.org",
    "lapprenti.com", "letudiant.fr", "data.gouv.fr",
    "catalogue.apprentissage.education.gouv.fr",
    "parcoursup.fr", "onisep.fr", "intercfa.fr",
    "linkedin.com", "facebook.com", "twitter.com",
    "instagram.com", "youtube.com", "tiktok.com",
    "indeed.com", "jobteaser.com", "francetravail.fr",
    "hellowork.com", "cadremploi.fr", "monster.fr",
    "alternance.emploi.gouv.fr", "francecompetences.fr",
    "orientation.fr", "studyrama.com",
    "google.com", "bing.com", "yahoo.com",
    "pages-jaunes.fr", "pagesjaunesentreprises.fr",
    "societe.com", "infogreffe.fr", "pappers.fr",
    "annuaire-mairie.fr", "kompass.com",
    "opendatasoft.com", "data.opendatasoft.com",
    "annuaire-cfa.fr", "lhc.re",
    "etablissements-scolaires.fr", "fabert.com",
    "education.gouv.fr",
}


def is_excluded(url: str) -> bool:
    """Vérifie si un URL provient d'un domaine à exclure."""
    if not url:
        return True
    for domain in EXCLUDED_DOMAINS:
        if domain in url:
            return True
    return False


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def search_website(ddgs: DDGS, name: str, city: str, cp: str) -> str:
    """
    Cherche le site officiel d'un CFA via DuckDuckGo.
    Retourne l'URL trouvée ou chaîne vide.
    """
    # Construction de la requête
    location = city or cp or ""
    query = f'"{name}" {location} site officiel CFA'

    try:
        results = ddgs.text(query, max_results=5, region="fr-fr")
        for r in results:
            url = r.get("href", "")
            if not is_excluded(url):
                return url
    except Exception:
        pass

    # Requête de secours sans guillemets
    try:
        query2 = f"{name} {location} CFA apprentissage"
        results = ddgs.text(query2, max_results=5, region="fr-fr")
        for r in results:
            url = r.get("href", "")
            if not is_excluded(url):
                return url
    except Exception:
        pass

    return ""


def load_excel_rows() -> tuple:
    """
    Charge les lignes de l'Excel existant.
    Retourne (wb, ws, columns, rows_data)
    """
    wb = openpyxl.load_workbook(EXCEL_IN)
    ws = wb.active

    # Lire les colonnes depuis la 1ère ligne
    columns = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]

    rows = []
    for r in range(2, ws.max_row + 1):
        row = {}
        for c, col_name in enumerate(columns, start=1):
            row[col_name] = ws.cell(r, c).value or ""
        rows.append(row)

    return wb, ws, columns, rows


def update_excel(rows: list, columns: list):
    """Réécrit le fichier Excel avec les données mises à jour."""
    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    SOURCE_COLORS = {
        "data.gouv.fr IDF": "D6E4F0",
        "lapprenti.com":    "D5F5E3",
        "letudiant.fr":     "FEF9E7",
    }
    COL_WIDTHS = {
        "Source": 20, "Nom du CFA": 45, "Adresse": 40, "Code Postal": 12,
        "Ville": 25, "Département": 25, "Région": 22, "Téléphone": 16,
        "Site Web": 40, "Email": 35,
    }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tous les CFA"

    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 20
    ws.freeze_panes = "A2"

    for row_idx, row in enumerate(rows, start=2):
        source = row.get("Source", "")
        fill_color = SOURCE_COLORS.get(source, "FFFFFF")
        row_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
        for col_idx, col_name in enumerate(columns, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=row.get(col_name, ""))
            cell.fill = row_fill
            cell.alignment = Alignment(vertical="center")

    for col_idx, col_name in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = COL_WIDTHS.get(col_name, 20)
    ws.auto_filter.ref = ws.dimensions

    wb.save(EXCEL_OUT)


def main():
    print("Chargement de l'Excel existant…")
    wb, ws, columns, rows = load_excel_rows()
    total = len(rows)

    # Charger le cache de progression
    cache = load_cache()
    print(f"Cache existant : {len(cache)} entrées")

    # Compter les CFAs sans site web
    without_web = [r for r in rows if not r.get("Site Web")]
    print(f"CFAs sans site web : {len(without_web)} / {total}")

    ddgs = DDGS()
    found_count = 0
    processed = 0

    for i, row in enumerate(rows):
        name = row.get("Nom du CFA", "")
        city = row.get("Ville", "")
        cp   = row.get("Code Postal", "")

        # Déjà un site web → passer
        if row.get("Site Web"):
            continue

        # Clé de cache
        cache_key = f"{name}|{cp}"

        if cache_key in cache:
            url = cache[cache_key]
        else:
            # Attente aléatoire pour éviter le rate limiting (1.0–2.5s)
            time.sleep(random.uniform(1.0, 2.5))
            url = search_website(ddgs, name, city, cp)
            cache[cache_key] = url

            # Sauvegarder le cache toutes les 10 recherches
            if processed % 10 == 0:
                save_cache(cache)

        if url:
            row["Site Web"] = url
            found_count += 1

        processed += 1

        # Affichage de progression
        if processed % 50 == 0 or processed == 1:
            pct = processed * 100 // len(without_web)
            print(f"  [{processed}/{len(without_web)}] {pct}% — {found_count} sites trouvés")
            # Sauvegarde intermédiaire de l'Excel toutes les 100 CFAs
            if processed % 100 == 0:
                save_cache(cache)
                update_excel(rows, columns)
                print(f"  → Excel sauvegardé ({found_count} sites web)")

    # Sauvegarde finale
    save_cache(cache)
    update_excel(rows, columns)

    with_web_total = sum(1 for r in rows if r.get("Site Web"))
    print(f"\n{'='*55}")
    print(f"  TERMINÉ")
    print(f"  Sites web trouvés : {with_web_total} / {total} ({with_web_total*100//total}%)")
    print(f"  Fichier mis à jour : {EXCEL_OUT}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
