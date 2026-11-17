# Cafeteria Gourmet Delivery

Projeto do PIT II (Sistemas de Informação - Cruzeiro do Sul Virtual). É a implementação do sistema que eu planejei no PIT I, a partir do backlog de 15 user stories.

Basicamente é um site de pedidos pra uma cafeteria com delivery. O cliente monta o pedido e paga, o atendente vai acompanhando os pedidos num painel e o admin cuida do cardápio, dos usuários e dos relatórios.

Feito em Python com Flask (MVC), SQLAlchemy e SQLite rodando local (no servidor dá pra usar MySQL). O front é HTML, CSS e JS puro.

## Pastas

- `models/` - as tabelas (usuário, produto, pedido...)
- `controllers/` - as rotas, separadas por parte do sistema (vitrine, carrinho, pedidos, conta, painel do atendente e admin)
- `views/` - os templates HTML
- `services/` - cálculo do frete e o pagamento simulado
- `static/` - css, js e imagens
- `database/schema_mysql.sql` - script do banco
- `seed.py` - cria os dados de teste

## Rodando

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

(no linux/mac é `source venv/bin/activate`)

Depois é só abrir http://127.0.0.1:5000

Usuários que o seed cria:

- admin: admin@cafeteria.com / admin123
- atendente: atendente@cafeteria.com / atend123
- cliente: cliente@teste.com / cliente123

## Pagamento

Não tenho conta de lojista, então o pagamento é simulado. Pra testar:

- cartão `4111 1111 1111 1111` passa (qualquer nome, validade futura tipo 12/30, CVV 123)
- cartão `4000 0000 0000 0002` é recusado
- no Pix aparece o código copia e cola e o botão "Já paguei" faz o papel do banco confirmando

## Entrega

A taxa sai pela faixa do CEP, só atende Curitiba e região metropolitana. Fora disso o site avisa que não entrega. O endereço é preenchido pelo ViaCEP.

## Subindo no PythonAnywhere

Usei o plano gratuito.

1. Num console Bash, clonar o projeto (ou subir o zip) e rodar `pip install --user -r requirements.txt` e `python seed.py`
2. Na aba Web criar um app com Manual configuration, Python 3
3. No arquivo WSGI colocar:
   ```python
   import sys
   sys.path.insert(0, "/home/SEU_USUARIO/cafeteria")
   from app import app as application
   ```
4. Em Static files mapear `/static/` pra `/home/SEU_USUARIO/cafeteria/static`
5. Dar reload

Se quiser MySQL é só criar o banco na aba Databases e configurar a variável `DATABASE_URL`.

## O que ficou pronto do backlog

Fiz quase tudo, de US01 até US15. O que ficou faltando ou ficou diferente do planejado:

- US05: o pagamento funciona, mas com o gateway simulado
- US06: a tela do pedido atualiza sozinha, mas é polling de 10 em 10 segundos e não websocket
- US07: cadastro e login funcionam, só não fiz o login com Google
- US10 (push de promoções) não fiz
- US14: o relatório exporta CSV, o PDF é pela impressão do navegador

Também não coloquei token CSRF nos formulários, fica pra uma próxima (provavelmente com Flask-WTF).
