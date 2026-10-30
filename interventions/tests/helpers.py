from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from interventions.models import Categorie, Priorite, Signalement
from interventions.roles import GROUPE_GESTIONNAIRES

User = get_user_model()


def creer_utilisateur(username="alice"):
    return User.objects.create_user(username=username)


def creer_gestionnaire(username="manu"):
    user = User.objects.create_user(username=username)
    groupe, _ = Group.objects.get_or_create(name=GROUPE_GESTIONNAIRES)
    user.groups.add(groupe)
    return user


def creer_categorie(nom="Informatique"):
    return Categorie.objects.get_or_create(nom=nom)[0]


def creer_signalement(demandeur, **kwargs):
    data = {
        "titre": "Projecteur en panne",
        "description": "Le projecteur ne s'allume plus.",
        "lieu": "Salle B12",
        "priorite": Priorite.MOYENNE,
        "categorie": creer_categorie(),
    }
    data.update(kwargs)
    return Signalement.objects.create(demandeur=demandeur, **data)
