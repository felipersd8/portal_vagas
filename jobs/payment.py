import mercadopago
from django.conf import settings
from django.urls import reverse
from decimal import Decimal

class MercadoPagoService:
    def __init__(self):
        self.mp = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    def criar_preferencia(self, plano, request):
        preference_data = {
            "items": [
                {
                    "title": f"Plano {plano.nome} - Portal de Vagas",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": float(plano.preco)
                }
            ],
            "back_urls": {
                "success": request.build_absolute_uri(reverse('payment_success')),
                "failure": request.build_absolute_uri(reverse('payment_failure')),
                "pending": request.build_absolute_uri(reverse('payment_pending'))
            },
            "auto_return": "approved",
            "external_reference": str(plano.id),
        }

        preference_response = self.mp.preference().create(preference_data)
        return preference_response["response"] 