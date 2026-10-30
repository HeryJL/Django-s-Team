from django.contrib import admin

from .models import Categorie, HistoriqueStatut, Signalement

admin.site.site_header = "Suivi des interventions — administration"
admin.site.site_title = "Interventions"


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "actif")
    list_filter = ("actif",)
    search_fields = ("nom", "description")


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
