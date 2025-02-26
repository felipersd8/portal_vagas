from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from jobs.models import Assinatura
from datetime import timedelta

class Command(BaseCommand):
    help = 'Verifica e processa renovações automáticas de assinaturas'

    def handle(self, *args, **options):
        hoje = timezone.now()
        
        # Assinaturas que vencem em 5 dias
        assinaturas_proximas = Assinatura.objects.filter(
            ativa=True,
            renovacao_automatica=True,
            data_fim__lte=hoje + timedelta(days=5),
            data_fim__gt=hoje
        )

        # Enviar emails de aviso
        for assinatura in assinaturas_proximas:
            if not assinatura.notificacao_enviada:
                self.enviar_email_aviso(assinatura)
                assinatura.notificacao_enviada = True
                assinatura.save()

        # Assinaturas vencidas que precisam ser renovadas
        assinaturas_vencidas = Assinatura.objects.filter(
            ativa=True,
            renovacao_automatica=True,
            data_fim__lte=hoje
        )

        for assinatura in assinaturas_vencidas:
            self.processar_renovacao(assinatura)

    def enviar_email_aviso(self, assinatura):
        context = {
            'user': assinatura.user,
            'assinatura': assinatura,
            'data_renovacao': assinatura.data_fim.strftime('%d/%m/%Y')
        }

        html_message = render_to_string('jobs/emails/aviso_renovacao.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Sua assinatura será renovada em breve',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assinatura.user.email],
            html_message=html_message
        )

    def processar_renovacao(self, assinatura):
        try:
            # Aqui você implementaria a lógica de cobrança com o Mercado Pago
            # Por enquanto, vamos apenas simular a renovação
            
            assinatura.data_fim = assinatura.data_fim + timedelta(days=30)
            assinatura.ultima_renovacao = timezone.now()
            assinatura.proxima_cobranca = assinatura.data_fim
            assinatura.save()

            self.enviar_email_confirmacao(assinatura)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao renovar assinatura {assinatura.id}: {str(e)}')) 