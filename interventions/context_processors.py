from .roles import est_gestionnaire


def roles(request):
    return {"est_gestionnaire": est_gestionnaire(request.user)}
