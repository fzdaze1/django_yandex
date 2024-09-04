from django import forms


class PublicKeyForm(forms.Form):
    public_key = forms.URLField(
        label='Публичная ссылка на Яндекс.Диск', required=True)
