from django.contrib import admin

from .models import Annonce, Categorie, HistoriqueStatut, MessageSignalement, Signalement

admin.site.site_header = "Suivi des interventions — administration"
admin.site.site_title = "Interventions"


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "actif")
    list_filter = ("actif",)
    search_fields = ("nom", "description")


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ("titre", "auteur", "publie_le")
    search_fields = ("titre", "contenu", "auteur__username")
    readonly_fields = ("auteur", "publie_le")


class HistoriqueInline(admin.TabularInline):
    model = HistoriqueStatut
    extra = 0
    can_delete = False
    fields = ("date", "ancien_statut", "nouveau_statut", "par", "commentaire")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ("titre", "categorie", "priorite", "statut", "demandeur", "gestionnaire", "cree_le")
    list_filter = ("statut", "priorite", "categorie")
    search_fields = ("titre", "lieu", "demandeur__username")
    # Le statut ne se modifie que par changer_statut() : on le verrouille dans l'admin
    # pour ne jamais contourner l'historique.
    readonly_fields = ("statut", "gestionnaire", "commentaire_resolution", "cree_le", "maj_le")
    inlines = [HistoriqueInline]


@admin.register(HistoriqueStatut)
class HistoriqueStatutAdmin(admin.ModelAdmin):
    list_display = ("signalement", "ancien_statut", "nouveau_statut", "par", "date")
    list_filter = ("nouveau_statut",)
    readonly_fields = ("signalement", "ancien_statut", "nouveau_statut", "par", "commentaire", "date")

    def has_add_permission(self, request):
        return False


@admin.register(MessageSignalement)
class MessageSignalementAdmin(admin.ModelAdmin):
    list_display = ("signalement", "auteur", "date")
    search_fields = ("signalement__titre", "auteur__username", "contenu")
    readonly_fields = ("signalement", "auteur", "contenu", "date")

    def has_add_permission(self, request):
        return False
