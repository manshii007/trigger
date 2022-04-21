from content.models import Series, Movie
from django import forms


class SeriesForm(forms.Form):
    series = forms.ModelChoiceField(queryset=Series.objects.all())


class MovieForm(forms.Form):
    movie = forms.ModelChoiceField(queryset=Movie.objects.all())