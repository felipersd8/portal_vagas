from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from .models import Job, Profile, Plano, Assinatura, Pagamento
from .forms import JobSearchForm, UserForm, ProfileForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .payment import MercadoPagoService
from django.conf import settings
import logging
from .services import MercadoPagoService
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Create your views here.

def job_list(request):
    form = JobSearchForm(request.GET)
    jobs = Job.objects.filter(ativo=True)

    if form.is_valid():
        # Busca por palavra-chave
        if busca := form.cleaned_data.get('busca'):
            jobs = jobs.filter(
                Q(titulo__icontains=busca) |
                Q(descricao__icontains=busca) |
                Q(empresa__icontains=busca) |
                Q(requisitos__icontains=busca)
            )

        # Filtro por modalidade
        if modalidades := form.cleaned_data.get('modalidade'):
            jobs = jobs.filter(modalidade__in=modalidades)

        # Filtro por tipo de contrato
        if tipos := form.cleaned_data.get('tipo_contrato'):
            jobs = jobs.filter(tipo_contrato__in=tipos)

        # Filtro por faixa salarial
        if faixa := form.cleaned_data.get('faixa_salarial'):
            if faixa == '0_3000':
                jobs = jobs.filter(salario__lte=3000)
            elif faixa == '3000_6000':
                jobs = jobs.filter(salario__gt=3000, salario__lte=6000)
            elif faixa == '6000_9000':
                jobs = jobs.filter(salario__gt=6000, salario__lte=9000)
            elif faixa == '9000_':
                jobs = jobs.filter(salario__gt=9000)

        # Ordenação
        if ordenacao := form.cleaned_data.get('ordenacao'):
            if ordenacao == 'recentes':
                jobs = jobs.order_by('-data_publicacao')
            elif ordenacao == 'antigos':
                jobs = jobs.order_by('data_publicacao')
            elif ordenacao == 'salario_alto':
                jobs = jobs.order_by('-salario')
            elif ordenacao == 'salario_baixo':
                jobs = jobs.order_by('salario')

    context = {
        'form': form,
        'jobs': jobs,
        'total_vagas': jobs.count(),
        'modalidades_count': {
            'remoto': jobs.filter(modalidade='remoto').count(),
            'presencial': jobs.filter(modalidade='presencial').count(),
            'hibrido': jobs.filter(modalidade='hibrido').count(),
        }
    }
    
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, ativo=True)
    return render(request, 'jobs/job_detail.html', {'job': job})

@login_required
def profile_edit(request):
    # Tenta obter o perfil ou cria um novo se não existir
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
    
    return render(request, 'jobs/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def profile_view(request):
    # Tenta obter o perfil ou cria um novo se não existir
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'jobs/profile_view.html', {'profile': profile})

def home(request):
    context = {
        'total_vagas': Job.objects.filter(ativo=True).count(),
        'vagas_remotas': Job.objects.filter(ativo=True, modalidade='remoto').count(),
        'total_empresas': Job.objects.filter(ativo=True).values('empresa').distinct().count(),
        'latest_jobs': Job.objects.filter(ativo=True).order_by('-data_publicacao')[:6],
        'tipos_contrato': [
            {
                'tipo': tipo[0],
                'nome': tipo[1],
                'count': Job.objects.filter(ativo=True, tipo_contrato=tipo[0]).count()
            }
            for tipo in Job.TIPO_CONTRATO
        ]
    }
    return render(request, 'jobs/home.html', context)

def planos(request):
    planos = Plano.objects.all().order_by('preco')
    
    context = {
        'planos': planos,
        'plano_gratuito': planos.filter(preco=0).first(),
        'plano_basico': planos.filter(nome='Básico').first(),
        'plano_premium': planos.filter(nome='Premium').first(),
        'plano_empresarial': planos.filter(nome='Empresarial').first(),
    }
    
    return render(request, 'jobs/planos.html', context)

@login_required
def assinar_plano(request, plano_id):
    plano = get_object_or_404(Plano, id=plano_id)
    
    # Aqui você implementaria a lógica de pagamento
    # Por enquanto, vamos apenas criar a assinatura
    
    Assinatura.objects.create(
        user=request.user,
        plano=plano,
        data_fim=timezone.now() + timedelta(days=30)
    )
    
    messages.success(request, f'Parabéns! Você assinou o plano {plano.nome}!')
    return redirect('profile')

@login_required
def checkout(request, plano_id):
    try:
        plano = get_object_or_404(Plano, id=plano_id)
        assinatura_existente = Assinatura.objects.filter(
            user=request.user, 
            ativa=True
        ).first()

        if plano.preco == 0:
            if request.method == 'POST':
                # Lógica do plano gratuito...
                pass
            return render(request, 'jobs/checkout.html', {
                'plano': plano,
                'assinatura_existente': assinatura_existente
            })
        else:
            # Para planos pagos
            mp_service = MercadoPagoService()
            preference = mp_service.criar_preferencia(plano, request)
            
            return render(request, 'jobs/checkout.html', {
                'plano': plano,
                'assinatura_existente': assinatura_existente,
                'public_key': settings.MERCADO_PAGO_PUBLIC_KEY,
                'preference_id': preference['id']
            })

    except Exception as e:
        messages.error(request, 'Ocorreu um erro ao processar o checkout. Tente novamente.')
        return redirect('planos')

@login_required
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    status = request.GET.get('status')
    external_reference = request.GET.get('external_reference')
    
    if status == 'approved':
        plano = get_object_or_404(Plano, id=external_reference)
        
        # Registra o pagamento
        Pagamento.objects.create(
            user=request.user,
            plano=plano,
            valor=plano.preco,
            status='approved',
            payment_id=payment_id
        )
        
        # Atualiza ou cria assinatura
        assinatura, created = Assinatura.objects.update_or_create(
            user=request.user,
            defaults={
                'plano': plano,
                'data_fim': timezone.now() + timedelta(days=30),
                'ativa': True,
                'data_inicio': timezone.now()
            }
        )
        
        # Prepara e envia o email
        context = {
            'user': request.user,
            'plano': plano,
            'assinatura': assinatura,
            'site_url': f"{request.scheme}://{request.get_host()}"
        }
        
        html_message = render_to_string('jobs/emails/confirmacao_pagamento.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Confirmação de Pagamento - Portal de Vagas',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            html_message=html_message
        )
        
        return render(request, 'jobs/payment_success.html', {
            'plano': plano,
            'assinatura': assinatura
        })
    
    return redirect('planos')

@login_required
def payment_pending(request):
    messages.warning(request, 'Seu pagamento está pendente de aprovação.')
    return redirect('profile')

@login_required
def payment_failure(request):
    messages.error(request, 'Houve um problema com o pagamento. Por favor, tente novamente.')
    return redirect('planos')

@login_required
def payment_history(request):
    pagamentos = Pagamento.objects.filter(user=request.user)
    return render(request, 'jobs/payment_history.html', {'pagamentos': pagamentos})

@login_required
def subscription_settings(request):
    assinatura = Assinatura.objects.filter(user=request.user, ativa=True).first()
    renovacoes = Pagamento.objects.filter(user=request.user).order_by('-data_pagamento')
    
    return render(request, 'jobs/subscription_settings.html', {
        'assinatura': assinatura,
        'renovacoes': renovacoes
    })

@login_required
def toggle_auto_renewal(request):
    if request.method == 'POST':
        assinatura = get_object_or_404(Assinatura, user=request.user, ativa=True)
        assinatura.renovacao_automatica = request.POST.get('auto_renewal') == 'on'
        assinatura.save()
        
        messages.success(request, 
            'Renovação automática ativada.' if assinatura.renovacao_automatica 
            else 'Renovação automática desativada.'
        )
    
    return redirect('subscription_settings')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada com sucesso! Agora você pode fazer login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'jobs/register.html', {'form': form})
