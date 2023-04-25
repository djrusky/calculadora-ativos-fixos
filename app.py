import matplotlib.pyplot as plt
from flask import Flask, render_template, request

import lib.FIA as FIA

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("calculator.html")


@app.route("/example")
def example():
    return render_template("example.html")


@app.route("/calculator/fair-price", methods=["POST"])
def fair_price():
    maturidade = float(request.form["maturidade"])
    ytm = float(request.form["ytm"])
    cupom = float(request.form["cupom"])
    valor_face = float(request.form["valor_face"])
    compounding = float(request.form["compounding"])
    print(compounding)

    titulo = FIA.create_coupon_bond(
        maturity=maturidade, face=valor_face, rate=cupom, frequency=1
    )
    preco = titulo.price(ytm, compounding=compounding)

    return render_template("calculator.html", preco=preco)


@app.route("/calculator/ytm", methods=["POST"])
def ytm():
    maturidade = float(request.form["maturidade"])
    preco = float(request.form["preco"])
    cupom = float(request.form["cupom"])
    valor_face = float(request.form["valor_face"])

    titulo = FIA.create_coupon_bond(
        maturity=maturidade, face=valor_face, rate=cupom, frequency=1
    )
    ytm = titulo.YTM(preco)

    return render_template("calculator.html", ytm=ytm)


@app.route("/calculator/graph", methods=["POST"])
def grafico():
    # Dados do título original
    maturidade = float(request.form["maturidade"])
    cupom = float(request.form["cupom"])
    valor_face = float(request.form["valor_face"])
    compounding = float(request.form["compounding"])

    titulo1 = FIA.create_coupon_bond(
        maturity=maturidade, face=valor_face, rate=cupom, frequency=1
    )

    ytm1 = float(request.form["ytm"])
    preco_justo1 = titulo1.price(ytm1, compounding=1)

    # Dados do título com curva de juros ajustada
    ytm2 = float(request.form["ytm2"])
    if int(request.form["periodo"]) == None:
        periodo = 0
    else:
        periodo = int(request.form["periodo"])

    titulo2 = FIA.create_coupon_bond(
        maturity=maturidade - periodo, face=valor_face, rate=cupom, frequency=1
    )
    preco_justo2 = titulo2.price(ytm2, compounding=1)

    # Cria as curvas
    prices = [preco_justo1, preco_justo2]
    yields = [ytm1, ytm2]
    plt.plot(yields, prices)

    # Cria o gráfico
    fig, ax = plt.subplots()
    ax.plot(ytm1, preco_justo1, label="Curva original", color="purple")
    ax.plot(ytm2, preco_justo2, label="Nova curva", color="blue")
    ax.plot(ytm1, preco_justo1, "ro", label="Preço original", color="purple")
    ax.plot(ytm2, preco_justo2, "go", label="Novo preço", color="blue")
    ax.set_xlabel("YTM")
    ax.set_ylabel("Preço")
    ax.legend()

    return render_template("calculator.html")


@app.route("/calculator/price-table", methods=["POST"])
def calcular_tabela():
    maturidade = float(request.form["maturidade"])
    cupom = float(request.form["cupom"])
    valor_face = float(request.form["valor_face"])
    compounding = float(request.form["compounding"])
    taxas = [0.01 * i for i in range(1, 11)]  # taxa de juros de 1% a 10%

    titulo = FIA.create_coupon_bond(
        maturity=maturidade, face=valor_face, rate=cupom, frequency=1
    )
    preco_base = titulo.price(0.0, compounding=compounding)

    precos = []
    variacoes = []
    for taxa in taxas:
        preco = titulo.price(taxa, compounding=compounding)
        variacao = (preco_base - preco) / preco_base * 100
        precos.append(preco)
        variacoes.append(variacao)

    return render_template(
        "calculator.html", taxas=taxas, precos=precos, variacoes=variacoes
    )
