import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Categorie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=100, unique=True, verbose_name="nom")),
                ("description", models.TextField(blank=True, verbose_name="description")),
                ("slug", models.SlugField(blank=True, editable=False, max_length=120, unique=True, verbose_name="slug")),
                ("actif", models.BooleanField(default=True, verbose_name="active")),
            ],
            options={
                "verbose_name": "catégorie",
                "verbose_name_plural": "catégories",
                "ordering": ["nom"],
            },
        ),
        migrations.CreateModel(
            name="Signalement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titre", models.CharField(max_length=200, verbose_name="titre")),
                ("description", models.TextField(verbose_name="description")),
                ("lieu", models.CharField(max_length=150, verbose_name="lieu")),
                ("priorite", models.CharField(choices=[("basse", "Basse"), ("moyenne", "Moyenne"), ("haute", "Haute")], default="moyenne", max_length=10, verbose_name="priorité")),
                ("statut", models.CharField(choices=[("nouvelle", "Nouvelle"), ("en_cours", "En cours"), ("resolue", "Résolue"), ("retiree", "Retirée")], default="nouvelle", max_length=10, verbose_name="statut")),
                ("commentaire_resolution", models.TextField(blank=True, verbose_name="commentaire de résolution")),
                ("cree_le", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("maj_le", models.DateTimeField(auto_now=True, verbose_name="mis à jour le")),
                ("categorie", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="signalements", to="interventions.categorie", verbose_name="catégorie")),
                ("demandeur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="signalements_demandes", to=settings.AUTH_USER_MODEL, verbose_name="demandeur")),
                ("gestionnaire", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="signalements_pris_en_charge", to=settings.AUTH_USER_MODEL, verbose_name="gestionnaire")),
            ],
            options={
                "verbose_name": "signalement",
                "verbose_name_plural": "signalements",
                "ordering": ["-cree_le"],
            },
        ),
        migrations.CreateModel(
            name="HistoriqueStatut",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ancien_statut", models.CharField(choices=[("nouvelle", "Nouvelle"), ("en_cours", "En cours"), ("resolue", "Résolue"), ("retiree", "Retirée")], max_length=10, verbose_name="ancien statut")),
                ("nouveau_statut", models.CharField(choices=[("nouvelle", "Nouvelle"), ("en_cours", "En cours"), ("resolue", "Résolue"), ("retiree", "Retirée")], max_length=10, verbose_name="nouveau statut")),
                ("commentaire", models.TextField(blank=True, verbose_name="commentaire")),
                ("date", models.DateTimeField(auto_now_add=True, verbose_name="date")),
                ("par", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="par")),
                ("signalement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historiques", to="interventions.signalement", verbose_name="signalement")),
            ],
            options={
                "verbose_name": "historique de statut",
                "verbose_name_plural": "historiques de statut",
                "ordering": ["date", "id"],
            },
        ),
    ]
