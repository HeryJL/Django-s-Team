from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.crypto import get_random_string

from interventions.models import Categorie, Priorite, Signalement, Statut
from interventions.roles import GROUPE_GESTIONNAIRES

CATEGORIES = [
    ("Matériel informatique", "Ordinateurs, projecteurs, imprimantes."),
    ("Locaux & Mobilier", "Salles, chaises, tables, portes, électricité, plomberie."),
    ("Réseau & Connexion", "Wi-Fi, câblage, accès Internet."),
]

DEMO = [
    ("Projecteur en panne en salle B12", "Le projecteur ne s'allume plus depuis lundi.",
     "Salle B12", Priorite.HAUTE, "Matériel informatique", "alice", Statut.NOUVELLE),
    ("Fuite d'eau dans les toilettes du bloc A", "Une fuite sous le lavabo inonde le sol.",
     "Bloc A, RDC", Priorite.HAUTE, "Locaux & Mobilier", "bob", Statut.EN_COURS),
    ("Prise électrique défectueuse au labo info", "La prise du poste 4 produit des étincelles.",
     "Labo info", Priorite.MOYENNE, "Locaux & Mobilier", "alice", Statut.RESOLUE),
    ("Chaise cassée en amphi 2", "Un pied de chaise est cassé (rangée 3).",
     "Amphi 2", Priorite.BASSE, "Locaux & Mobilier", "bob", Statut.RETIREE),
    ("Wi-Fi instable à la bibliothèque", "La connexion saute toutes les dix minutes.",
     "Bibliothèque", Priorite.MOYENNE, "Réseau & Connexion", "bob", Statut.NOUVELLE),
]


class Command(BaseCommand):
    help = ("Crée le groupe Gestionnaires, 1 gestionnaire, 2 demandeurs, 3 catégories et "
            "5 signalements couvrant tous les statuts. Idempotent. Mots de passe générés "
            "aléatoirement et affichés une seule fois.")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        groupe, _ = Group.objects.get_or_create(name=GROUPE_GESTIONNAIRES)
        generes = {}

        def utilisateur(username, gestionnaire=False):
            user, cree = User.objects.get_or_create(username=username)
            if cree:
                mot_de_passe = get_random_string(16)
                user.set_password(mot_de_passe)
                user.save()
                generes[username] = mot_de_passe
            if gestionnaire:
                user.groups.add(groupe)
            return user

        gestionnaire = utilisateur("gestionnaire", gestionnaire=True)
        demandeurs = {"alice": utilisateur("alice"), "bob": utilisateur("bob")}
        categories = {nom: Categorie.objects.get_or_create(nom=nom, defaults={"description": desc})[0]
                      for nom, desc in CATEGORIES}

        crees = 0
        for titre, description, lieu, priorite, cat, demandeur, cible in DEMO:
            s, cree = Signalement.objects.get_or_create(
                titre=titre,
                defaults={"description": description, "lieu": lieu, "priorite": priorite,
                          "categorie": categories[cat], "demandeur": demandeurs[demandeur]},
            )
            if not cree:
                continue
            crees += 1
            if cible in (Statut.EN_COURS, Statut.RESOLUE):
                s.changer_statut(Statut.EN_COURS, gestionnaire)
            if cible == Statut.RESOLUE:
                s.changer_statut(Statut.RESOLUE, gestionnaire, "Prise remplacée par l'électricien.")
            if cible == Statut.RETIREE:
                s.changer_statut(Statut.RETIREE, s.demandeur, "Doublon, déjà signalé.")

        self.stdout.write(self.style.SUCCESS(
            f"Démo prête : {len(categories)} catégories, {crees} signalement(s) créé(s)."))
        if generes:
            self.stdout.write(self.style.WARNING(
                "Mots de passe générés (affichés UNE SEULE FOIS, notez-les) :"))
            for nom, mdp in generes.items():
                self.stdout.write(f"  {nom} : {mdp}")
        else:
            self.stdout.write("Comptes déjà existants : mots de passe inchangés "
                              "(python manage.py changepassword <nom> pour en définir un).")
