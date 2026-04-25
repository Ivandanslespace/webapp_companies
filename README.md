# Panorama des Entreprises — application web Dash

Application web de visualisation financière (thème clair) basée sur Dash et dash-mantine-components, centrée sur l’entreprise : descriptions (DES) et actualités des trois derniers mois (NEWS).

## Démarrage

```bash
pip install -r requirements.txt
python app.py
```

Accès par défaut : <http://127.0.0.1:8050>.

## Architecture

Couches séparées : **l’UI ne lit jamais de DataFrame directement** ; tout passe par `CompanyRepository`.

```
src/
├── data/         # Parquet, loaders, point d’entrée repository
├── services/     # Filtres, extraits Markdown (fonctions pures, testables)
├── ui/           # Thème, layout, composants, pages
├── callbacks/    # Un fichier par page, orchestration des callbacks
└── assets/       # CSS global chargé par Dash
```

## Étendre avec un nouveau jeu de fondamentaux (3 étapes)

Exemple : ajouter `fundamentals.parquet` (indicateurs financiers) :

1. Ajouter `load_fundamentals()` dans `src/data/loaders.py`.
2. Exposer `get_fundamentals(isin)` sur `CompanyRepository` dans `src/data/repository.py`.
3. Ajouter un onglet ou un composant dans `src/ui/pages/company_detail.py` et les callbacks associés dans `src/callbacks/company_detail.py`.

Le code existant peut rester **inchangé** en dehors de ces ajouts.

## Tests

```bash
pytest
```

## Conventions

- Commentaires de code : **français ou anglais** uniquement.
- Préférer des changements ciblés et modulaires, sans régression inutile.
