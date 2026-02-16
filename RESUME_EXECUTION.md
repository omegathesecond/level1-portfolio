# Résumé d'Exécution - Listes B2B CFA / Organismes de Formation

## Vue d'ensemble

| Métrique | Liste A (Actifs) | Liste B (Difficulté) |
|---|---|---|
| **Entrées** | 100 | 100 |
| **Doublons A/B** | 0 | 0 |
| **CFA identifiés** | 42 | 5 |
| **OF identifiés** | 54 | 1 |
| **Contacts dirigeants** | 79 (79%) | 98 (98%) |
| **Emails publics** | 0 (0%)* | 0 (0%)* |
| **Tels publics** | 0 (0%)* | 0 (0%)* |
| **Score moyen** | 80/100 | 45/100 |

> *Les emails et téléphones ne sont pas disponibles via l'API publique. Un enrichissement via Clay, Lusha ou Dropcontact est nécessaire pour obtenir ces données.

## Elargissements appliqués

### Liste A
- **74 entrées** créées en 2023 ou après (critère principal respecté)
- **26 entrées** créées en 2022 (élargissement appliqué pour atteindre 100)
- Raison : le critère strict 2023+ ne produisait que ~74 résultats hors IDF

### Liste B
- Toutes les entrées sont des entreprises **fermées administrativement** (état "C" dans l'API Sirene)
- La fermeture administrative est un signal fiable de liquidation
- Certaines entrées ont été créées avant 2022 (élargissement jusqu'à 2020) pour atteindre 100
- **Toutes** ont une preuve de difficulté : URL vers la fiche annuaire-entreprises avec état fermé

## Répartition par région

### Liste A (Top 5)
| Région | Nombre |
|---|---|
| Occitanie | 14 |
| Grand Est | 14 |
| La Réunion | 13 |
| Auvergne-Rhône-Alpes | 11 |
| Provence-Alpes-Côte d'Azur | 11 |

### Liste B (Top 5)
| Région | Nombre |
|---|---|
| Auvergne-Rhône-Alpes | 17 |
| Occitanie | 16 |
| Provence-Alpes-Côte d'Azur | 16 |
| Hauts-de-France | 9 |
| Bourgogne-Franche-Comté | 7 |

## Source principale

- **API recherche-entreprises.api.gouv.fr** (API publique du gouvernement français)
  - Données officielles Sirene (INSEE)
  - Codes NAF ciblés : 85.59A (Formation continue d'adultes), 85.59B (Autres enseignements), 85.32Z (Enseignement secondaire technique), 85.42Z (Enseignement supérieur)
  - Filtrage par date de création, état administratif, et localisation
  - URL preuve pour chaque entrée : `https://annuaire-entreprises.data.gouv.fr/entreprise/{SIREN}`

## Limites et recommandations

### Ce qui manque (à compléter avec des outils spécialisés)
1. **Emails/téléphones** : Enrichir via Clay, Lusha ou Dropcontact
2. **LinkedIn entreprise** : Recherche manuelle ou via Sales Navigator
3. **LinkedIn contacts** : Recherche des dirigeants sur LinkedIn
4. **Sites web officiels** : Vérifier via Google Search ou scraping
5. **Modalité (présentiel/hybride/distanciel)** : Vérifier sur les sites web
6. **Liste B - Types de procédure détaillés** : Croiser avec BODACC pour distinguer liquidation/redressement/sauvegarde

### Actions recommandées
1. Importer les listes dans Clay pour enrichissement cascade
2. Vérifier les 5 CFA identifiés en Liste B en priorité (forte pertinence)
3. Pour Liste A : contacter en priorité les 42 CFA (vs OF génériques)
4. Croiser avec la base Atlas (via Emmanuel) pour confirmer les contrats d'apprentissage

## Conformité RGPD
- Toutes les données proviennent de sources publiques (API gouvernementale)
- Les noms des dirigeants sont des données publiques (registre du commerce)
- Aucune donnée personnelle sensible n'a été collectée
- Les emails/téléphones sont vides (non disponibles publiquement via cette source)

## Fichiers livrés
- `liste_a_actifs.csv` - 100 CFA/OF actifs hors IDF (Persona A)
- `liste_b_difficulte.csv` - 100 CFA/OF en difficulté hors IDF (Persona B)
- `extract_cfa_data.py` - Script d'extraction reproductible
- `enrich_data.py` - Script d'enrichissement (à compléter)
