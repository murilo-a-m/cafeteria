// =========================================================
//  Cafeteria Gourmet - scripts do front
//  (sem framework, so JS puro mesmo)
// =========================================================

function formatBRL(v) {
    return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// esconde os alertas depois de uns segundos
document.querySelectorAll(".alert").forEach(function (el) {
    setTimeout(function () {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 500);
    }, 5000);
});


// ---------------------------------------------------------
// Filtro de categorias do cardapio (US02)
// ---------------------------------------------------------
function initCategoryFilter(initial) {
    const chips = document.querySelectorAll("#filters .chip");
    const cards = document.querySelectorAll("#product-grid .product");
    const noResults = document.getElementById("no-results");

    function applyFilter(cat) {
        let visible = 0;
        cards.forEach(card => {
            if (cat === "todos" || card.dataset.category === cat) {
                card.classList.remove("hidden");
                visible++;
            } else {
                card.classList.add("hidden");
            }
        });
        chips.forEach(c => c.classList.toggle("active", c.dataset.cat === cat));
        noResults.classList.toggle("hidden", visible > 0);

        // atualiza a url sem recarregar, assim se der F5 continua no filtro
        const url = cat === "todos" ? "/" : "/?cat=" + cat;
        history.replaceState(null, "", url);
    }

    chips.forEach(chip => {
        chip.addEventListener("click", () => applyFilter(chip.dataset.cat));
    });

    if (initial && initial !== "todos") applyFilter(initial);
}


// ---------------------------------------------------------
// CEP -> busca endereco no ViaCEP
// ---------------------------------------------------------
function setupCepLookup(onCepFound) {
    document.querySelectorAll(".cep-input").forEach(input => {
        const form = input.closest("form");
        const msg = input.parentElement.querySelector(".cep-msg");

        input.addEventListener("input", function () {
            // mascara 00000-000
            let v = this.value.replace(/\D/g, "").slice(0, 8);
            if (v.length > 5) v = v.slice(0, 5) + "-" + v.slice(5);
            this.value = v;

            const digits = v.replace("-", "");
            if (digits.length === 8) {
                lookupCep(digits, form, msg);
                if (onCepFound) onCepFound(digits);
            }
        });
    });
}

function lookupCep(cep, form, msg) {
    if (msg) msg.textContent = "buscando...";
    fetch("https://viacep.com.br/ws/" + cep + "/json/")
        .then(r => r.json())
        .then(data => {
            if (data.erro) {
                if (msg) msg.textContent = "CEP não encontrado";
                return;
            }
            form.querySelector("[name=street]").value = data.logradouro || "";
            form.querySelector("[name=district]").value = data.bairro || "";
            form.querySelector("[name=city]").value = data.localidade || "";
            form.querySelector("[name=state]").value = data.uf || "";
            if (msg) msg.textContent = "";
            form.querySelector("[name=number]").focus();
        })
        .catch(() => {
            // viacep fora do ar, o cliente preenche na mao
            if (msg) msg.textContent = "não consegui buscar o CEP, preencha manualmente";
        });
}

// pagina "minha conta" tambem tem o form de endereco
if (document.querySelector(".address-form") && !document.getElementById("checkout-form")) {
    setupCepLookup();
}


// ---------------------------------------------------------
// Checkout: frete, forma de pagamento, mascara do cartao
// ---------------------------------------------------------
function initCheckout(quoteUrl) {
    const subtotal = parseFloat(document.getElementById("subtotal").dataset.value);
    const feeEl = document.getElementById("fee");
    const etaEl = document.getElementById("eta");
    const totalEl = document.getElementById("total");
    const btn = document.getElementById("btn-finish");
    const newAddr = document.getElementById("new-address");

    function updateQuote(cep) {
        if (!cep || cep.replace(/\D/g, "").length !== 8) {
            feeEl.textContent = "informe o CEP";
            etaEl.textContent = "-";
            totalEl.textContent = formatBRL(subtotal);
            return;
        }
        fetch(quoteUrl + "?cep=" + cep)
            .then(r => r.json())
            .then(res => {
                if (!res.ok) {
                    feeEl.textContent = res.msg;
                    etaEl.textContent = "-";
                    btn.disabled = true;
                    return;
                }
                btn.disabled = false;
                feeEl.textContent = res.fee_txt;
                etaEl.textContent = "~" + res.minutes + " min";
                totalEl.textContent = formatBRL(subtotal + res.fee);
            });
    }

    function currentCep() {
        const checked = document.querySelector("input[name=address_id]:checked");
        if (!checked) return "";
        if (checked.value === "new") {
            return document.querySelector("#new-address .cep-input").value;
        }
        return checked.dataset.cep;
    }

    // troca entre endereco salvo e novo
    document.querySelectorAll("input[name=address_id]").forEach(r => {
        r.addEventListener("change", () => {
            newAddr.classList.toggle("hidden", r.value !== "new" || !r.checked);
            updateQuote(currentCep());
        });
    });

    setupCepLookup(cep => updateQuote(cep));

    // pix x cartao
    document.querySelectorAll("input[name=payment_method]").forEach(r => {
        r.addEventListener("change", () => {
            const isPix = document.querySelector("input[name=payment_method]:checked").value === "pix";
            document.getElementById("card-fields").classList.toggle("hidden", isPix);
            document.getElementById("pix-info").classList.toggle("hidden", !isPix);
        });
    });

    // mascaras do cartao
    const cardInput = document.querySelector("[name=card_number]");
    cardInput.addEventListener("input", function () {
        let v = this.value.replace(/\D/g, "").slice(0, 19);
        this.value = v.replace(/(\d{4})(?=\d)/g, "$1 ");
    });
    const exp = document.querySelector("[name=card_expiry]");
    exp.addEventListener("input", function () {
        let v = this.value.replace(/\D/g, "").slice(0, 4);
        if (v.length > 2) v = v.slice(0, 2) + "/" + v.slice(2);
        this.value = v;
    });

    // evita clique duplo = pedido duplicado
    document.getElementById("checkout-form").addEventListener("submit", function () {
        btn.disabled = true;
        btn.textContent = "Processando...";
    });

    updateQuote(currentCep());
}


// ---------------------------------------------------------
// Acompanhamento do pedido (US06) - polling a cada 10s
// ---------------------------------------------------------
const STEPS = ["recebido", "em_preparo", "saiu", "entregue"];

function paintTracker(status) {
    const idx = STEPS.indexOf(status);
    document.querySelectorAll("#tracker .step").forEach((el, i) => {
        el.classList.toggle("done", i <= idx);
        el.classList.toggle("current", i === idx);
    });
}

function startOrderTracking(url) {
    let lastStatus = document.getElementById("tracker").dataset.status;

    const timer = setInterval(function () {
        fetch(url)
            .then(r => r.json())
            .then(data => {
                if (data.status === lastStatus) return;
                lastStatus = data.status;

                paintTracker(data.status);
                const lbl = document.getElementById("status-label");
                lbl.textContent = data.label;
                lbl.className = "status status-" + data.status;

                if (data.status === "entregue") {
                    clearInterval(timer);
                    document.getElementById("eta-text").textContent = "Pedido entregue! Bom café ☕";
                    const rb = document.getElementById("review-box");
                    if (rb && data.can_review) rb.classList.remove("hidden");
                }
            })
            .catch(err => console.log("erro no polling", err));
    }, 10000);
}


// ---------------------------------------------------------
// Painel do atendente (US11 / US12)
// ---------------------------------------------------------
function startStaffPanel(jsonUrl, advanceUrlTemplate) {
    let knownIds = null; // null = primeira carga, nao toca som
    const nextLabel = { em_preparo: "Iniciar preparo", saiu: "Saiu p/ entrega", entregue: "Marcar entregue" };

    function beep() {
        if (!document.getElementById("sound-on").checked) return;
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880;
            gain.gain.value = 0.2;
            osc.start();
            // dois bipes
            setTimeout(() => { osc.frequency.value = 660; }, 200);
            setTimeout(() => { osc.stop(); ctx.close(); }, 450);
        } catch (e) {
            // alguns navegadores bloqueiam audio sem interacao do usuario
            console.log("nao rolou tocar o som", e);
        }
    }

    function card(o, done) {
        let html = '<div class="k-card' + (done ? " k-done" : "") + '">';
        html += '<div class="k-top"><strong>#' + o.id + '</strong><span>' + o.time + "</span></div>";
        html += '<div class="k-cust">' + escapeHtml(o.customer) + "</div>";
        html += "<ul>";
        o.items.forEach(i => {
            html += "<li>" + i.qty + "x " + escapeHtml(i.name);
            if (i.notes) html += ' <em>(' + escapeHtml(i.notes) + ")</em>";
            html += "</li>";
        });
        html += "</ul>";
        html += '<small class="muted">' + escapeHtml(o.address) + "</small>";
        if (o.next) {
            html += '<button class="btn btn-sm btn-block" data-id="' + o.id + '">' + nextLabel[o.next] + "</button>";
        }
        html += "</div>";
        return html;
    }

    function render(data) {
        const cols = { recebido: "", em_preparo: "", saiu: "" };
        data.active.forEach(o => { cols[o.status] += card(o, false); });

        for (const st in cols) {
            document.getElementById("k-" + st).innerHTML = cols[st] || '<p class="muted small">nenhum</p>';
            document.getElementById("c-" + st).textContent = data.active.filter(o => o.status === st).length;
        }
        document.getElementById("k-entregue").innerHTML =
            data.done.map(o => card(o, true)).join("") || '<p class="muted small">nenhum ainda</p>';

        // detecta pedido novo
        const ids = data.active.filter(o => o.status === "recebido").map(o => o.id);
        if (knownIds !== null) {
            const hasNew = ids.some(id => !knownIds.includes(id));
            if (hasNew) beep();
        }
        knownIds = ids.concat(knownIds || []);

        document.getElementById("last-update").textContent =
            "atualizado às " + new Date().toLocaleTimeString("pt-BR");
    }

    function load() {
        fetch(jsonUrl)
            .then(r => {
                if (r.status !== 200) throw new Error("status " + r.status);
                return r.json();
            })
            .then(render)
            .catch(e => console.log("falha ao carregar pedidos", e));
    }

    // clique no botao de avancar status (delegacao de evento pq os cards sao recriados)
    document.querySelector(".kanban").addEventListener("click", function (ev) {
        const b = ev.target.closest("button[data-id]");
        if (!b) return;
        b.disabled = true;
        const url = advanceUrlTemplate.replace("/0/", "/" + b.dataset.id + "/");
        fetch(url, { method: "POST", headers: { "X-Requested-With": "fetch" } })
            .then(r => r.json())
            .then(() => load());
    });

    load();
    setInterval(load, 8000);
}

function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}
