from django.core.exceptions import ValidationError
from django.test import TestCase

from interventions.models import HistoriqueStatut, Priorite, Signalement, Statut

from .helpers import creer_categorie, creer_gestionnaire, creer_signalement, creer_utilisateur


class ValidationDonneesTests(TestCase):
    def test_creation_signalement_champs_requis(self):
        """Un signalement sans titre est refusé par la validation du modèle."""
        alice = creer_utilisateur()
        s = Signalement(
            titre="", description="x", lieu="Salle B12", priorite=Priorite.HAUTE,
            categorie=creer_categorie(), demandeur=alice,
        )
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("titre", ctx.exception.message_dict)


class TransitionsTests(TestCase):
    def setUp(self):
        self.alice = creer_utilisateur("alice")
        self.bob = creer_utilisateur("bob")
        self.manu = creer_gestionnaire("manu")
        self.s = creer_signalement(self.alice)

    def test_transition_invalide_retiree_vers_resolue(self):
        self.s.changer_statut(Statut.RETIREE, self.alice)
        with self.assertRaises(ValidationError):
            self.s.changer_statut(Statut.RESOLUE, self.manu, "Réparé")
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.RETIREE)

    def test_nouvelle_vers_resolue_directement_interdit(self):
        with self.assertRaises(ValidationError):
            self.s.changer_statut(Statut.RESOLUE, self.manu, "Réparé")

    def test_en_cours_vers_retiree_interdit(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        with self.assertRaises(ValidationError):
            self.s.changer_statut(Statut.RETIREE, self.alice)

    def test_resolution_exige_commentaire(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        for vide in ("", "   "):
            with self.assertRaises(ValidationError):
                self.s.changer_statut(Statut.ATTENTE_VALIDATION, self.manu, vide)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.EN_COURS)

    def test_prise_en_charge_assigne_le_gestionnaire(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.EN_COURS)
        self.assertEqual(self.s.gestionnaire, self.manu)

    def test_utilisateur_simple_ne_peut_pas_prendre_en_charge(self):
        with self.assertRaises(ValidationError):
            self.s.changer_statut(Statut.EN_COURS, self.bob)

    def test_seul_le_demandeur_peut_retirer(self):
        with self.assertRaises(ValidationError):
            self.s.changer_statut(Statut.RETIREE, self.bob)
        self.s.changer_statut(Statut.RETIREE, self.alice)
        self.assertEqual(self.s.statut, Statut.RETIREE)

    def test_historique_cree_a_chaque_transition(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        self.s.changer_statut(Statut.ATTENTE_VALIDATION, self.manu, "Ampoule remplacée")
        self.s.valider_fermeture(self.alice)
        self.s.valider_fermeture(self.manu)
        lignes = list(HistoriqueStatut.objects.filter(signalement=self.s))
        self.assertEqual(len(lignes), 3)
        self.assertEqual((lignes[0].ancien_statut, lignes[0].nouveau_statut),
                         (Statut.NOUVELLE, Statut.EN_COURS))
        self.assertEqual((lignes[1].ancien_statut, lignes[1].nouveau_statut),
                         (Statut.EN_COURS, Statut.ATTENTE_VALIDATION))
        self.assertEqual(lignes[1].commentaire, "Ampoule remplacée")
        self.assertEqual((lignes[2].ancien_statut, lignes[2].nouveau_statut),
                         (Statut.ATTENTE_VALIDATION, Statut.RESOLUE))

    def test_fermeture_exige_les_deux_validations(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        self.s.changer_statut(Statut.ATTENTE_VALIDATION, self.manu, "Travaux terminés")
        self.s.valider_fermeture(self.alice)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.ATTENTE_VALIDATION)
        self.assertTrue(self.s.validation_demandeur)
        self.s.valider_fermeture(self.manu)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.RESOLUE)

    def test_transition_refusee_n_ecrit_pas_d_historique(self):
        with self.assertRaises(ValidationError):
            self.s.changer_statut(Statut.RESOLUE, self.manu, "ok")
        self.assertEqual(HistoriqueStatut.objects.count(), 0)
