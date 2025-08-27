    # core/forms.py
from django import forms

class FileUploadForm(forms.Form):
        file = forms.FileField(label="Selecciona el archivo GESTION DE COMBUSTIBLE.XLSX")
    