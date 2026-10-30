from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Annonce, Categorie, MessageSignalement, Signalement


class BootstrapMixin:
    """Ajoute les classes de widgets attendues par static/css/app.css."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + " " + css).strip()


class SignalementForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Signalement
        fields = ["titre", "description", "lieu", "priorite", "categorie"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].queryset = Categorie.objects.filter(actif=True)
        self.fields["categorie"].empty_label = "— Choisir une catégorie —"

    def clean_titre(self):
        titre = self.cleaned_data["titre"].strip()
        if len(titre) < 3:
            raise forms.ValidationError("Le titre doit contenir au moins 3 caractères.")
        return titre


class ResolutionForm(BootstrapMixin, forms.Form):
    commentaire = forms.CharField(
        label="Commentaire de résolution",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4}),
        error_messages={"required": "Le commentaire de résolution est obligatoire."},
    )


class MessageSignalementForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = MessageSignalement
        fields = ["contenu"]
        widgets = {"contenu": forms.Textarea(attrs={"rows": 3})}

    def clean_contenu(self):
        contenu = self.cleaned_data["contenu"].strip()
        if not contenu:
            raise forms.ValidationError("Le message ne peut pas être vide.")
        return contenu


class AnnonceForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Annonce
        fields = ["titre", "contenu"]
        widgets = {"contenu": forms.Textarea(attrs={"rows": 6})}

    def clean_titre(self):
        titre = self.cleaned_data["titre"].strip()
        if len(titre) < 3:
            raise forms.ValidationError("Le titre doit contenir au moins 3 caractères.")
        return titre

    def clean_contenu(self):
        contenu = self.cleaned_data["contenu"].strip()
        if not contenu:
            raise forms.ValidationError("Le contenu de l'annonce est obligatoire.")
        return contenu


class InscriptionForm(BootstrapMixin, UserCreationForm):
    pass


class ConnexionForm(BootstrapMixin, AuthenticationForm):
    pass
