"""Rôles : un gestionnaire = membre du groupe « Gestionnaires » (ou superuser)."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

GROUPE_GESTIONNAIRES = "Gestionnaires"


def est_gestionnaire(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUPE_GESTIONNAIRES).exists()


def gestionnaire_required(view):
    """Visiteur -> redirection login ; connecté non gestionnaire -> 403."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not est_gestionnaire(request.user):
            raise PermissionDenied("Action réservée aux gestionnaires.")
        return view(request, *args, **kwargs)

    return wrapper
