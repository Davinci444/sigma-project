"""Forms used in the core application."""

from django import forms


class FileUploadForm(forms.Form):
    """Form for uploading the fuel consumption Excel file."""

    file = forms.FileField(
        label="Selecciona el archivo GESTION DE COMBUSTIBLE.XLSX"
    )

