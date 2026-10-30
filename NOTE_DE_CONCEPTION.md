# Note de conception — Suivi des demandes d'intervention (Thème 2)

M1 Génie Logiciel — Université de Vakinankaratra.

## 1. Thème et objectif

Dans un établissement, les pannes de matériel et problèmes de locaux sont signalés oralement : aucun suivi
centralisé, aucune trace de l'avancement. L'application web remplace ce circuit par un outil de signalement
et de suivi, de la demande jusqu'à sa résolution. Le **demandeur** dépose et suit ses problèmes ; le
**gestionnaire** retrouve les demandes prioritaires et consigne le traitement, sans perdre l'historique des statuts.

## 2. Rôles et droits

| Rôle | Définition | Droits |
|---|---|---|
| Visiteur | non connecté | accueil, catégories, liste publique (titre, catégorie, lieu, priorité, état, date), inscription, connexion |
| Utilisateur | connecté | tout ce qui précède + déposer un signalement, voir **ses** demandes, ouvrir le détail de **ses** demandes, retirer une demande « nouvelle » |
| Gestionnaire | membre du groupe `Gestionnaires` (ou superuser) | tableau de bord trié par priorité, voir tout détail, prendre en charge, résoudre |

Choix : le rôle est un **groupe Django** créé par migration (`0002`), pas un champ sur l'utilisateur. Un utilisateur connecté mais non autorisé reçoit **403** (page `403.html`) ; un visiteur est redirigé vers la connexion.
La liste publique n'expose ni description ni demandeur ; son lien vers le détail n'apparaît que pour l'auteur et les gestionnaires.

## 3. Modèle de données

```
User (auth) 1 ──< Signalement >── 1 Catégorie
User (auth) 0..1 ──< Signalement   (gestionnaire assigné)
Signalement 1 ──< HistoriqueStatut >── 0..1 User (auteur du changement)
```

**Catégorie** : `nom` (unique), `description`, `slug` (généré automatiquement), `actif`.

**Signalement** : `titre`, `description`, `lieu`, `priorite` (basse/moyenne/haute), `statut`
(nouvelle/en_cours/resolue/retiree), `categorie` (FK, PROTECT), `demandeur` (FK User, `related_name="signalements_demandes"`), `gestionnaire` (FK User, nullable, `related_name="signalements_pris_en_charge"`),
`commentaire_resolution`, `cree_le`, `maj_le`.

**HistoriqueStatut** : `signalement` (FK, `related_name="historiques"`), `ancien_statut`, `nouveau_statut`, `par` (FK User, SET_NULL), `commentaire`, `date`.
Indispensable pour respecter « sans perdre l'historique du statut » : chaque changement ajoute une ligne, aucune n'est modifiée ni supprimée par l'application.

Choix : la création d'un signalement n'écrit pas de ligne d'historique (ce n'est pas une transition) ; la date de création est affichée en tête de la chronologie.

## 4. Règles métier

Diagramme des transitions autorisées :

```
nouvelle ──(gestionnaire)──> en_cours ──(gestionnaire + commentaire)──> resolue
    └────(demandeur)────> retiree
```

| Transition | Qui | Conditions / effets |
|---|---|---|
| nouvelle → en_cours | gestionnaire | assigne le gestionnaire au signalement |
| en_cours → resolue | gestionnaire | commentaire de résolution non vide, enregistré |
| nouvelle → retiree | demandeur (auteur) | uniquement tant que la demande est « nouvelle » |
| tout le reste | — | refusé : `resolue` et `retiree` sont finaux ; `en_cours → retiree` est interdit ; `nouvelle → resolue` est interdit |

Implémentation : la méthode `Signalement.changer_statut(nouveau, user, commentaire)` est le **seul** point d'entrée.
Elle valide la transition (table `TRANSITIONS_AUTORISEES`), le rôle de l'acteur et le commentaire, lève `ValidationError` sinon,
puis met à jour le signalement et écrit l'`HistoriqueStatut` dans une même transaction `atomic`. Les vues se contentent
de l'appeler et d'afficher le message d'erreur ; les règles ne dépendent donc pas des vues. Les propriétés
`peut_etre_retire`, `peut_etre_pris_en_charge` et `peut_etre_resolu` pilotent l'affichage des boutons.
Dans l'admin, `statut`, `gestionnaire` et `commentaire_resolution` sont en lecture seule pour que l'historique ne soit jamais contourné.

## 5. Sécurité

- Toute opération qui modifie des données est un **POST protégé par CSRF** (`{% csrf_token %}`) ; `require_POST` renvoie 405 sur GET pour la prise en charge ; les pages de retrait et de résolution affichent d'abord une **confirmation** (GET sans effet) puis agissent sur POST. La déconnexion est aussi un POST.
- Autorisations dans les vues : `login_required` ; décorateur `gestionnaire_required` ; contrôle de propriété (auteur) pour détail et retrait.
- Formulaires validés côté serveur (titre ≥ 3 caractères, priorité et catégorie valides, catégorie active, commentaire obligatoire).
- Aucun mot de passe dans le code : `seed_demo` génère des mots de passe aléatoires affichés une fois.

## 6. Interface

`base.html` (Bootstrap 5 par CDN, style uniquement) avec navbar conditionnelle visiteur / utilisateur / gestionnaire et bloc de messages
succès/erreur/avertissement. Pages : accueil, catégories, liste (recherche par titre, filtre par état, pagination de 10), détail avec
chronologie de l'historique (badges de statut : nouvelle bleu, en cours jaune, résolue vert, retirée gris), formulaire de création, confirmation de retrait, formulaire de résolution, tableau de bord (cartes de statistiques : total, en attente, en cours, résolues ; puis nouvelles et en cours,
triées par priorité haute → basse puis date), connexion, inscription.

## 7. Tests (`python manage.py test`)

- Validation : titre requis (modèle et formulaire), titre trop court, priorité invalide, catégorie inactive refusée, commentaire de résolution requis.
- Règles métier : `retiree → resolue`, `nouvelle → resolue`, `en_cours → retiree` refusés ; résolution sans commentaire refusée ; seul le demandeur retire ; historique écrit à chaque transition (et pas en cas de refus).
- Accès : non-gestionnaire → 403 sur prise en charge ; retrait du signalement d'autrui → 403 ; détail d'autrui → 403 ; visiteur redirigé ; CSRF exigé ; GET sans effet.
- Listes : pagination, recherche, filtre, isolation entre utilisateurs, tri par priorité.

## 8. Limites assumées

Pas de notification par e-mail, pas de pièces jointes, pas de réouverture d'une demande résolue (une nouvelle demande est à créer).
Pas de verrouillage concurrent entre deux gestionnaires (SQLite, usage local).
