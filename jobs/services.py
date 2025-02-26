import mercadopago
from django.conf import settings

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
                "success": request.build_absolute_uri('/pagamento/sucesso/'),
                "failure": request.build_absolute_uri('/pagamento/falha/'),
                "pending": request.build_absolute_uri('/pagamento/pendente/')
            },
            "auto_return": "approved",
            "external_reference": str(plano.id),
            "payment_methods": {
                "excluded_payment_methods": [{"id": "amex"}],
                "installments": 1
            }
        }

        preference_response = self.mp.preference().create(preference_data)
        return preference_response["response"] 