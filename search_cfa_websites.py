#!/usr/bin/env python3
"""
Recherche le site web de chaque CFA sur DuckDuckGo par son nom + ville.
Version parallèle avec ThreadPoolExecutor pour accélérer les recherches.
Sauvegarde la progression dans cfa_website_cache.json.
"""

import json
import os
import sys
import time
import random
import threading
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from concurrent.futures import ThreadPoolExecutor, as_completed
from ddgs import DDGS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_IN  = os.path.join(BASE_DIR, "Liste_CFA_Combinée.xlsx")
EXCEL_OUT = os.path.join(BASE_DIR, "Liste_CFA_Combinée.xlsx")
CACHE_FILE = os.path.join(BASE_DIR, "cfa_website_cache.json")

NUM_WORKERS = 5  # threads parallèles

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
    "education.gouv.fr", "annuaire-ecoles.org",
}

# Verrou pour l'accès thread-safe au cache
cache_lock = threading.Lock()
progress_lock = threading.Lock()


def is_excluded(url: str) -> bool:
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


def search_one_cfa(name: str, city: str, cp: str) -> str:
    """Cherche le site officiel d'un CFA via DuckDuckGo."""
    location = city or cp or ""
    ddgs = DDGS()

    # Première tentative
    try:
        query = f'"{name}" {location} site officiel CFA'
        results = ddgs.text(query, max_results=5, region="fr-fr")
        for r in results:
            url = r.get("href", "")
            if not is_excluded(url):
                return url
    except Exception:
        pass

    # Requête de secours
    try:
        time.sleep(0.5)
        query2 = f"{name} {location} CFA apprentissage"
        results = ddgs.text(query2, max_results=5, region="fr-fr")
        for r in results:
            url = r.get("href", "")
            if not is_excluded(url):
                return url
    except Exception:
        pass

    return ""


def process_cfa(item, cache, counters):
    """Traite un seul CFA : recherche + mise à jour du cache."""
    idx, name, city, cp = item
    cache_key = f"{name}|{cp}"

    # Vérifier le cache
    with cache_lock:
        if cache_key in cache:
            url = cache[cache_key]
            # Re-filtrer avec les nouvelles exclusions
            if is_excluded(url):
                url = ""
            else:
                with progress_lock:
                    counters["skipped"] += 1
                return cache_key, url

    # Délai aléatoire court pour éviter le rate limiting
    time.sleep(random.uniform(0.3, 1.0))

    url = search_one_cfa(name, city, cp)

    with cache_lock:
        cache[cache_key] = url

    with progress_lock:
        counters["done"] += 1
        if url:
            counters["found"] += 1
        total_done = counters["done"] + counters["skipped"]
        if counters["done"] % 20 == 0:
            pct = total_done * 100 // counters["total"]
            print(f"  [{total_done}/{counters['total']}] {pct}% — "
                  f"{counters['found']} nouveaux sites trouvés "
                  f"(+{counters['skipped']} en cache)", flush=True)
            save_cache(cache)

    return cache_key, url


def load_excel_rows():
    wb = openpyxl.load_workbook(EXCEL_IN)
    ws = wb.active
    columns = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(2, ws.max_row + 1):
        row = {}
        for c, col_name in enumerate(columns, start=1):
            row[col_name] = ws.cell(r, c).value or ""
        rows.append(row)
    return columns, rows


def update_excel(rows, columns):
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
    print("Chargement de l'Excel…", flush=True)
    columns, rows = load_excel_rows()
    total = len(rows)

    cache = load_cache()
    print(f"Cache existant : {len(cache)} entrées", flush=True)

    # Construire la liste des CFAs à traiter (sans site web)
    to_process = []
    for i, row in enumerate(rows):
        if not row.get("Site Web"):
            to_process.append((
                i,
                row.get("Nom du CFA", ""),
                row.get("Ville", ""),
                str(row.get("Code Postal", "")),
            ))

    print(f"CFAs à traiter : {len(to_process)} / {total}", flush=True)
    print(f"Threads parallèles : {NUM_WORKERS}", flush=True)

    counters = {"done": 0, "found": 0, "skipped": 0, "total": len(to_process)}
    results_map = {}

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {
            executor.submit(process_cfa, item, cache, counters): item
            for item in to_process
        }
        for future in as_completed(futures):
            try:
                cache_key, url = future.result()
                results_map[cache_key] = url
            except Exception as e:
                print(f"  Erreur: {e}", flush=True)

    # Appliquer les résultats aux lignes
    for row in rows:
        if not row.get("Site Web"):
            cache_key = f"{row.get('Nom du CFA', '')}|{row.get('Code Postal', '')}"
            url = results_map.get(cache_key, "") or cache.get(cache_key, "")
            if url and not is_excluded(url):
                row["Site Web"] = url

    # Sauvegarde finale
    save_cache(cache)
    update_excel(rows, columns)

    with_web = sum(1 for r in rows if r.get("Site Web"))
    print(f"\n{'='*55}", flush=True)
    print(f"  TERMINÉ", flush=True)
    print(f"  Sites web trouvés : {with_web} / {total} ({with_web*100//total}%)", flush=True)
    print(f"  Fichier mis à jour : {EXCEL_OUT}", flush=True)
    print(f"{'='*55}", flush=True)


if __name__ == "__main__":
    main()
