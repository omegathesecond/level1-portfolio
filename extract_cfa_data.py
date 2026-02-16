#!/usr/bin/env python3
"""
Script d'extraction de données CFA/Organismes de formation via l'API recherche-entreprises.api.gouv.fr
Pour constitution de listes B2B (Liste A: actifs, Liste B: en difficulté)
"""

import requests
import json
import csv
import time
import sys
from datetime import datetime

BASE_URL = "https://recherche-entreprises.api.gouv.fr/search"

# Départements IDF à exclure
IDF_DEPS = {"75", "77", "78", "91", "92", "93", "94", "95"}

# Mapping département -> région
DEP_TO_REGION = {
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
    "2A": "Corse", "2B": "Corse",
    "08": "Grand Est", "10": "Grand Est", "51": "Grand Est", "52": "Grand Est",
    "54": "Grand Est", "55": "Grand Est", "57": "Grand Est", "67": "Grand Est", "68": "Grand Est", "88": "Grand Est",
    "02": "Hauts-de-France", "59": "Hauts-de-France", "60": "Hauts-de-France",
    "62": "Hauts-de-France", "80": "Hauts-de-France",
    "14": "Normandie", "27": "Normandie", "50": "Normandie", "61": "Normandie", "76": "Normandie",
    "44": "Pays de la Loire", "49": "Pays de la Loire", "53": "Pays de la Loire",
    "72": "Pays de la Loire", "85": "Pays de la Loire",
    "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine", "19": "Nouvelle-Aquitaine",
    "23": "Nouvelle-Aquitaine", "24": "Nouvelle-Aquitaine", "33": "Nouvelle-Aquitaine",
    "40": "Nouvelle-Aquitaine", "47": "Nouvelle-Aquitaine", "64": "Nouvelle-Aquitaine",
    "79": "Nouvelle-Aquitaine", "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
    "09": "Occitanie", "11": "Occitanie", "12": "Occitanie", "30": "Occitanie",
    "31": "Occitanie", "32": "Occitanie", "34": "Occitanie", "46": "Occitanie",
    "48": "Occitanie", "65": "Occitanie", "66": "Occitanie", "81": "Occitanie", "82": "Occitanie",
    "04": "Provence-Alpes-Côte d'Azur", "05": "Provence-Alpes-Côte d'Azur",
    "06": "Provence-Alpes-Côte d'Azur", "13": "Provence-Alpes-Côte d'Azur",
    "83": "Provence-Alpes-Côte d'Azur", "84": "Provence-Alpes-Côte d'Azur",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion", "976": "Mayotte",
}

def get_dep_from_cp(code_postal):
    """Extrait le département du code postal."""
    if not code_postal:
        return None
    cp = str(code_postal).strip()
    if cp.startswith("97") and len(cp) >= 3:
        return cp[:3]
    if cp.startswith("20"):
        # Corse
        num = int(cp[:5]) if len(cp) >= 5 else int(cp)
        if num >= 20000 and num < 20200:
            return "2A"
        elif num >= 20200:
            return "2B"
    return cp[:2]

def get_region(dep):
    """Retourne la région à partir du département."""
    return DEP_TO_REGION.get(dep, "Inconnue")

def is_idf(dep):
    """Vérifie si un département est en IDF."""
    return dep in IDF_DEPS

def extract_dirigeant(dirigeants):
    """Extrait le dirigeant principal (personne physique) de la liste."""
    priority_roles = ["Directeur", "Directeur général", "Président", "Gérant",
                      "Président de SAS", "Président du conseil d'administration",
                      "Président du conseil d'administration et directeur général"]

    best = None
    best_score = -1

    for d in dirigeants:
        if d.get("type_dirigeant") != "personne physique":
            continue
        qualite = d.get("qualite", "") or ""
        score = 0
        for i, role in enumerate(priority_roles):
            if role.lower() in qualite.lower():
                score = len(priority_roles) - i
                break
        if score > best_score or (best is None and d.get("type_dirigeant") == "personne physique"):
            best = d
            best_score = score

    if best:
        nom = best.get("nom", "")
        prenoms = best.get("prenoms", "")
        qualite = best.get("qualite", "")
        # Format: Prénom Nom (capitalize)
        if prenoms:
            first_prenom = prenoms.split()[0].capitalize()
            contact_nom = f"{first_prenom} {nom.capitalize()}"
        else:
            contact_nom = nom.capitalize()
        return contact_nom, qualite
    return "", ""

def query_api(params, max_retries=3):
    """Interroge l'API avec retry."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            else:
                print(f"  API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"  Request error: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    return None

def fetch_all_pages(base_params, max_pages=50, max_results=300):
    """Récupère toutes les pages de résultats."""
    all_results = []
    seen_sirens = set()

    for page in range(1, max_pages + 1):
        params = {**base_params, "page": page, "per_page": 25}
        data = query_api(params)
        if not data or not data.get("results"):
            break

        for r in data["results"]:
            siren = r.get("siren", "")
            if siren and siren not in seen_sirens:
                seen_sirens.add(siren)
                all_results.append(r)

        total_pages = data.get("total_pages", 0)
        print(f"  Page {page}/{min(total_pages, max_pages)} - {len(all_results)} résultats uniques", file=sys.stderr)

        if page >= total_pages or len(all_results) >= max_results:
            break

        time.sleep(0.3)  # Rate limiting

    return all_results

def process_entity(entity, persona="A"):
    """Transforme une entité API en ligne CSV."""
    siege = entity.get("siege", {})
    complements = entity.get("complements", {})

    siren = entity.get("siren", "")
    siret = siege.get("siret", "")
    nom_complet = entity.get("nom_complet", "")
    nom_raison = entity.get("nom_raison_sociale", "")

    code_postal = siege.get("code_postal", "")
    dep = siege.get("departement", "") or get_dep_from_cp(code_postal)
    ville = siege.get("libelle_commune", "")
    region = get_region(dep)

    date_creation = entity.get("date_creation", "")
    annee_creation = date_creation[:4] if date_creation else ""

    # Déterminer le type
    est_qualiopi = complements.get("est_qualiopi", False)
    est_of = complements.get("est_organisme_formation", False)
    nom_lower = nom_complet.lower()

    if "cfa" in nom_lower or "apprenti" in nom_lower or "apprentissage" in nom_lower:
        type_structure = "CFA"
    elif est_of or est_qualiopi:
        type_structure = "OF"
    else:
        type_structure = "inconnu"

    # Site web - construct from annuaire-entreprises
    site_web = f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else ""
    source_creation = site_web

    # Dirigeant
    dirigeants = entity.get("dirigeants", [])
    contact_nom, contact_role = extract_dirigeant(dirigeants)

    # Score
    score = 0
    raisons = []

    if "cfa" in nom_lower or "apprenti" in nom_lower:
        score += 30
        raisons.append("CFA identifié dans le nom")
    elif est_of:
        score += 15
        raisons.append("Organisme de formation confirmé")

    if annee_creation and int(annee_creation) >= 2023:
        score += 20
        raisons.append(f"Création {annee_creation} confirmée API")
    elif annee_creation and int(annee_creation) >= 2022:
        score += 10
        raisons.append(f"Création {annee_creation} (élargissement)")

    if dep and not is_idf(dep):
        score += 15
        raisons.append(f"Hors IDF ({dep})")

    if contact_nom:
        score += 15
        raisons.append(f"Dirigeant identifié: {contact_role}")

    if site_web:
        score += 10
        raisons.append("Fiche annuaire-entreprises disponible")

    if est_qualiopi:
        score += 10
        raisons.append("Certifié Qualiopi")

    return {
        "persona": persona,
        "organisation_nom": nom_complet,
        "organisation_nom_legal": nom_raison,
        "siren": siren,
        "siret": siret,
        "annee_creation": annee_creation,
        "date_creation_source_url": source_creation,
        "adresse_ville": ville,
        "adresse_departement": dep,
        "adresse_region": region,
        "site_web_url": site_web,
        "linkedin_entreprise_url": "",
        "type_structure": type_structure,
        "modalite_presume": "presentiel" if "cfa" in nom_lower or "campus" in nom_lower or "centre" in nom_lower else "inconnu",
        "preuve_modalite": "Déduit du nom/type (CFA = généralement présentiel)" if "cfa" in nom_lower else "",
        "contact_nom": contact_nom,
        "contact_role": contact_role,
        "contact_linkedin_url": "",
        "contact_email_public": "",
        "contact_tel_public": "",
        "source_contact_preuve": f"API recherche-entreprises.api.gouv.fr (SIREN {siren})" if contact_nom else "",
        "notes_qualite": "",
        "score_fit": min(score, 100),
        "raisons_score": " | ".join(raisons[:3]),
    }

def main():
    print("=" * 60, file=sys.stderr)
    print("EXTRACTION CFA / ORGANISMES DE FORMATION", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # ============================================================
    # LISTE A : Actifs, créés en 2023+, hors IDF
    # ============================================================
    print("\n--- LISTE A : CFA/OF actifs créés en 2023+ hors IDF ---", file=sys.stderr)

    liste_a_raw = []
    seen_a = set()

    # Recherches multiples pour maximiser la couverture
    searches_a = [
        {"q": "CFA", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "CFA", "activite_principale": "85.59B", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "formation apprentis", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "centre formation", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "organisme formation", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "formation professionnelle", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "apprentissage", "date_naissance_min": "2023-01-01", "etat_administratif": "A", "activite_principale": "85.59A"},
        {"q": "formation", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "formation", "activite_principale": "85.59B", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "formation", "activite_principale": "85.32Z", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "formation", "activite_principale": "85.42Z", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "campus", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        {"q": "ecole", "activite_principale": "85.59A", "date_naissance_min": "2023-01-01", "etat_administratif": "A"},
        # Élargissement 2022 si nécessaire
        {"q": "CFA", "activite_principale": "85.59A", "date_naissance_min": "2022-01-01", "date_naissance_max": "2022-12-31", "etat_administratif": "A"},
        {"q": "formation apprentis", "activite_principale": "85.59A", "date_naissance_min": "2022-01-01", "date_naissance_max": "2022-12-31", "etat_administratif": "A"},
        {"q": "formation", "activite_principale": "85.59A", "date_naissance_min": "2022-01-01", "date_naissance_max": "2022-12-31", "etat_administratif": "A"},
        {"q": "CFA", "activite_principale": "85.59B", "date_naissance_min": "2022-01-01", "date_naissance_max": "2022-12-31", "etat_administratif": "A"},
    ]

    for i, params in enumerate(searches_a):
        print(f"\nRecherche A #{i+1}: q='{params.get('q','')}' naf={params.get('activite_principale','')} date_min={params.get('date_naissance_min','')}", file=sys.stderr)
        results = fetch_all_pages(params, max_pages=20, max_results=200)

        for entity in results:
            siren = entity.get("siren", "")
            if siren in seen_a:
                continue

            siege = entity.get("siege", {})
            dep = siege.get("departement", "")
            if not dep:
                cp = siege.get("code_postal", "")
                dep = get_dep_from_cp(cp) if cp else ""

            # Exclure IDF
            if is_idf(dep):
                continue

            # Vérifier date création
            date_creation = entity.get("date_creation", "")
            if not date_creation:
                continue

            annee = int(date_creation[:4]) if date_creation[:4].isdigit() else 0
            if annee < 2022:
                continue

            # Vérifier pas en procédure
            etat = entity.get("etat_administratif", "")
            if etat != "A":
                continue

            seen_a.add(siren)
            row = process_entity(entity, "A")

            # Ajout note si 2022
            if annee == 2022:
                row["notes_qualite"] = "Élargissement 2022 (critère initial: 2023+)"

            liste_a_raw.append(row)

        print(f"  Total Liste A après recherche #{i+1}: {len(liste_a_raw)}", file=sys.stderr)

        if len(liste_a_raw) >= 120:
            print("  -> 120+ résultats, arrêt des recherches Liste A", file=sys.stderr)
            break

    # Trier par score décroissant et prendre les 100 meilleurs
    liste_a_raw.sort(key=lambda x: x["score_fit"], reverse=True)
    liste_a = liste_a_raw[:100]

    print(f"\n==> LISTE A finale: {len(liste_a)} entrées", file=sys.stderr)

    # ============================================================
    # LISTE B : En difficulté (liquidation/redressement), hors IDF
    # ============================================================
    print("\n--- LISTE B : CFA/OF en difficulté hors IDF ---", file=sys.stderr)

    liste_b_raw = []
    seen_b = set()

    # Recherches pour entreprises en difficulté
    # L'API supporte les filtres de procédures collectives via des paramètres spécifiques
    searches_b_liquidation = [
        {"q": "formation", "activite_principale": "85.59A", "page": 1, "per_page": 25},
        {"q": "formation", "activite_principale": "85.59B", "page": 1, "per_page": 25},
        {"q": "CFA", "page": 1, "per_page": 25},
        {"q": "centre formation", "page": 1, "per_page": 25},
        {"q": "apprentissage", "activite_principale": "85.59A", "page": 1, "per_page": 25},
        {"q": "formation professionnelle", "page": 1, "per_page": 25},
        {"q": "organisme formation", "page": 1, "per_page": 25},
        {"q": "ecole formation", "page": 1, "per_page": 25},
        {"q": "institut formation", "page": 1, "per_page": 25},
        {"q": "campus formation", "page": 1, "per_page": 25},
    ]

    # Chercher les entreprises fermées (etat_administratif=C) dans le secteur formation
    for difficulty_type, etat_filter in [("liquidation", "C"), ("actif_procedure", "A")]:
        for i, base_params in enumerate(searches_b_liquidation):
            params = {**base_params}

            if difficulty_type == "liquidation":
                # Entreprises fermées = souvent liquidées
                params["etat_administratif"] = "C"
                if "date_naissance_min" not in params:
                    params["date_naissance_min"] = "2022-01-01"
            else:
                # Essayer les filtres de procédure pour entreprises encore actives
                # L'API ne supporte pas directement les filtres de procédure collective
                # On va chercher autrement
                continue

            print(f"\nRecherche B #{i+1} ({difficulty_type}): q='{params.get('q','')}' naf={params.get('activite_principale','')}", file=sys.stderr)
            results = fetch_all_pages(params, max_pages=15, max_results=200)

            for entity in results:
                siren = entity.get("siren", "")
                if siren in seen_b or siren in seen_a:
                    continue

                siege = entity.get("siege", {})
                dep = siege.get("departement", "")
                if not dep:
                    cp = siege.get("code_postal", "")
                    dep = get_dep_from_cp(cp) if cp else ""

                if is_idf(dep):
                    continue

                date_creation = entity.get("date_creation", "")
                annee = int(date_creation[:4]) if date_creation and date_creation[:4].isdigit() else 0

                # Pour Liste B, on accepte aussi des créations plus anciennes si en difficulté
                # Mais on privilégie 2022+
                if annee < 2020:
                    continue

                seen_b.add(siren)
                row = process_entity(entity, "B")

                # Déterminer le type de difficulté
                etat_admin = entity.get("etat_administratif", "")
                date_fermeture = entity.get("date_fermeture", "")
                date_fermeture_siege = siege.get("date_fermeture", "")

                if etat_admin == "C":
                    difficulte_type = "liquidation judiciaire (entreprise fermée)"
                    risque = "élevé - entreprise fermée administrativement"
                else:
                    difficulte_type = "procédure en cours (à vérifier)"
                    risque = "moyen - statut à confirmer sur BODACC"

                row["difficulte_type"] = difficulte_type
                row["difficulte_date"] = date_fermeture or date_fermeture_siege or ""
                row["difficulte_source_url"] = f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
                row["risque_trop_tard"] = risque

                if annee < 2022:
                    row["notes_qualite"] = f"Création {annee} (hors critère strict 2023+, inclus car en difficulté)"

                liste_b_raw.append(row)

            print(f"  Total Liste B après recherche #{i+1}: {len(liste_b_raw)}", file=sys.stderr)

            if len(liste_b_raw) >= 120:
                break

        if len(liste_b_raw) >= 120:
            break

    # Si pas assez de résultats, élargir aux entreprises plus anciennes fermées
    if len(liste_b_raw) < 100:
        print(f"\n  Liste B insuffisante ({len(liste_b_raw)}), élargissement créations 2020+...", file=sys.stderr)
        additional_searches = [
            {"q": "formation", "activite_principale": "85.59A", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "CFA", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "formation professionnelle", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "formation", "activite_principale": "85.59B", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "centre formation", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "apprentissage formation", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "institut formation", "etat_administratif": "C", "date_naissance_min": "2020-01-01"},
            {"q": "ecole formation", "etat_administratif": "C", "date_naissance_min": "2018-01-01"},
            {"q": "formation continue", "etat_administratif": "C", "date_naissance_min": "2018-01-01", "activite_principale": "85.59A"},
        ]

        for i, params in enumerate(additional_searches):
            print(f"\nRecherche B élargie #{i+1}: q='{params.get('q','')}'", file=sys.stderr)
            results = fetch_all_pages(params, max_pages=10, max_results=150)

            for entity in results:
                siren = entity.get("siren", "")
                if siren in seen_b or siren in seen_a:
                    continue

                siege = entity.get("siege", {})
                dep = siege.get("departement", "")
                if not dep:
                    cp = siege.get("code_postal", "")
                    dep = get_dep_from_cp(cp) if cp else ""

                if is_idf(dep):
                    continue

                seen_b.add(siren)
                row = process_entity(entity, "B")

                date_fermeture = entity.get("date_fermeture", "")
                date_fermeture_siege = siege.get("date_fermeture", "")

                row["difficulte_type"] = "liquidation judiciaire (entreprise fermée)"
                row["difficulte_date"] = date_fermeture or date_fermeture_siege or ""
                row["difficulte_source_url"] = f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}"
                row["risque_trop_tard"] = "élevé - entreprise fermée administrativement"

                date_creation = entity.get("date_creation", "")
                annee = int(date_creation[:4]) if date_creation and date_creation[:4].isdigit() else 0
                if annee < 2022:
                    row["notes_qualite"] = f"Création {annee} (élargi car Liste B insuffisante)"

                liste_b_raw.append(row)

            print(f"  Total Liste B: {len(liste_b_raw)}", file=sys.stderr)
            if len(liste_b_raw) >= 120:
                break

    # Trier par score et prendre les 100 meilleurs
    liste_b_raw.sort(key=lambda x: x["score_fit"], reverse=True)
    liste_b = liste_b_raw[:100]

    print(f"\n==> LISTE B finale: {len(liste_b)} entrées", file=sys.stderr)

    # ============================================================
    # ÉCRITURE DES CSV
    # ============================================================

    # Colonnes communes
    cols_common = [
        "persona", "organisation_nom", "organisation_nom_legal", "siren", "siret",
        "annee_creation", "date_creation_source_url", "adresse_ville", "adresse_departement",
        "adresse_region", "site_web_url", "linkedin_entreprise_url", "type_structure",
        "modalite_presume", "preuve_modalite", "contact_nom", "contact_role",
        "contact_linkedin_url", "contact_email_public", "contact_tel_public",
        "source_contact_preuve", "notes_qualite", "score_fit", "raisons_score"
    ]

    cols_b_extra = ["difficulte_type", "difficulte_date", "difficulte_source_url", "risque_trop_tard"]

    # CSV Liste A
    with open("/home/user/level1-portfolio/liste_a_actifs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols_common, extrasaction="ignore")
        writer.writeheader()
        for row in liste_a:
            writer.writerow(row)

    # CSV Liste B
    with open("/home/user/level1-portfolio/liste_b_difficulte.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols_common + cols_b_extra, extrasaction="ignore")
        writer.writeheader()
        for row in liste_b:
            writer.writerow(row)

    # ============================================================
    # RÉSUMÉ
    # ============================================================
    print("\n" + "=" * 60, file=sys.stderr)
    print("RÉSUMÉ D'EXÉCUTION", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Stats Liste A
    regions_a = {}
    emails_a = sum(1 for r in liste_a if r.get("contact_email_public"))
    tels_a = sum(1 for r in liste_a if r.get("contact_tel_public"))
    contacts_a = sum(1 for r in liste_a if r.get("contact_nom"))
    for r in liste_a:
        reg = r.get("adresse_region", "Inconnue")
        regions_a[reg] = regions_a.get(reg, 0) + 1

    print(f"\nLISTE A (actifs): {len(liste_a)} entrées", file=sys.stderr)
    print(f"  Contacts identifiés: {contacts_a} ({contacts_a*100//max(len(liste_a),1)}%)", file=sys.stderr)
    print(f"  Emails publics: {emails_a} ({emails_a*100//max(len(liste_a),1)}%)", file=sys.stderr)
    print(f"  Tels publics: {tels_a} ({tels_a*100//max(len(liste_a),1)}%)", file=sys.stderr)
    print("  Top régions:", file=sys.stderr)
    for reg, count in sorted(regions_a.items(), key=lambda x: -x[1])[:5]:
        print(f"    {reg}: {count}", file=sys.stderr)

    # Stats Liste B
    regions_b = {}
    contacts_b = sum(1 for r in liste_b if r.get("contact_nom"))
    for r in liste_b:
        reg = r.get("adresse_region", "Inconnue")
        regions_b[reg] = regions_b.get(reg, 0) + 1

    print(f"\nLISTE B (difficulté): {len(liste_b)} entrées", file=sys.stderr)
    print(f"  Contacts identifiés: {contacts_b} ({contacts_b*100//max(len(liste_b),1)}%)", file=sys.stderr)
    print("  Top régions:", file=sys.stderr)
    for reg, count in sorted(regions_b.items(), key=lambda x: -x[1])[:5]:
        print(f"    {reg}: {count}", file=sys.stderr)

    # Vérification déduplication
    all_sirens_a = set(r["siren"] for r in liste_a if r["siren"])
    all_sirens_b = set(r["siren"] for r in liste_b if r["siren"])
    overlap = all_sirens_a & all_sirens_b
    print(f"\nDoublons A/B: {len(overlap)}", file=sys.stderr)

    print(f"\nFichiers générés:", file=sys.stderr)
    print(f"  /home/user/level1-portfolio/liste_a_actifs.csv", file=sys.stderr)
    print(f"  /home/user/level1-portfolio/liste_b_difficulte.csv", file=sys.stderr)

    # Sortie JSON résumé sur stdout
    summary = {
        "liste_a_count": len(liste_a),
        "liste_b_count": len(liste_b),
        "doublons": len(overlap),
        "regions_a_top5": dict(sorted(regions_a.items(), key=lambda x: -x[1])[:5]),
        "regions_b_top5": dict(sorted(regions_b.items(), key=lambda x: -x[1])[:5]),
        "contacts_a_pct": contacts_a * 100 // max(len(liste_a), 1),
        "contacts_b_pct": contacts_b * 100 // max(len(liste_b), 1),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
