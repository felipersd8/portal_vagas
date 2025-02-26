from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Job(models.Model):
    TIPO_CONTRATO = (
        ('CLT', 'CLT'),
        ('PJ', 'Pessoa Jurídica'),
        ('Temporário', 'Temporário'),
        ('Estágio', 'Estágio'),
    )

    MODALIDADE_TRABALHO = (
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
    )

    titulo = models.CharField(max_length=200)
    empresa = models.CharField(max_length=100)
    descricao = models.TextField()
    requisitos = models.TextField(blank=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO, blank=True)
    modalidade = models.CharField(
        max_length=20, 
        choices=MODALIDADE_TRABALHO, 
        default='presencial'
    )
    local = models.CharField(max_length=100, blank=True)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-data_publicacao']

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"

class Plano(models.Model):
    NIVEL_CHOICES = (
        ('free', 'Gratuito'),
        ('basic', 'Básico'),
        ('premium', 'Premium'),
        ('enterprise', 'Empresarial'),
    )

    nome = models.CharField(max_length=100)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    
    # Benefícios do plano
    vagas_por_dia = models.IntegerField(default=3)  # Número de vagas que pode se candidatar por dia
    destaque_cv = models.BooleanField(default=False)  # CV aparece primeiro para as empresas
    acesso_antecipado = models.BooleanField(default=False)  # Acesso a vagas antes dos outros
    contato_direto = models.BooleanField(default=False)  # Contato direto com recrutadores
    notificacoes = models.BooleanField(default=False)  # Notificações de novas vagas
    mentoria = models.BooleanField(default=False)  # Acesso a mentoria de carreira

    def __str__(self):
        return f"{self.nome} ({self.get_nivel_display()})"

class Assinatura(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plano = models.ForeignKey('Plano', on_delete=models.CASCADE)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField()
    ativa = models.BooleanField(default=True)
    renovacao_automatica = models.BooleanField(default=True)
    ultima_renovacao = models.DateTimeField(null=True, blank=True)
    proxima_cobranca = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plano.nome}"

    def dias_restantes(self):
        delta = self.data_fim - timezone.now()
        return max(0, delta.days)

    def esta_proxima_do_vencimento(self):
        delta = self.data_fim - timezone.now()
        return delta.days <= 5

class Profile(models.Model):
    NIVEL_EXPERIENCIA = (
        ('estagiario', 'Estagiário'),
        ('junior', 'Júnior'),
        ('pleno', 'Pleno'),
        ('senior', 'Sênior'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='profile_pics', blank=True)
    telefone = models.CharField(max_length=15, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    nivel_experiencia = models.CharField(
        max_length=20,
        choices=NIVEL_EXPERIENCIA,
        blank=True
    )
    resumo = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    curriculo = models.FileField(upload_to='curriculos', blank=True)
    disponivel_mudanca = models.BooleanField(default=False)
    aceita_remoto = models.BooleanField(default=True)
    candidaturas_hoje = models.IntegerField(default=0)
    ultima_candidatura = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def pode_se_candidatar(self):
        plano = self.user.assinatura.plano if hasattr(self.user, 'assinatura') else None
        if not plano:
            return False
            
        # Reseta o contador diário
        hoje = timezone.now().date()
        if self.ultima_candidatura != hoje:
            self.candidaturas_hoje = 0
            self.ultima_candidatura = hoje
            self.save()
            
        return self.candidaturas_hoje < plano.vagas_por_dia

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Pagamento(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('refunded', 'Reembolsado'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plano = models.ForeignKey(Plano, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_id = models.CharField(max_length=100, blank=True)
    data_pagamento = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_pagamento']

    def __str__(self):
        return f"{self.user.username} - {self.plano.nome} - {self.get_status_display()}"
