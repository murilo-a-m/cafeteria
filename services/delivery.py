# frete pela faixa do CEP. Curitiba 80-82, RMC 83

from utils import only_digits


def calc_delivery(cep):
    # retorna (taxa, minutos) ou None se nao entrega no CEP
    cep = only_digits(cep)
    if len(cep) != 8:
        return None

    prefix = int(cep[:2])
    prefix3 = int(cep[:3])

    if prefix in (80, 81, 82):
        if prefix == 80:
            return 6.90, 35
        return 8.90, 45

    if prefix == 83:
        # RMC - SJP, Pinhais, Colombo... 830 e 831 sao os mais proximos
        if prefix3 in (830, 831, 832):
            return 11.90, 55
        return 15.90, 70

    return None
