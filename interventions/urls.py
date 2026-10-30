from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import ConnexionForm

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("categories/", views.categorie_list, name="categorie_list"),
    path("signalements/", views.signalement_list, name="signalement_list"),
    path("signalements/nouveau/", views.signalement_create, name="signalement_create"),
    path("signalements/<int:pk>/", views.signalement_detail, name="signalement_detail"),
    path("signalements/<int:pk>/retirer/", views.signalement_retirer, name="signalement_retirer"),
    path("signalements/<int:pk>/prendre-en-charge/", views.signalement_prendre_en_charge,
         name="signalement_prendre_en_charge"),
    path("signalements/<int:pk>/resoudre/", views.signalement_resoudre, name="signalement_resoudre"),
    path("mes-signalements/", views.mes_signalements, name="mes_signalements"),
    path("gestion/", views.gestionnaire_dashboard, name="gestionnaire_dashboard"),
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", auth_views.LoginView.as_view(authentication_form=ConnexionForm,
                                                    redirect_authenticated_user=True),
         name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
]
