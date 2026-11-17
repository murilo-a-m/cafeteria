# pagamento fake, sem conta de lojista nao da pra usar PagSeguro/Stripe de verdade.
# cartao final 0002 sempre recusa
import random
import string
from datetime import date

from utils import only_digits


class PaymentResult:
    def __init__(self, approved, message, last4=None):
        self.approved = approved
        self.message = message
        self.last4 = last4


def luhn_ok(number):
    total = 0
    reverse = number[::-1]
    for i, ch in enumerate(reverse):
        d = int(ch)
        if i % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def charge_card(number, holder, expiry, cvv, amount):
    number = only_digits(number)

    if len(number) < 13 or len(number) > 19:
        return PaymentResult(False, "Número do cartão inválido.")
    if not luhn_ok(number):
        return PaymentResult(False, "Número do cartão inválido.")
    if not holder or len(holder.strip()) < 3:
        return PaymentResult(False, "Informe o nome impresso no cartão.")

    try:
        mm, yy = expiry.split("/")
        mm = int(mm)
        yy = int(yy) + 2000
        if mm < 1 or mm > 12:
            raise ValueError
    except Exception:
        return PaymentResult(False, "Validade inválida, use MM/AA.")

    today = date.today()
    if (yy, mm) < (today.year, today.month):
        return PaymentResult(False, "Cartão vencido.")

    if not cvv or not cvv.isdigit() or len(cvv) not in (3, 4):
        return PaymentResult(False, "CVV inválido.")

    # cartao de teste pra simular recusa
    if number.endswith("0002"):
        return PaymentResult(False, "Pagamento recusado pela operadora. Tente outro cartão.", number[-4:])

    if amount <= 0:
        return PaymentResult(False, "Valor inválido")

    return PaymentResult(True, "Pagamento aprovado!", number[-4:])


def generate_pix_code(order_id, amount):
    # nao e um BR Code de verdade, so parece um rs
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
    return f"00020126CAFEGOURMET{order_id:06d}5204000053039865406{amount:.2f}{rand}6304"
