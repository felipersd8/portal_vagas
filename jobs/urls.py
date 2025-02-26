from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('vagas/', views.job_list, name='job_list'),
    path('vaga/<int:pk>/', views.job_detail, name='job_detail'),
    path('perfil/', views.profile_view, name='profile'),
    path('perfil/editar/', views.profile_edit, name='profile_edit'),
    path('planos/', views.planos, name='planos'),
    path('planos/checkout/<int:plano_id>/', views.checkout, name='checkout'),
    path('pagamento/sucesso/', views.payment_success, name='payment_success'),
    path('pagamento/pendente/', views.payment_pending, name='payment_pending'),
    path('pagamento/falha/', views.payment_failure, name='payment_failure'),
    path('pagamentos/historico/', views.payment_history, name='payment_history'),
    path('assinatura/configuracoes/', views.subscription_settings, name='subscription_settings'),
    path('assinatura/toggle-renovacao/', views.toggle_auto_renewal, name='toggle_auto_renewal'),
] 