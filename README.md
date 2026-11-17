# Cafeteria Gourmet Delivery

Projeto do PIT II de Sistemas de Informação (Cruzeiro do Sul Virtual).
É a implementação do sistema que foi planejado no PIT I (BMC + Product Backlog com 15 user stories).

Aplicação web de pedidos para uma cafeteria gourmet com delivery: cliente monta o pedido e paga,
o atendente acompanha os pedidos num painel e o administrador cuida do cardápio, usuários e relatórios.

**Stack:** Python 3 + Flask (padrão MVC), SQLAlchemy, SQLite (local) ou MySQL (produção), HTML/CSS/JS puro no front.

## Estrutura (MVC)

```
cafeteria/
├── app.py               # cria o app e registra os controllers
├── config.py
├── seed.py              # popula o banco com dados de teste
├── models/              # MODEL  - tabelas (User, Product, Order...)
├── controllers/         # CONTROLLER - rotas/regras de cada modulo
│   ├── shop.py          #   vitrine
│   ├── cart.py          #   carrinho
│   ├── orders.py        #   checkout, pagamento, acompanhamento, avaliacao
│   ├── account.py       #   cadastro, login, minha conta
│   ├── staff.py         #   painel do atendente
│   └── admin.py         #   produtos, usuarios, relatorio
├── views/               # VIEW - templates HTML (Jinja2)
├── services/            # calculo de frete e gateway de pagamento (simulado)
├── static/              # css, js, imagens
└── database/schema_mysql.sql   # projeto fisico do banco
```

## Como rodar local

```bash
python -m venv venv
# windows: venv\Scripts\activate   |  linux/mac: source venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

Abrir http://127.0.0.1:5000

### Usuários de teste

| Perfil    | E-mail                  | Senha      |
|-----------|-------------------------|------------|
| Admin     | admin@cafeteria.com     | admin123   |
| Atendente | atendente@cafeteria.com | atend123   |
| Cliente   | cliente@teste.com       | cliente123 |

### Pagamento (ambiente de teste)

O gateway é simulado (não tem conta de lojista real):

- Cartão aprovado: `4111 1111 1111 1111`, qualquer nome, validade futura (ex: 12/30), CVV 123
- Cartão recusado: `4000 0000 0000 0002`
- Pix: gera o código copia-e-cola e o botão "Já paguei" simula a confirmação do banco

### Entrega

A taxa é calculada pela faixa do CEP (Curitiba e região metropolitana). CEP fora da faixa = "não entregamos".
O endereço é preenchido automaticamente pelo ViaCEP.

## Publicar no PythonAnywhere (grátis)

1. Criar conta em pythonanywhere.com (plano Beginner)
2. Em *Consoles > Bash*: subir o projeto (git clone ou upload do zip) e rodar
   `pip install --user -r requirements.txt` e `python seed.py`
3. Em *Web > Add a new web app > Manual configuration > Python 3.x*
4. No arquivo WSGI deixar:
   ```python
   import sys
   sys.path.insert(0, "/home/SEU_USUARIO/cafeteria")
   from app import app as application
   ```
5. Em *Static files*: URL `/static/` -> `/home/SEU_USUARIO/cafeteria/static`
6. Reload. (Opcional: criar banco MySQL na aba *Databases* e setar `DATABASE_URL`)

## O que foi implementado (backlog do PIT I)

| US | Funcionalidade | Situação |
|----|----------------|----------|
| US01 | Cardápio com fotos e preços | ✅ |
| US02 | Filtro por categoria sem recarregar | ✅ |
| US03 | Carrinho com quantidade e observações | ✅ |
| US04 | Endereço com CEP automático, taxa e prazo, endereços salvos | ✅ |
| US05 | Pagamento cartão / Pix com tratamento de recusa | ✅ (gateway simulado) |
| US06 | Acompanhamento do pedido com atualização automática | ✅ (polling a cada 10s) |
| US07 | Cadastro e login, sessão mantida | ✅ (login Google não feito) |
| US08 | Histórico + pedir novamente | ✅ |
| US09 | Avaliação 1-5 estrelas até 48h depois da entrega | ✅ |
| US10 | Notificação push de promoções | ❌ não implementado |
| US11 | Painel do atendente em tempo real com alerta sonoro | ✅ |
| US12 | Mudar status com um clique | ✅ |
| US13 | CRUD de produtos | ✅ |
| US14 | Relatório por período/produto/categoria, gráfico, exportação | ✅ (CSV + imprimir em PDF) |
| US15 | Perfis, ativar/desativar contas, log de acessos | ✅ |

## Limitações conhecidas

- gateway de pagamento é simulado
- sem login com Google e sem push (US10)
- o "tempo real" é feito com polling, não websocket
- formulários sem token CSRF (melhoria futura com Flask-WTF)
