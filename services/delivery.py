# Calculo de taxa e prazo de entrega.
# Nao tem integracao com API de frete, a regra e pela faixa do CEP mesmo.
# Curitiba = 80000-000 ate 82999-999, regiao metropolitana comeca com 83

from utils import only_digits


def calc_delivery(cep):
    """
    Returns (fee, minutes) or None if we don't deliver there.
    """
    cep = only_digits(cep)
    if len(cep) != 8:
        return None

    prefix = int(cep[:2])
    prefix3 = int(cep[:3])

    if prefix in (80, 81, 82):
        # centro e bairros mais perto
        if prefix == 80:
            return 6.90, 35
        return 8.90, 45

    if prefix == 83:
        # RMC - SJP, Pinhais, Colombo... 830 e 831 sao os mais proximos
        if prefix3 in (830, 831, 832):
            return 11.90, 55
        return 15.90, 70

    # fora da area
    return None
