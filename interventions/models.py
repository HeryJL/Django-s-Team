from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Case, IntegerField, Value, When
from django.urls import reverse
from django.utils.text import slugify

from .roles import est_gestionnaire


class Statut(models.TextChoices):
    NOUVELLE = "nouvelle", "Nouvelle"
    EN_COURS = "en_cours", "En cours"
    RESOLUE = "resolue", "Résolue"
    RETIREE = "retiree", "Retirée"


class Priorite(models.TextChoices):
    BASSE = "basse", "Basse"
    MOYENNE = "moyenne", "Moyenne"
    HAUTE = "haute", "Haute"


# Seules transitions possibles. retiree et resolue sont des états finaux.
TRANSITIONS_AUTORISEES = {
    Statut.NOUVELLE.value: {Statut.EN_COURS.value, Statut.RETIREE.value},
    Statut.EN_COURS.value: {Statut.RESOLUE.value},
    Statut.RESOLUE.value: set(),
    Statut.RETIREE.value: set(),
}

# Classes Bootstrap complètes des badges de statut (bleu / jaune / vert / gris).
BADGES_STATUT = {
    Statut.NOUVELLE.value: "bg-primary",
    Statut.EN_COURS.value: "bg-warning text-dark",
    Statut.RESOLUE.value: "bg-success",
    Statut.RETIREE.value: "bg-secondary",
}
COULEURS_PRIORITE = {
    Priorite.BASSE.value: "info",
    Priorite.MOYENNE.value: "warning",
    Priorite.HAUTE.value: "danger",
}


class Categorie(models.Model):
    nom = models.CharField("nom", max_length=100, unique=True)
    description = models.TextField("description", blank=True)
    slug = models.SlugField("slug", max_length=120, unique=True, blank=True, editable=False)
    actif = models.BooleanField("active", default=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nom) or "categorie"
            slug, n = base, 2
            while Categorie.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class SignalementQuerySet(models.QuerySet):
    def par_priorite(self):
        """Haute d'abord, puis moyenne, puis basse ; à égalité, les plus anciennes d'abord."""
        ordre = Case(
            When(priorite=Priorite.HAUTE, then=Value(0)),
            When(priorite=Priorite.MOYENNE, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
        return self.annotate(ordre_priorite=ordre).order_by("ordre_priorite", "cree_le")


class Signalement(models.Model):
    titre = models.CharField("titre", max_length=200)
    description = models.TextField("description")
    lieu = models.CharField("lieu", max_length=150)
    priorite = models.CharField(
        "priorité", max_length=10, choices=Priorite.choices, default=Priorite.MOYENNE
    )
    statut = models.CharField(
        "statut", max_length=10, choices=Statut.choices, default=Statut.NOUVELLE
    )
    categorie = models.ForeignKey(
        Categorie,
        verbose_name="catégorie",
        on_delete=models.PROTECT,
        related_name="signalements",
    )
    demandeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="demandeur",
        on_delete=models.CASCADE,
        related_name="signalements_demandes",
    )
    gestionnaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="gestionnaire",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="signalements_pris_en_charge",
    )
    commentaire_resolution = models.TextField("commentaire de résolution", blank=True)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    maj_le = models.DateTimeField("mis à jour le", auto_now=True)

    objects = SignalementQuerySet.as_manager()

    class Meta:
        ordering = ["-cree_le"]
        verbose_name = "signalement"
        verbose_name_plural = "signalements"

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse("signalement_detail", kwargs={"pk": self.pk})

    # --- Propriétés d'état -------------------------------------------------
    @property
    def peut_etre_retire(self):
        return self.statut == Statut.NOUVELLE

    @property
    def peut_etre_pris_en_charge(self):
        return self.statut == Statut.NOUVELLE

    @property
    def peut_etre_resolu(self):
        return self.statut == Statut.EN_COURS

    @property
    def badge_statut(self):
        return BADGES_STATUT.get(self.statut, "bg-secondary")

    @property
    def couleur_priorite(self):
        return COULEURS_PRIORITE.get(self.priorite, "secondary")

    # --- Validation --------------------------------------------------------
    def clean(self):
        super().clean()
        if self.statut == Statut.RESOLUE and not (self.commentaire_resolution or "").strip():
            raise ValidationError(
                {"commentaire_resolution": "Un commentaire de résolution est obligatoire."}
            )

    # --- Transition explicite ---------------------------------------------
    def changer_statut(self, nouveau, user, commentaire=""):
        """Seul point d'entrée pour modifier le statut. Lève ValidationError si invalide.

        nouvelle -> en_cours : gestionnaire (devient le gestionnaire assigné)
        en_cours -> resolue  : gestionnaire, commentaire obligatoire
        nouvelle -> retiree  : demandeur uniquement
        Toute autre transition est interdite. Chaque transition écrit un HistoriqueStatut.
        """
        commentaire = (commentaire or "").strip()
        ancien = self.statut

        if nouveau not in Statut.values:
            raise ValidationError(f"Statut inconnu : « {nouveau} ».")
        if nouveau not in TRANSITIONS_AUTORISEES[ancien]:
            raise ValidationError(
                f"Transition interdite : « {Statut(ancien).label} » → « {Statut(nouveau).label} »."
            )

        if nouveau == Statut.EN_COURS:
            if not est_gestionnaire(user):
                raise ValidationError("Seul un gestionnaire peut prendre en charge une demande.")
        elif nouveau == Statut.RESOLUE:
            if not est_gestionnaire(user):
                raise ValidationError("Seul un gestionnaire peut résoudre une demande.")
            if not commentaire:
                raise ValidationError("Un commentaire de résolution est obligatoire.")
        elif nouveau == Statut.RETIREE:
            if user is None or user.pk is None or user.pk != self.demandeur_id:
                raise ValidationError("Seul le demandeur peut retirer sa propre demande.")

        with transaction.atomic():
            self.statut = nouveau
            if nouveau == Statut.EN_COURS:
                self.gestionnaire = user
            elif nouveau == Statut.RESOLUE:
                self.commentaire_resolution = commentaire
            self.save()
            HistoriqueStatut.objects.create(
                signalement=self,
                ancien_statut=ancien,
                nouveau_statut=nouveau,
                par=user,
                commentaire=commentaire,
            )


class HistoriqueStatut(models.Model):
    signalement = models.ForeignKey(
        Signalement,
        verbose_name="signalement",
        on_delete=models.CASCADE,
        related_name="historiques",
    )
    ancien_statut = models.CharField("ancien statut", max_length=10, choices=Statut.choices)
    nouveau_statut = models.CharField("nouveau statut", max_length=10, choices=Statut.choices)
    par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="par",
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    commentaire = models.TextField("commentaire", blank=True)
    date = models.DateTimeField("date", auto_now_add=True)

    class Meta:
        ordering = ["date", "id"]
        verbose_name = "historique de statut"
        verbose_name_plural = "historiques de statut"

    def __str__(self):
        return f"{self.signalement_id} : {self.ancien_statut} → {self.nouveau_statut}"
