# Fonctionnalités ajoutées depuis `main`

Cette branche regroupe les évolutions réalisées depuis le dernier commit de
`main` (`2b96c43`).

## Accès et navigation

- Suppression des listes globales `/signalements/` et `/categories/`.
- Accueil `/` enrichi avec les catégories actives et le nombre de signalements
  « en cours » par catégorie.
- Espace `/mes-signalements/` réservé au demandeur connecté.
- Accès gestionnaire séparé avec un tableau de bord de traitement.
- Les gestionnaires sont redirigés vers leur tableau de bord lorsqu'ils
  tentent d'ouvrir l'espace demandeur ou le formulaire de création.

## Catégories et signalements

- Ajout de huit catégories de démonstration couvrant notamment le matériel,
  les locaux, le réseau, l'électricité, la plomberie, la sécurité et la
  propreté.
- Conservation des recherches et filtres dans l'espace personnel du demandeur.
- Conservation des demandes fermées et retirées dans l'historique du demandeur
  et du gestionnaire.

## Annonces

- Ajout du modèle `Annonce`.
- Ajout de la page publique `/annonces/`.
- Ajout du formulaire gestionnaire `/annonces/nouveau/`.
- Publication limitée aux gestionnaires.
- Affichage des annonces à tous les utilisateurs de l'application.
- Ajout de la gestion des annonces dans l'administration Django.

## Discussion par signalement

- Ajout du modèle `MessageSignalement`.
- Discussion privée entre le demandeur et le gestionnaire assigné.
- Enregistrement de l'auteur, du contenu et de la date de chaque message.
- Consultation et envoi de messages depuis la page de détail du signalement.
- Historique des discussions conservé après la fermeture du signalement.

## Validation de fermeture

- Ajout du statut « En attente de validation ».
- Le gestionnaire propose la fin du traitement avec un commentaire.
- Le demandeur et le gestionnaire assigné valident séparément la fermeture.
- Le signalement devient « Résolue » uniquement après les deux validations.
- Chaque validation et la fermeture finale sont conservées dans l'historique
  des statuts.
- Un refus motivé repasse le signalement à « En cours ».
- Les transitions incohérentes restent interdites.

## Données, administration et qualité

- Ajout des migrations pour les annonces, les messages et les validations.
- Ajout de l'administration des annonces et des messages.
- Mise à jour de la commande `seed_demo`.
- Mise à jour du README et de la note de conception.
- Ajout et adaptation des tests d'accès, de discussion, de validation et de
  conservation de l'historique.

## Validation effectuée

- 46 tests Django réussis.
- `manage.py check` réussi.
- Aucune migration manquante avec
  `manage.py makemigrations --check --dry-run`.
