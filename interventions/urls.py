from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import ConnexionForm

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("annonces/", views.annonces, name="annonces"),
    path("annonces/nouveau/", views.annonce_create, name="annonce_create"),
    path("signalements/nouveau/", views.signalement_create, name="signalement_create"),
    path("signalements/<int:pk>/", views.signalement_detail, name="signalement_detail"),
    path("signalements/<int:pk>/retirer/", views.signalement_retirer, name="signalement_retirer"),
    path("signalements/<int:pk>/prendre-en-charge/", views.signalement_prendre_en_charge,
         name="signalement_prendre_en_charge"),
    path("signalements/<int:pk>/resoudre/", views.signalement_resoudre, name="signalement_resoudre"),
    path("signalements/<int:pk>/valider-fermeture/", views.signalement_valider_fermeture,
         name="signalement_valider_fermeture"),
    path("signalements/<int:pk>/refuser-fermeture/", views.signalement_refuser_fermeture,
         name="signalement_refuser_fermeture"),
    path("mes-signalements/", views.mes_signalements, name="mes_signalements"),
    path("gestion/", views.gestionnaire_dashboard, name="gestionnaire_dashboard"),
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", auth_views.LoginView.as_view(authentication_form=ConnexionForm,
                                                    redirect_authenticated_user=True),
         name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
]
