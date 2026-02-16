#!/usr/bin/env python3
"""
Fix type_structure classification and recalculate scores for both lists.
Many Liste B entries have 'inconnu' type despite being formation orgs.
"""

import csv
import sys
import re

def classify_type(nom, nom_legal, naf_code=""):
    """Classify org type based on name and NAF code."""
    nom_lower = (nom + " " + nom_legal).lower()

    if "cfa" in nom_lower or "apprenti" in nom_lower or "apprentissage" in nom_lower:
        return "CFA"
    elif any(x in nom_lower for x in ["formation", "ecole", "institut", "campus", "academy",
                                        "enseignement", "pedagogie", "didactique", "educati"]):
        return "OF"
    elif naf_code in ("85.59A", "85.59B", "8559A", "8559B", "85.32Z", "85.42Z"):
        return "OF"
    else:
        return "inconnu"

def classify_modalite(nom, type_struct):
    """Guess modality from name."""
    nom_lower = nom.lower()
    if any(x in nom_lower for x in ["digital", "numerique", "online", "e-learning", "distanciel", "distance"]):
        return "distanciel", "Mot-clé dans le nom suggère distanciel"
    elif any(x in nom_lower for x in ["campus", "centre", "cfa", "atelier", "labo"]):
        return "presentiel", "Mot-clé dans le nom suggère présentiel"
    elif type_struct == "CFA":
        return "presentiel", "CFA = généralement présentiel"
    else:
        return "inconnu", ""

def recalculate_score(row, is_liste_b=False):
    """Recalculate fit score based on all available data."""
    score = 0
    raisons = []

    nom_lower = row.get("organisation_nom", "").lower()
    type_s = row.get("type_structure", "")
    annee = row.get("annee_creation", "")
    dep = row.get("adresse_departement", "")
    contact = row.get("contact_nom", "")
    site = row.get("site_web_url", "")

    # Type scoring
    if type_s == "CFA":
        score += 30
        raisons.append("CFA identifié")
    elif type_s == "OF":
        score += 20
        raisons.append("Organisme de formation confirmé")

    # Date scoring
    if annee:
        try:
            y = int(annee)
            if y >= 2023:
                score += 20
                raisons.append(f"Création {annee} (critère principal)")
            elif y >= 2022:
                score += 10
                raisons.append(f"Création {annee} (élargissement)")
            elif y >= 2020:
                score += 5
                raisons.append(f"Création {annee} (élargissement étendu)")
        except ValueError:
            pass

    # Geo scoring
    idf = {"75", "77", "78", "91", "92", "93", "94", "95"}
    if dep and dep not in idf:
        score += 15
        raisons.append(f"Hors IDF ({dep})")

    # Contact scoring
    if contact:
        role = row.get("contact_role", "")
        score += 15
        raisons.append(f"Dirigeant: {role}" if role else "Dirigeant identifié")

    # Site/proof scoring
    if site:
        score += 10
        raisons.append("Fiche entreprise disponible")

    # Liste B specific
    if is_liste_b:
        diff = row.get("difficulte_type", "")
        if diff:
            score += 5
            raisons.append("Procédure confirmée")

    return min(score, 100), " | ".join(raisons[:3])

def fix_csv(path, is_liste_b=False):
    """Fix types and scores in a CSV file."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    fixed_types = 0
    for row in rows:
        nom = row.get("organisation_nom", "")
        nom_legal = row.get("organisation_nom_legal", "")

        # Fix type
        old_type = row.get("type_structure", "")
        new_type = classify_type(nom, nom_legal)
        if old_type == "inconnu" and new_type != "inconnu":
            row["type_structure"] = new_type
            fixed_types += 1
        elif old_type == "inconnu":
            row["type_structure"] = new_type

        # Fix modalite
        modalite, preuve = classify_modalite(nom, row["type_structure"])
        if row.get("modalite_presume", "") == "inconnu" or not row.get("modalite_presume"):
            row["modalite_presume"] = modalite
            if preuve:
                row["preuve_modalite"] = preuve

        # Recalculate score
        score, raisons = recalculate_score(row, is_liste_b)
        row["score_fit"] = str(score)
        row["raisons_score"] = raisons

    # Write back
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Stats
    types = {}
    for r in rows:
        t = r["type_structure"]
        types[t] = types.get(t, 0) + 1

    print(f"  {path}:", file=sys.stderr)
    print(f"  Types corrigés: {fixed_types}", file=sys.stderr)
    print(f"  Répartition types: {types}", file=sys.stderr)
    scores = [int(r["score_fit"]) for r in rows]
    print(f"  Scores: min={min(scores)}, max={max(scores)}, moy={sum(scores)//len(scores)}", file=sys.stderr)

def main():
    print("=== CORRECTION TYPES & SCORES ===", file=sys.stderr)
    fix_csv("/home/user/level1-portfolio/liste_a_actifs.csv", is_liste_b=False)
    fix_csv("/home/user/level1-portfolio/liste_b_difficulte.csv", is_liste_b=True)
    print("\nTerminé.", file=sys.stderr)

if __name__ == "__main__":
    main()
