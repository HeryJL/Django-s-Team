from django.test import TestCase
from django.urls import reverse

from interventions.models import Annonce, HistoriqueStatut, Signalement, Statut

from .helpers import creer_categorie, creer_gestionnaire, creer_signalement, creer_utilisateur


class AccesTests(TestCase):
    def setUp(self):
        self.alice = creer_utilisateur("alice")
        self.bob = creer_utilisateur("bob")
        self.manu = creer_gestionnaire("manu")
        self.s = creer_signalement(self.alice)

    # --- Restrictions d'accès ---
    def test_user_non_gestionnaire_ne_peut_pas_prendre_en_charge(self):
        self.client.force_login(self.bob)
        r = self.client.post(reverse("signalement_prendre_en_charge", args=[self.s.pk]))
        self.assertEqual(r.status_code, 403)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.NOUVELLE)

    def test_auteur_non_gestionnaire_ne_peut_pas_prendre_en_charge_sa_demande(self):
        self.client.force_login(self.alice)
        r = self.client.post(reverse("signalement_prendre_en_charge", args=[self.s.pk]))
        self.assertEqual(r.status_code, 403)

    def test_user_ne_peut_pas_retirer_signalement_autre(self):
        self.client.force_login(self.bob)
        r = self.client.post(reverse("signalement_retirer", args=[self.s.pk]))
        self.assertEqual(r.status_code, 403)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.NOUVELLE)

    def test_detail_d_autrui_interdit_mais_gestionnaire_autorise(self):
        url = reverse("signalement_detail", args=[self.s.pk])
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.manu)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_visiteur_redirige_vers_connexion(self):
        for nom, args in (("signalement_create", []), ("mes_signalements", []),
                          ("signalement_detail", [self.s.pk]), ("gestionnaire_dashboard", [])):
            r = self.client.get(reverse(nom, args=args))
            self.assertEqual(r.status_code, 302, nom)
            self.assertIn(reverse("login"), r["Location"], nom)

    def test_dashboard_interdit_aux_non_gestionnaires(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("gestionnaire_dashboard")).status_code, 403)

    def test_pages_publiques(self):
        for nom in ("accueil", "annonces", "login", "inscription"):
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200, nom)

    def test_anciennes_listes_globales_n_existent_plus(self):
        self.assertEqual(self.client.get("/signalements/").status_code, 404)
        self.assertEqual(self.client.get("/categories/").status_code, 404)

    def test_accueil_affiche_le_nombre_de_demandes_en_cours_par_categorie(self):
        categorie = creer_categorie("Électricité")
        demande = creer_signalement(self.alice, categorie=categorie)
        demande.changer_statut(Statut.EN_COURS, self.manu)
        response = self.client.get(reverse("accueil"))
        self.assertEqual(response.context["categories"].get(nom="Électricité").nb_en_cours, 1)

    def test_gestionnaire_n_a_pas_d_espace_demandeur(self):
        self.client.force_login(self.manu)
        self.assertRedirects(
            self.client.get(reverse("mes_signalements")),
            reverse("gestionnaire_dashboard"),
        )
        self.assertRedirects(
            self.client.get(reverse("signalement_create")),
            reverse("gestionnaire_dashboard"),
        )

    def test_mutations_refusent_get(self):
        self.client.force_login(self.manu)
        r = self.client.get(reverse("signalement_prendre_en_charge", args=[self.s.pk]))
        self.assertEqual(r.status_code, 405)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.NOUVELLE)

    def test_get_retrait_ne_modifie_rien(self):
        self.client.force_login(self.alice)
        r = self.client.get(reverse("signalement_retirer", args=[self.s.pk]))
        self.assertEqual(r.status_code, 200)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.NOUVELLE)

    def test_csrf_exige_sur_les_mutations(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manu)
        r = client.post(reverse("signalement_prendre_en_charge", args=[self.s.pk]))
        self.assertEqual(r.status_code, 403)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.NOUVELLE)


class FluxMetierTests(TestCase):
    def setUp(self):
        self.alice = creer_utilisateur("alice")
        self.manu = creer_gestionnaire("manu")
        self.s = creer_signalement(self.alice)

    def test_creation_via_formulaire(self):
        self.client.force_login(self.alice)
        cat = creer_categorie()
        r = self.client.post(reverse("signalement_create"), {
            "titre": "Fuite d'eau", "description": "Sous l'évier.", "lieu": "Bloc A",
            "priorite": "haute", "categorie": cat.pk,
        })
        nouveau = Signalement.objects.get(titre="Fuite d'eau")
        self.assertRedirects(r, reverse("signalement_detail", args=[nouveau.pk]))
        self.assertEqual(nouveau.demandeur, self.alice)
        self.assertEqual(nouveau.statut, Statut.NOUVELLE)

    def test_creation_sans_titre_affiche_erreur(self):
        self.client.force_login(self.alice)
        r = self.client.post(reverse("signalement_create"), {
            "titre": "", "description": "x", "lieu": "y", "priorite": "basse",
            "categorie": creer_categorie().pk,
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors.get("titre"))

    def test_gestionnaire_publie_une_annonce_visible_aux_utilisateurs(self):
        self.client.force_login(self.manu)
        response = self.client.post(reverse("annonce_create"), {
            "titre": "Maintenance planifiée",
            "contenu": "Le réseau sera indisponible samedi matin.",
        })
        self.assertRedirects(response, reverse("annonces"))
        annonce = Annonce.objects.get()
        self.assertEqual(annonce.auteur, self.manu)
        self.client.force_login(self.alice)
        response = self.client.get(reverse("annonces"))
        self.assertContains(response, "Maintenance planifiée")
        self.assertContains(response, "Le réseau sera indisponible samedi matin.")

    def test_demandeur_ne_peut_pas_faire_une_annonce(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("annonce_create")).status_code, 403)

    def test_retrait_par_l_auteur(self):
        self.client.force_login(self.alice)
        r = self.client.post(reverse("signalement_retirer", args=[self.s.pk]))
        self.assertRedirects(r, reverse("mes_signalements"))
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.RETIREE)

    def test_retrait_impossible_une_fois_en_cours(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        self.client.force_login(self.alice)
        self.client.post(reverse("signalement_retirer", args=[self.s.pk]))
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.EN_COURS)

    def test_gestionnaire_prend_en_charge_puis_resout(self):
        self.client.force_login(self.manu)
        self.client.post(reverse("signalement_prendre_en_charge", args=[self.s.pk]))
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.EN_COURS)
        r = self.client.post(reverse("signalement_resoudre", args=[self.s.pk]),
                             {"commentaire": "Ampoule changée."})
        self.assertRedirects(r, reverse("gestionnaire_dashboard"))
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.ATTENTE_VALIDATION)
        self.assertEqual(self.s.commentaire_resolution, "Ampoule changée.")
        self.client.force_login(self.alice)
        self.client.post(reverse("signalement_valider_fermeture", args=[self.s.pk]))
        self.client.force_login(self.manu)
        self.client.post(reverse("signalement_valider_fermeture", args=[self.s.pk]))
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.RESOLUE)
        self.assertEqual(HistoriqueStatut.objects.filter(signalement=self.s).count(), 3)

    def test_resolution_sans_commentaire_refusee(self):
        self.s.changer_statut(Statut.EN_COURS, self.manu)
        self.client.force_login(self.manu)
        r = self.client.post(reverse("signalement_resoudre", args=[self.s.pk]), {"commentaire": ""})
        self.assertEqual(r.status_code, 200)
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.EN_COURS)

    def test_discussion_accessible_aux_parties_du_signalement(self):
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse("signalement_detail", args=[self.s.pk]),
            {"contenu": "Le problème est-il toujours présent ?"},
        )
        self.assertRedirects(response, reverse("signalement_detail", args=[self.s.pk]))
        self.assertContains(
            self.client.get(reverse("signalement_detail", args=[self.s.pk])),
            "Le problème est-il toujours présent ?",
        )

    def test_resolution_directe_d_une_nouvelle_refusee(self):
        self.client.force_login(self.manu)
        self.client.post(reverse("signalement_resoudre", args=[self.s.pk]), {"commentaire": "ok"})
        self.s.refresh_from_db()
        self.assertEqual(self.s.statut, Statut.NOUVELLE)


class ListesTests(TestCase):
    def setUp(self):
        self.alice = creer_utilisateur("alice")
        self.manu = creer_gestionnaire("manu")

    def test_pagination_10_par_page(self):
        for i in range(12):
            creer_signalement(self.alice, titre=f"Demande {i:02d}")
        self.client.force_login(self.alice)
        r = self.client.get(reverse("mes_signalements"))
        self.assertEqual(len(r.context["page_obj"]), 10)
        self.assertEqual(r.context["page_obj"].paginator.num_pages, 2)
        r = self.client.get(reverse("mes_signalements"), {"page": 2})
        self.assertEqual(len(r.context["page_obj"]), 2)

    def test_recherche_et_filtre_etat(self):
        creer_signalement(self.alice, titre="Projecteur HS")
        s2 = creer_signalement(self.alice, titre="Fuite robinet")
        s2.changer_statut(Statut.EN_COURS, self.manu)
        self.client.force_login(self.alice)
        r = self.client.get(reverse("mes_signalements"), {"q": "fuite"})
        self.assertEqual([s.titre for s in r.context["page_obj"]], ["Fuite robinet"])
        r = self.client.get(reverse("mes_signalements"), {"statut": "nouvelle"})
        self.assertEqual([s.titre for s in r.context["page_obj"]], ["Projecteur HS"])

    def test_utilisateur_ne_voit_que_ses_demandes(self):
        bob = creer_utilisateur("bob")
        creer_signalement(bob, titre="Chez Bob")
        creer_signalement(self.alice, titre="Chez Alice")
        self.client.force_login(self.alice)
        r = self.client.get(reverse("mes_signalements"))
        self.assertEqual([s.titre for s in r.context["page_obj"]], ["Chez Alice"])

    def test_dashboard_tri_par_priorite(self):
        creer_signalement(self.alice, titre="B basse", priorite="basse")
        creer_signalement(self.alice, titre="A haute", priorite="haute")
        creer_signalement(self.alice, titre="C moyenne", priorite="moyenne")
        self.client.force_login(self.manu)
        r = self.client.get(reverse("gestionnaire_dashboard"))
        self.assertEqual([s.titre for s in r.context["nouvelles"]],
                         ["A haute", "C moyenne", "B basse"])


class DashboardStatsTests(TestCase):
    def test_cartes_de_statistiques(self):
        alice = creer_utilisateur("alice")
        manu = creer_gestionnaire("manu")
        creer_signalement(alice, titre="Une nouvelle")
        s2 = creer_signalement(alice, titre="Une en cours")
        s2.changer_statut(Statut.EN_COURS, manu)
        s3 = creer_signalement(alice, titre="Une résolue")
        s3.changer_statut(Statut.EN_COURS, manu)
        s3.changer_statut(Statut.ATTENTE_VALIDATION, manu, "Fait")
        s3.valider_fermeture(alice)
        s3.valider_fermeture(manu)
        self.client.force_login(manu)
        r = self.client.get(reverse("gestionnaire_dashboard"))
        self.assertEqual(r.context["stats"],
                         {"total": 3, "en_attente": 1, "en_cours": 1, "resolues": 1})

    def test_related_names_et_badges(self):
        alice = creer_utilisateur("alice")
        manu = creer_gestionnaire("manu")
        s = creer_signalement(alice)
        self.assertIn(s, alice.signalements_demandes.all())
        self.assertEqual(s.badge_statut, "bg-primary")
        s.changer_statut(Statut.EN_COURS, manu)
        self.assertIn(s, manu.signalements_pris_en_charge.all())
        self.assertEqual(s.badge_statut, "bg-warning text-dark")
        self.assertEqual(s.historiques.count(), 1)
