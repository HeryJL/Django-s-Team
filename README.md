# Suivi des demandes d'intervention (Django)

Projet M1 GL — Université de Vakinankaratra — Thème 2.
Stack : Python 3.11+, Django 5.x, SQLite, Bootstrap 5 (CDN, style uniquement). Aucun service externe.

## Installation et lancement

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate          # crée db.sqlite3 + le groupe « Gestionnaires »
python manage.py seed_demo        # gestionnaire, 2 demandeurs, 3 catégories, 5 signalements
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/.

`seed_demo` génère des mots de passe aléatoires, **affichés une seule fois** dans le terminal
(aucun mot de passe n'est écrit dans le code). Comptes créés : `gestionnaire`, `alice`, `bob`.
Commande relançable sans doublons. Mot de passe perdu : `python manage.py changepassword gestionnaire`.


## Repartir d'une base propre

Après une mise à jour des migrations : supprimer `db.sqlite3`, puis relancer `migrate` et `seed_demo`.

## Créer un compte gestionnaire à la main

Un gestionnaire = membre du groupe **Gestionnaires** (ou superuser).

```bash
python manage.py createsuperuser           # pour accéder à /admin/
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
u = get_user_model().objects.get(username="mon_compte")
u.groups.add(Group.objects.get(name="Gestionnaires"))
```
Ou via /admin/ : Utilisateurs → l'utilisateur → Groupes → « Gestionnaires ».

## Tests et vérifications

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run   # doit afficher « No changes detected »
python manage.py check --deploy                     # avertissements attendus en dev (DEBUG, SECRET_KEY de dev, HTTPS/cookies)
python manage.py collectstatic --noinput            # optionnel
```

Pour la production : définir `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`.

## Routes principales

| URL | Nom | Accès |
|---|---|---|
| `/` | accueil | public |
| `/categories/` | categorie_list | public |
| `/signalements/` | signalement_list | public (sans description/demandeur ; retirées masquées) |
| `/signalements/nouveau/` | signalement_create | connecté |
| `/signalements/<id>/` | signalement_detail | auteur ou gestionnaire |
| `/signalements/<id>/retirer/` | signalement_retirer | auteur, statut « nouvelle » (GET = confirmation, POST = action) |
| `/signalements/<id>/prendre-en-charge/` | signalement_prendre_en_charge | gestionnaire, POST |
| `/signalements/<id>/resoudre/` | signalement_resoudre | gestionnaire (GET = formulaire, POST = action) |
| `/mes-signalements/` | mes_signalements | connecté |
| `/gestion/` | gestionnaire_dashboard | gestionnaire |
| `/admin/` | — | staff/superuser |

## Captures d'écran à produire (4)

Lancer `seed_demo` puis `runserver`, fenêtre ~1280 px de large.

1. **Liste** : connecté en `alice`, `/signalements/`, saisir « projecteur » dans la recherche (ou choisir un état) → capturer le tableau filtré.
2. **Formulaire** : `/signalements/nouveau/`, laisser le titre vide et envoyer → capturer le message d'erreur ; (option : seconde capture du formulaire rempli).
3. **Espace utilisateur** : `/mes-signalements/` en `alice` → capturer la liste avec dates, priorités, états ; puis ouvrir un signalement résolu pour montrer l'historique.
4. **Traitement gestionnaire** : se connecter en `gestionnaire`, `/gestion/` (tri par priorité), cliquer « Prendre en charge », puis « Résoudre » sur une demande en cours → capturer la page de résolution et le message de succès.

## Structure

```
gestion_interventions/
  manage.py, requirements.txt, requirements-postgres.txt, README.md, NOTE_DE_CONCEPTION.md
  config/           settings, urls, wsgi, asgi
  interventions/    models, forms, views, urls, admin, roles, migrations/, tests/,
                    templates/interventions/, management/commands/seed_demo.py, fixtures/
  templates/        base.html, 403.html, registration/ (connexion, inscription)
  static/css/app.css
```
`fixtures/` est vide : les données de démo sont produites par `seed_demo` (reproductible, sans mot de passe en clair).
