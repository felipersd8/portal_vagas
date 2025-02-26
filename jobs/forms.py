from django import forms
from .models import Job, User, Profile

class JobSearchForm(forms.Form):
    ORDEM_CHOICES = (
        ('recentes', 'Mais Recentes'),
        ('antigos', 'Mais Antigos'),
        ('salario_alto', 'Maior Salário'),
        ('salario_baixo', 'Menor Salário'),
    )

    busca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar vagas...'
        })
    )

    modalidade = forms.MultipleChoiceField(
        required=False,
        choices=Job.MODALIDADE_TRABALHO,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    tipo_contrato = forms.MultipleChoiceField(
        required=False,
        choices=Job.TIPO_CONTRATO,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    faixa_salarial = forms.ChoiceField(
        required=False,
        choices=(
            ('', 'Qualquer'),
            ('0_3000', 'Até R$ 3.000'),
            ('3000_6000', 'R$ 3.000 a R$ 6.000'),
            ('6000_9000', 'R$ 6.000 a R$ 9.000'),
            ('9000_', 'Acima de R$ 9.000')
        ),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    ordenacao = forms.ChoiceField(
        required=False,
        choices=ORDEM_CHOICES,
        initial='recentes',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('foto', 'telefone', 'cidade', 'estado', 'nivel_experiencia',
                 'resumo', 'linkedin', 'github', 'portfolio', 'curriculo',
                 'disponivel_mudanca', 'aceita_remoto')
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel_experiencia': forms.Select(attrs={'class': 'form-select'}),
            'resumo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio': forms.URLInput(attrs={'class': 'form-control'}),
        } 