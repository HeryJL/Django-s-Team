from django.db import migrations

NOM_GROUPE = "Gestionnaires"


def creer_groupe(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name=NOM_GROUPE)


def supprimer_groupe(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=NOM_GROUPE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("interventions", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(creer_groupe, supprimer_groupe),
    ]
