from django.test import TestCase

from interventions.forms import ResolutionForm, SignalementForm
from interventions.models import Categorie

from .helpers import creer_categorie


class SignalementFormTests(TestCase):
    def setUp(self):
        self.cat = creer_categorie()

    def donnees(self, **kw):
        d = {"titre": "Prise cassée", "description": "Étincelles.", "lieu": "Labo 2",
             "priorite": "haute", "categorie": self.cat.pk}
        d.update(kw)
        return d

    def test_formulaire_valide(self):
        self.assertTrue(SignalementForm(self.donnees()).is_valid())

    def test_titre_requis(self):
        form = SignalementForm(self.donnees(titre=""))
        self.assertFalse(form.is_valid())
        self.assertIn("titre", form.errors)

    def test_titre_trop_court(self):
        form = SignalementForm(self.donnees(titre="ab"))
        self.assertFalse(form.is_valid())
        self.assertIn("titre", form.errors)

    def test_priorite_invalide(self):
        self.assertFalse(SignalementForm(self.donnees(priorite="urgente")).is_valid())

    def test_categorie_inactive_refusee(self):
        inactive = Categorie.objects.create(nom="Archivée", actif=False)
        self.assertFalse(SignalementForm(self.donnees(categorie=inactive.pk)).is_valid())


class ResolutionFormTests(TestCase):
    def test_commentaire_obligatoire(self):
        self.assertFalse(ResolutionForm({"commentaire": ""}).is_valid())
        self.assertFalse(ResolutionForm({"commentaire": "   "}).is_valid())
        self.assertTrue(ResolutionForm({"commentaire": "Réparé."}).is_valid())
