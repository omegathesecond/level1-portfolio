#!/usr/bin/env python3
"""
Enrichissement avec la Liste Publique des Organismes de Formation (DGEFP).
Croise les SIREN de nos listes avec la base officielle DGEFP pour :
- Confirmer le statut CFA (certifications.actionsDeFormationParApprentissage)
- Confirmer le statut OF
- Ajouter les spécialités de formation
- Ajouter le nombre de stagiaires
"""

import csv
import sys

def load_dgefp(path="/tmp/liste_of.csv"):
    """Charge la base DGEFP indexée par SIREN."""
    db = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            siren = row.get("siren", "").strip().strip('"')
            if siren:
                # Keep first occurrence per SIREN (or override if CFA)
                is_cfa = row.get("certifications.actionsDeFormationParApprentissage", "").strip().lower() == "true"
                is_of = row.get("certifications.actionsDeFormation", "").strip().lower() == "true"
                denom = row.get("denomination", "").strip().strip('"')
                specialite1 = row.get("informationsDeclarees.specialitesDeFormation.libelleSpecialite1", "").strip().strip('"')
                nb_stagiaires = row.get("informationsDeclarees.nbStagiaires", "").strip().strip('"')

                if siren not in db or is_cfa:
                    db[siren] = {
                        "is_cfa": is_cfa,
                        "is_of": is_of,
                        "denomination": denom,
                        "specialite": specialite1,
                        "nb_stagiaires": nb_stagiaires,
                    }
    return db

def enrich_list(csv_path, dgefp_db, is_liste_b=False):
    """Enrichit un CSV avec les données DGEFP."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    matched = 0
    upgraded_cfa = 0
    for row in rows:
        siren = row.get("siren", "")
        if siren in dgefp_db:
            matched += 1
            info = dgefp_db[siren]

            # Upgrade type_structure if confirmed CFA
            if info["is_cfa"] and row.get("type_structure") != "CFA":
                row["type_structure"] = "CFA"
                upgraded_cfa += 1

            # Confirm OF status
            if info["is_of"] and row.get("type_structure") == "inconnu":
                row["type_structure"] = "OF"

            # Add notes about speciality and nb stagiaires
            notes = row.get("notes_qualite", "")
            if info["specialite"]:
                spec_note = f"Spécialité DGEFP: {info['specialite'][:60]}"
                if spec_note not in notes:
                    notes = (notes + " | " + spec_note) if notes else spec_note
            if info["nb_stagiaires"]:
                stag_note = f"{info['nb_stagiaires']} stagiaires déclarés"
                if stag_note not in notes:
                    notes = (notes + " | " + stag_note) if notes else stag_note
            row["notes_qualite"] = notes

            # Boost score for DGEFP confirmed
            score = int(row.get("score_fit", 0))
            raisons = row.get("raisons_score", "")
            if "DGEFP" not in raisons:
                score = min(score + 5, 100)
                raisons = (raisons + " | Confirmé base DGEFP") if raisons else "Confirmé base DGEFP"
                row["score_fit"] = str(score)
                row["raisons_score"] = raisons

    # Write back
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"  {csv_path}:", file=sys.stderr)
    print(f"    Matchs DGEFP: {matched}/{len(rows)}", file=sys.stderr)
    print(f"    Upgradés CFA: {upgraded_cfa}", file=sys.stderr)

    # Type stats
    types = {}
    for r in rows:
        t = r["type_structure"]
        types[t] = types.get(t, 0) + 1
    print(f"    Types: {types}", file=sys.stderr)

    scores = [int(r["score_fit"]) for r in rows]
    print(f"    Scores: min={min(scores)}, max={max(scores)}, moy={sum(scores)//len(scores)}", file=sys.stderr)

def main():
    print("=== ENRICHISSEMENT DGEFP ===", file=sys.stderr)
    print("Chargement base DGEFP (151k entrées)...", file=sys.stderr)
    db = load_dgefp()
    print(f"  {len(db)} SIREN uniques chargés", file=sys.stderr)
    cfa_count = sum(1 for v in db.values() if v["is_cfa"])
    print(f"  Dont {cfa_count} CFA (apprentissage)", file=sys.stderr)

    print("\nEnrichissement Liste A...", file=sys.stderr)
    enrich_list("/home/user/level1-portfolio/liste_a_actifs.csv", db, is_liste_b=False)

    print("\nEnrichissement Liste B...", file=sys.stderr)
    enrich_list("/home/user/level1-portfolio/liste_b_difficulte.csv", db, is_liste_b=True)

    print("\nTerminé.", file=sys.stderr)

if __name__ == "__main__":
    main()
