#!/usr/bin/env python3
"""
Enrichissement de la Liste B avec les données BODACC détaillées.
Croise les SIREN de la Liste B avec les résultats BODACC pour préciser
le type de procédure et la date.
"""

import csv
import sys

# Données BODACC extraites de la recherche (SIREN -> infos procédure)
BODACC_DATA = {
    # Redressement judiciaire
    "354057705": {"type": "redressement judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/354057705", "nom": "FORMATION", "ville": "Montpellier"},
    "340615012": {"type": "redressement judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/340615012", "nom": "EDUCATION ET FORMATION", "ville": "Rouen"},
    "400734448": {"type": "redressement judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/400734448", "nom": "INNOVATION DEVELOPPEMENT FORMATION (IDF)", "ville": "Lille"},
    "398397927": {"type": "redressement judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/398397927", "nom": "VIA FORMATION", "ville": "Le Mans"},
    "902545060": {"type": "redressement judiciaire", "date": "2024-2025", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "DS FORMATION", "ville": "Saint-Memmie"},
    "792767873": {"type": "redressement judiciaire (plan)", "date": "2024-11-07", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "PCCF", "ville": "Nice"},

    # Liquidation judiciaire (BODACC confirmé)
    "388232779": {"type": "liquidation judiciaire", "date": "2009", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "EXA FORMATION", "ville": "Poitiers"},
    "878834563": {"type": "liquidation judiciaire (vente)", "date": "2020-02-26", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "SPORT ACADEMY FORMATION", "ville": "Pau"},
    "523432839": {"type": "liquidation judiciaire (clôture insuffisance actif)", "date": "2022-05-20", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "FORMATION.COUPDEFOUET", "ville": "Mâcon"},
    "800953564": {"type": "liquidation judiciaire (vente)", "date": "2024-02-06", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "MERCURE FORMATION", "ville": "Montauban"},
    "834476905": {"type": "liquidation judiciaire (radiation)", "date": "2025-09-30", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "FORMATIONVENTECONSEIL", "ville": "Montauban"},
    "842171274": {"type": "liquidation judiciaire", "date": "2025-11-28", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "AMMA FORMATION", "ville": "Verberie"},
    "807718085": {"type": "liquidation judiciaire (clôture insuffisance actif)", "date": "2018-07-29", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "B3A FORMATION", "ville": "Orvault"},
    "901869735": {"type": "liquidation judiciaire", "date": "2024-09-27", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "CFAB", "ville": "Vallauris"},
    "399111939": {"type": "liquidation judiciaire (clôture insuffisance actif)", "date": "2018-01-14", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "CFA Holding", "ville": "Troyes"},
    "840276646": {"type": "liquidation judiciaire (radiation)", "date": "2023-03-29", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "SASU CFO-CFA", "ville": "Wissant"},
    "397855875": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/397855875", "nom": "CFP MALUS", "ville": "Bourges"},
    "435086285": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/435086285", "nom": "CENTRE EUROPEEN DE FORMATION", "ville": "Villeneuve-d'Ascq"},
    "323590786": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/323590786", "nom": "CENTRE DE FORMATION TRANSPORT", "ville": "Isques"},
    "402912620": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/402912620", "nom": "CENTRE FORMATION PRESQU'ILE", "ville": "Saint-Nazaire"},
    "820141224": {"type": "liquidation judiciaire (fermée 2022-05-09)", "date": "2022-05-09", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/820141224", "nom": "CENTRE FORMATION", "ville": "Bourges"},
    "389602707": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/389602707", "nom": "CENTRE DE FORMATION WANTZ", "ville": "Aspach-le-Bas"},
    "485256549": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/485256549", "nom": "CENTRE DE FORMATION BLANCHARD", "ville": "Dreux"},
    "315844837": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/315844837", "nom": "CENTRE DE FORMATION ROUTIERE MARIONNEAU", "ville": "Bellevigny"},
    "309135796": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/309135796", "nom": "CENTRE DE FORMATION PIGNON", "ville": "Sarrebourg"},
    "533387833": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/533387833", "nom": "CENTRE DE FORMATION LANGUES", "ville": "Les Sables d'Olonne"},
    "502694367": {"type": "liquidation judiciaire", "date": "2024", "source": "https://annuaire-entreprises.data.gouv.fr/entreprise/502694367", "nom": "AF2R - APPRENTISSAGE ET FORMATION AUX RISQUES ROUTIERS", "ville": "Pluneret"},

    # Dissolution / cessation
    "839653862": {"type": "dissolution sans liquidation", "date": "2024-11-24", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "JC FORMATION", "ville": "Lyon"},
    "891988818": {"type": "dissolution", "date": "2022-04-13", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "COENEV FORMATION", "ville": "Rennes"},
    "844555250": {"type": "dissolution", "date": "2025-08-18", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "KAPH FORMATION", "ville": "Burtoncourt"},
    "824814164": {"type": "dissolution", "date": "2025-11-11", "source": "https://bodacc-datadila.opendatasoft.com/", "nom": "EOLE FORMATION", "ville": "Bruz"},
}

def enrich_liste_b():
    """Enrichit la Liste B avec les données BODACC."""
    input_path = "/home/user/level1-portfolio/liste_b_difficulte.csv"

    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    enriched = 0
    for row in rows:
        siren = row.get("siren", "")
        if siren in BODACC_DATA:
            bd = BODACC_DATA[siren]
            # Update with more precise BODACC data
            if bd.get("type"):
                row["difficulte_type"] = bd["type"]
            if bd.get("date"):
                row["difficulte_date"] = bd["date"]
            if bd.get("source"):
                row["difficulte_source_url"] = bd["source"]

            # Update risk level
            dtype = bd.get("type", "").lower()
            if "clôture" in dtype or "radiation" in dtype:
                row["risque_trop_tard"] = "élevé - procédure clôturée/radiée (BODACC)"
            elif "redressement" in dtype:
                row["risque_trop_tard"] = "faible - en redressement, possibilité d'intervention"
            elif "dissolution" in dtype:
                row["risque_trop_tard"] = "moyen - dissolution en cours"
            elif "vente" in dtype:
                row["risque_trop_tard"] = "élevé - vente en liquidation judiciaire"
            else:
                row["risque_trop_tard"] = "élevé - entreprise fermée (BODACC confirmé)"

            enriched += 1

    # Write back
    with open(input_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Liste B enrichie: {enriched} entrées mises à jour avec données BODACC", file=sys.stderr)

if __name__ == "__main__":
    enrich_liste_b()
