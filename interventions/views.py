from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import InscriptionForm, ResolutionForm, SignalementForm
from .models import Categorie, Signalement, Statut
from .roles import est_gestionnaire, gestionnaire_required

PAR_PAGE = 10


# --- Helpers ---------------------------------------------------------------
def _contexte_liste(request, queryset, statuts=Statut.choices):
    """Recherche par titre + filtre par état + pagination (10 par page)."""
    q = request.GET.get("q", "").strip()
    statut = request.GET.get("statut", "").strip()
    if statut not in [valeur for valeur, _ in statuts]:
        statut = ""
    if q:
        queryset = queryset.filter(titre__icontains=q)
    if statut:
        queryset = queryset.filter(statut=statut)
    page_obj = Paginator(queryset, PAR_PAGE).get_page(request.GET.get("page"))
    params = {cle: val for cle, val in (("q", q), ("statut", statut)) if val}
    return {
        "page_obj": page_obj,
        "q": q,
        "statut": statut,
        "statuts": statuts,
        "querystring": urlencode(params),
    }


def _changer_statut(request, signalement, nouveau, commentaire, message_ok):
    try:
        signalement.changer_statut(nouveau, request.user, commentaire)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return False
    messages.success(request, message_ok)
    return True


# --- Pages publiques -------------------------------------------------------
def accueil(request):
    categories = Categorie.objects.filter(actif=True)
    return render(request, "interventions/accueil.html", {"categories": categories})


def categorie_list(request):
    categories = Categorie.objects.filter(actif=True).annotate(
        nb_signalements=Count("signalements", filter=~Q(signalements__statut=Statut.RETIREE))
    )
    return render(request, "interventions/categorie_list.html", {"categories": categories})


def signalement_list(request):
    """Liste publique (sans description ni demandeur). Les retirées ne sont visibles
    que des gestionnaires. Le détail reste réservé à l'auteur et aux gestionnaires."""
    gestionnaire = est_gestionnaire(request.user)
    queryset = Signalement.objects.select_related("categorie")
    statuts = Statut.choices
    if not gestionnaire:
        queryset = queryset.exclude(statut=Statut.RETIREE)
        statuts = [c for c in Statut.choices if c[0] != Statut.RETIREE]
    contexte = _contexte_liste(request, queryset, statuts)
    contexte["titre_page"] = "Toutes les demandes"
    return render(request, "interventions/signalement_list.html", contexte)


def inscription(request):
    if request.user.is_authenticated:
        return redirect("accueil")
    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé. Bienvenue !")
            return redirect("accueil")
        messages.error(request, "Le formulaire contient des erreurs.")
    else:
        form = InscriptionForm()
    return render(request, "registration/inscription.html", {"form": form})


# --- Espace utilisateur ----------------------------------------------------
@login_required
def mes_signalements(request):
    queryset = Signalement.objects.filter(demandeur=request.user).select_related("categorie")
    return render(request, "interventions/mes_signalements.html", _contexte_liste(request, queryset))


@login_required
def signalement_create(request):
    if request.method == "POST":
        form = SignalementForm(request.POST)
        if form.is_valid():
            signalement = form.save(commit=False)
            signalement.demandeur = request.user
            signalement.save()
            messages.success(request, "Votre signalement a été enregistré.")
            return redirect("signalement_detail", pk=signalement.pk)
        messages.error(request, "Le formulaire contient des erreurs.")
    else:
        form = SignalementForm()
    return render(request, "interventions/signalement_form.html", {"form": form})


@login_required
def signalement_detail(request, pk):
    signalement = get_object_or_404(
        Signalement.objects.select_related("categorie", "demandeur", "gestionnaire"), pk=pk
    )
    est_auteur = signalement.demandeur_id == request.user.id
    if not est_auteur and not est_gestionnaire(request.user):
        raise PermissionDenied("Ce signalement ne vous appartient pas.")
    return render(
        request,
        "interventions/signalement_detail.html",
        {
            "signalement": signalement,
            "historique": signalement.historiques.select_related("par"),
            "est_auteur": est_auteur,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def signalement_retirer(request, pk):
    """GET = page de confirmation (aucune modification) ; POST = retrait effectif."""
    signalement = get_object_or_404(Signalement, pk=pk)
    if signalement.demandeur_id != request.user.id:
        raise PermissionDenied("Vous ne pouvez retirer que vos propres demandes.")
    if not signalement.peut_etre_retire:
        messages.error(request, "Seule une demande « nouvelle » peut être retirée.")
        return redirect("signalement_detail", pk=signalement.pk)
    if request.method == "POST":
        if _changer_statut(request, signalement, Statut.RETIREE, "Retirée par le demandeur.",
                           "La demande a été retirée."):
            return redirect("mes_signalements")
        return redirect("signalement_detail", pk=signalement.pk)
    return render(request, "interventions/signalement_confirmer_retrait.html",
                  {"signalement": signalement})


# --- Espace gestionnaire ---------------------------------------------------
@require_POST
@gestionnaire_required
def signalement_prendre_en_charge(request, pk):
    signalement = get_object_or_404(Signalement, pk=pk)
    _changer_statut(request, signalement, Statut.EN_COURS, "",
                    "Demande prise en charge : elle est maintenant « en cours ».")
    return redirect("signalement_detail", pk=signalement.pk)


@gestionnaire_required
@require_http_methods(["GET", "POST"])
def signalement_resoudre(request, pk):
    """GET = formulaire de résolution (confirmation) ; POST = résolution effective."""
    signalement = get_object_or_404(Signalement, pk=pk)
    if not signalement.peut_etre_resolu:
        messages.error(request, "Seule une demande « en cours » peut être résolue.")
        return redirect("signalement_detail", pk=signalement.pk)
    if request.method == "POST":
        form = ResolutionForm(request.POST)
        if form.is_valid():
            if _changer_statut(request, signalement, Statut.RESOLUE,
                               form.cleaned_data["commentaire"], "La demande a été marquée résolue."):
                return redirect("gestionnaire_dashboard")
            return redirect("signalement_detail", pk=signalement.pk)
        messages.error(request, "Le commentaire de résolution est obligatoire.")
    else:
        form = ResolutionForm()
    return render(request, "interventions/signalement_resoudre.html",
                  {"signalement": signalement, "form": form})


@gestionnaire_required
def gestionnaire_dashboard(request):
    base = Signalement.objects.select_related("categorie", "demandeur", "gestionnaire")
    contexte = {
        "nouvelles": base.filter(statut=Statut.NOUVELLE).par_priorite(),
        "en_cours": base.filter(statut=Statut.EN_COURS).par_priorite(),
        "stats": {
            "total": Signalement.objects.count(),
            "en_attente": Signalement.objects.filter(statut=Statut.NOUVELLE).count(),
            "en_cours": Signalement.objects.filter(statut=Statut.EN_COURS).count(),
            "resolues": Signalement.objects.filter(statut=Statut.RESOLUE).count(),
        },
    }
    return render(request, "interventions/gestionnaire_dashboard.html", contexte)
