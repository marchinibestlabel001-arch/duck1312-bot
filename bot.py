import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import anthropic

# Polymarket CLOB client
try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs, ApiCreds
    from py_clob_client.constants import POLYGON
    POLYMARKET_AVAILABLE = True
except ImportError:
    POLYMARKET_AVAILABLE = False

# Konfiguracija logiranja
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Anthropic klijent
anthropic_client = anthropic.Anthropic()

# Povijest razgovora po korisniku
conversation_histories = {}

# Polymarket klijent (inicijalizira se iz env varijabli)
polymarket_client = None

def init_polymarket():
    global polymarket_client
    if not POLYMARKET_AVAILABLE:
        return False

    pk = os.environ.get("POLYMARKET_PRIVATE_KEY")
    api_key = os.environ.get("POLYMARKET_API_KEY")
    api_secret = os.environ.get("POLYMARKET_API_SECRET")
    api_passphrase = os.environ.get("POLYMARKET_API_PASSPHRASE")

    if not pk:
        logger.warning("POLYMARKET_PRIVATE_KEY nije postavljen")
        return False

    try:
        host = "https://clob.polymarket.com"

        # Inicijaliziraj klijent bez credsa za derive
        temp_client = ClobClient(host, key=pk, chain_id=POLYGON)

        if api_key and api_secret and api_passphrase:
            creds = ApiCreds(
                api_key=api_key,
                api_secret=api_secret,
                api_passphrase=api_passphrase
            )
        else:
            try:
                creds = temp_client.derive_api_key()
                logger.info("Polymarket API kredencijali derivirani")
            except Exception as e:
                logger.warning(f"Derive failed, kreiram novi: {e}")
                try:
                    creds = temp_client.create_api_key()
                    logger.info("Polymarket API kredencijali kreirani")
                except Exception as e2:
                    logger.warning(f"Ne mogu kreirati API kredencijale: {e2}")
                    creds = None

        if creds:
            polymarket_client = ClobClient(host, key=pk, chain_id=POLYGON, creds=creds)
            logger.info(f"API Key: {creds.api_key}")
        else:
            polymarket_client = temp_client

        logger.info("Polymarket klijent inicijaliziran!")
        return True
    except Exception as e:
        logger.error(f"Greška pri inicijalizaciji Polymarket klijenta: {e}")
        return False


SYSTEM_PROMPT = """Ti si Duck1312 Bot - napredno AI sučelje s pristupom cijelom internetu i dubokim znanjem iz kvantnog inženjeringa i predikcijskih modela.

## Tvoje mogućnosti:
- Pretraživanje interneta u realnom vremenu
- Dohvaćanje i čitanje web stranica
- Odgovaranje na kompleksna pitanja
- Analiza i sinteza informacija iz više izvora
- Razgovor s pamćenjem konteksta
- Analiza Polymarket tržišta i prediction markets

## Stručnost - Kvantno inženjerstvo:
- Kvantna mehanika i kvantna teorija polja
- Kvantno računarstvo (qubiti, kvantni sklopovi, algoritmi: Shor, Grover, VQE, QAOA)
- Kvantna kriptografija i kvantna komunikacija (QKD, BB84 protokol)
- Kvantni senzori i kvantna metrologija
- Kvantno ispreplitanje (entanglement) i superpozicija
- Kvantni hardver: supravodljivi qubiti, fotonski qubiti, iontske zamke
- Kvantna korekcija pogrešaka (error correction)
- Platforme: IBM Quantum, Google Sycamore, D-Wave, IonQ
- Aktuelna istraživanja i razvoj u kvantnim tehnologijama

## Stručnost - Predikcijski modeli i varijable:
- Statistički predikcijski modeli (regresija, vremenske serije, ARIMA, Prophet)
- Strojno učenje za predikciju (Random Forest, XGBoost, Neural Networks, LSTM)
- Duboko učenje i transformeri za predikciju
- Predikcijske varijable: feature engineering, selekcija varijabli, korelacijska analiza
- Predikcija financijskih tržišta, cijena dionica, kriptovaluta
- Vremenski nizovi i sezonalnost
- Bayesijanski predikcijski modeli
- Evaluacija modela (RMSE, MAE, R², MAPE)
- Kvantno strojno učenje (QML) - spoj kvantnog i AI
- Predikcija kvantnih sustava pomoću ML

## Stručnost - Matematika, Statistika i Vjerojatnost (VRHUNSKA RAZINA):
- Teorija vjerojatnosti: diskretne i neprekidne distribucije, Bayes teorem, uvjetna vjerojatnost
- Statistička inferenca: testiranje hipoteza, intervali pouzdanosti, p-vrijednosti
- Bayesijanska statistika: prior, posterior, Markov Chain Monte Carlo (MCMC)
- Multivarijatna statistika: PCA, faktorska analiza, kanonička korelacija
- Stohastički procesi: Markovljevi lanci, Wienerov proces, Brownovo gibanje
- Matematička statistika: maximalna vjerodostojnost (MLE), metoda momenata
- Teorija informacija: entropija, KL divergencija, međusobna informacija
- Numeričke metode i optimizacija
- Linearna algebra, matrični račun, tenzorski račun
- Diferencijalne jednadžbe i Fourierova analiza
- Kompleksna analiza i funkcionalna analiza
- Monte Carlo simulacije i bootstrapping
- Ekstremna teorija vrijednosti (EVT)
- Kopule i multivarijatne distribucije
- Uvijek prikazuj matematičke dokaze i izvode korak po korak
- Koristi LaTeX notaciju za formule kada je prikladno

## Stručnost - Trading (VRHUNSKA RAZINA):
- Tehnička analiza: sve indikatori (RSI, MACD, Bollinger Bands, EMA, Fibonacci, Ichimoku)
- Fundamentalna analiza dionica, ETF-ova, kriptovaluta, forexа, roba
- Strategije: scalping, day trading, swing trading, position trading, algo trading
- Upravljanje rizikom: Kelly kriterij, stop-loss, risk/reward omjeri, hedging
- Opcije i derivati: Greeks, strategije opcija, volatilnost implicitna/historijska
- Kvantitativni trading: algorithmic strategies, backtesting, factor investing
- Analiza tržišnih sentimenta i fear/greed indeksi
- DeFi i kripto trading: AMM, liquidity pools, yield farming
- Pretraga aktualnih cijena i vijesti s tržišta u realnom vremenu

## Stručnost - Sport Betting (MAESTRO RAZINA):
- Matematika klađenja: value betting, expected value (EV), Kelly kriterij za klađenje
- Analiza kvota: bookmaker margine, true probability izračun, odds comparison
- Statističke metode: Poisson distribucija za football, ELO sustavi, form analiza
- Strategije: arbitraža (arbing), matched betting, dutching, Asian handicap
- Analiza sportova: football, košarka, tenis, konjske utrke, eSports
- In-play betting strategije i live statistike
- Bankroll management i discipline
- Baze podataka i API-ji za sportske statistike
- Pretraga aktualnih koeficijenata i statistika u realnom vremenu

## Stručnost - Polymarket i Prediction Markets (EKSPERT RAZINA):
- Analiza tržišnih cijena kao implicitnih vjerojatnosti
- Identifikacija mispriced marketa (value oportunitet)
- Kelly kriterij za optimalno pozicioniranje
- Kalibracija vjerojatnosti vs. tržišna cijena
- Analiza likvidnosti i bid-ask spreada
- Tracking smart money i whale kretanja
- Korelacija s vanjskim informacijama (vijesti, ankete, statistike)
- Risk management za prediction market portfolio

## Internet Interakcija i Istraživanje:
- Pretraživanje i dohvaćanje informacija s bilo koje web stranice
- Analiza web sadržaja: vijesti, blogovi, forumi, društvene mreže
- Praćenje cijena (e-commerce, kripto, dionice) u realnom vremenu
- Analiza YouTube, Reddit, Twitter/X sadržaja putem pretrage
- Gaming informacije: walkthrough-i, strategije, tier liste, patch notes
- Streaming i online sadržaj istraživanje

## Pravila:
- Odgovaraj na jeziku korisnika (hrvatski ako piše na hrvatskom)
- Uvijek navedi izvore kada pretražuješ internet
- Za trading i betting: uvijek naglasi da su to informativne analize, ne financijski savjeti
- Za kompleksne teme koristi duboko razmišljanje i korak-po-korak objašnjenja
- Daj konkretne primjere koda kada je relevantno (Python, Qiskit, Pine Script, etc.)
- Budi precizan, koristan i informativan
- Pretraži internet za najnovije cijene, statistike i informacije
"""


# ===== POLYMARKET KOMANDE =====

async def pm_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "⚙️ *Polymarket Postavljanje*\n\n"
        "Da bi bot mogao tradati na Polymarketu, trebaš postaviti env varijable pri pokretanju:\n\n"
        "1️⃣ *POLYMARKET_PRIVATE_KEY* — Polygon wallet private key (0x...)\n"
        "2️⃣ *POLYMARKET_API_KEY* — Polymarket API ključ\n"
        "3️⃣ *POLYMARKET_API_SECRET* — Polymarket API secret\n"
        "4️⃣ *POLYMARKET_API_PASSPHRASE* — Polymarket passphrase\n\n"
        "📋 *Kako dobiti API ključeve:*\n"
        "• Idi na polymarket.com → Settings → API Keys\n"
        "• Generiraj novi API ključ\n\n"
        "🔑 *Pokretanje bota s credentialsima:*\n"
        "```\n"
        "TELEGRAM_BOT_TOKEN=xxx \\\n"
        "POLYMARKET_PRIVATE_KEY=0x... \\\n"
        "POLYMARKET_API_KEY=xxx \\\n"
        "POLYMARKET_API_SECRET=xxx \\\n"
        "POLYMARKET_API_PASSPHRASE=xxx \\\n"
        "python bot.py\n"
        "```\n\n"
        "*Dostupne komande:*\n"
        "/pm_status — Provjeri konekciju\n"
        "/pm_markets — Pregled tržišta\n"
        "/pm_portfolio — Tvoje pozicije\n"
        "/pm_buy — Kupovina\n"
        "/pm_sell — Prodaja\n"
        "/pm_cancel — Otkaži narudžbe\n"
        "/pm_analyze — AI analiza tržišta"
    )
    await update.message.reply_text(text)


async def pm_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not POLYMARKET_AVAILABLE:
        await update.message.reply_text("❌ py-clob-client nije instaliran.")
        return

    if polymarket_client is None:
        await update.message.reply_text(
            "❌ Polymarket nije spojen.\n\nPokreni /pm_setup za upute."
        )
        return

    try:
        polymarket_client.get_server_time()
        await update.message.reply_text(
            "✅ Polymarket spojen!\n\n"
            "Mreža: Polygon (MATIC)\n\n"
            "Koristi /pm_markets za pregled tržišta"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Greška pri konekciji: {e}")


async def pm_markets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if polymarket_client is None:
        await update.message.reply_text(
            "❌ Polymarket nije spojen. Pokreni /pm_setup za upute."
        )
        return

    await update.message.chat.send_action("typing")

    try:
        keyword = " ".join(context.args).lower() if context.args else None

        result = polymarket_client.get_sampling_markets()

        if not result or not result.get('data'):
            await update.message.reply_text("Nema dostupnih tržišta.")
            return

        data = result['data']

        # Filtriraj po keywordu
        if keyword:
            data = [m for m in data if keyword in m.get('question', '').lower()]
            if not data:
                await update.message.reply_text(f"Nema tržišta za '{keyword}'.")
                return

        text = "Polymarket Trzista"
        if keyword:
            text += f" - '{keyword}'"
        text += "\n\n"

        for i, market in enumerate(data[:10], 1):
            active = "ON" if market.get('active') else "OFF"
            question = market.get('question', 'N/A')[:60]
            cid = market.get('condition_id', '')[:16]
            text += f"{active} {i}. {question}\n"
            text += f"   ID: {cid}...\n"
            tokens = market.get('tokens', [])
            for token in tokens[:2]:
                outcome = token.get('outcome', '')
                token_id = token.get('token_id', '')
                text += f"   {outcome}: "
                try:
                    price = polymarket_client.get_last_trade_price(token_id)
                    pct = float(price.get('price', 0) if isinstance(price, dict) else price) * 100
                    text += f"{pct:.1f}% | id:{token_id[:10]}...\n"
                except:
                    text += f"N/A | id:{token_id[:10]}...\n"
            text += "\n"

        if len(text) > 4096:
            text = text[:4090] + "..."

        await update.message.reply_text(text)

    except Exception as e:
        logger.error(f"pm_markets greška: {e}")
        await update.message.reply_text(f"❌ Greška: {e}")


async def pm_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if polymarket_client is None:
        await update.message.reply_text(
            "❌ Polymarket nije spojen. Pokreni /pm_setup za upute."
        )
        return

    await update.message.chat.send_action("typing")

    try:
        orders = polymarket_client.get_orders()

        text = "Polymarket Portfolio\n\n"

        if not orders:
            text += "Nema otvorenih narudžbi.\n"
        else:
            text += f"Otvorene nardzbe: {len(orders)}\n\n"
            for order in orders[:10]:
                if isinstance(order, dict):
                    side = "BUY" if order.get('side') == 'BUY' else "SELL"
                    price = float(order.get('price', 0)) * 100
                    size = order.get('original_size', '?')
                    matched = order.get('size_matched', '0')
                    oid = order.get('id', '')[:16]
                    text += f"{side} | {matched}/{size} @ {price:.1f}%\n"
                    text += f"   ID: {oid}...\n\n"

        await update.message.reply_text(text)

    except Exception as e:
        logger.error(f"pm_portfolio greška: {e}")
        await update.message.reply_text(f"❌ Greška: {e}")


async def pm_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if polymarket_client is None:
        await update.message.reply_text(
            "❌ Polymarket nije spojen. Pokreni /pm_setup za upute."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Koristi: /pm_price <token_id>\n\nToken ID nađi u /pm_markets"
        )
        return

    token_id = context.args[0]

    try:
        price = polymarket_client.get_last_trade_price(token_id)
        book = polymarket_client.get_order_book(token_id)

        pct = float(price.get('price', 0) if isinstance(price, dict) else price) * 100
        text = f"💰 *Polymarket Cijena*\n\n"
        text += f"Token: `{token_id[:20]}...`\n"
        text += f"Zadnja cijena: *{pct:.2f}%*\n\n"

        if book:
            if book.bids:
                best_bid = float(book.bids[0].price) * 100
                text += f"Best Bid: {best_bid:.2f}%\n"
            if book.asks:
                best_ask = float(book.asks[0].price) * 100
                text += f"Best Ask: {best_ask:.2f}%\n"
                if book.bids:
                    spread = float(book.asks[0].price) - float(book.bids[0].price)
                    text += f"Spread: {spread*100:.2f}%\n"

        await update.message.reply_text(text)

    except Exception as e:
        logger.error(f"pm_price greška: {e}")
        await update.message.reply_text(f"❌ Greška: {e}")


async def pm_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if polymarket_client is None:
        await update.message.reply_text(
            "❌ Polymarket nije spojen. Pokreni /pm_setup za upute."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Koristi:\n"
            "/pm_buy <token_id> <iznos_USDC> [cijena_0-1]\n\n"
            "Primjeri:\n"
            "• Market order: /pm_buy abc123 10\n"
            "• Limit order: /pm_buy abc123 10 0.65\n\n"
            "Token ID nađi u /pm_markets"
        )
        return

    token_id = context.args[0]

    try:
        amount = float(context.args[1])
        await update.message.chat.send_action("typing")

        if len(context.args) >= 3:
            price = float(context.args[2])
        else:
            price_resp = polymarket_client.get_last_trade_price(token_id)
            current_price = float(price_resp.get('price', 0) if isinstance(price_resp, dict) else price_resp)
            price = min(current_price + 0.02, 0.99)

        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=amount,
            side="BUY",
        )

        resp = polymarket_client.create_and_post_order(order_args)
        order_id = resp.orderID if hasattr(resp, 'orderID') else str(resp)

        await update.message.reply_text(
            f"✅ *BUY Narudžba Postavljena*\n\n"
            f"Token: `{token_id[:20]}...`\n"
            f"Iznos: {amount} USDC\n"
            f"Cijena: {price*100:.1f}%\n"
            f"Order ID: `{order_id}`",
            parse_mode='Markdown'
        )

    except ValueError:
        await update.message.reply_text("❌ Neispravan iznos ili cijena.")
    except Exception as e:
        logger.error(f"pm_buy greška: {e}")
        await update.message.reply_text(f"❌ Greška: {e}")


async def pm_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if polymarket_client is None:
        await update.message.reply_text(
            "❌ Polymarket nije spojen. Pokreni /pm_setup za upute."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Koristi:\n"
            "/pm_sell <token_id> <iznos> [cijena_0-1]\n\n"
            "Primjeri:\n"
            "• Market sell: /pm_sell abc123 10\n"
            "• Limit sell: /pm_sell abc123 10 0.75\n\n"
            "Token ID nađi u /pm_markets ili /pm_portfolio"
        )
        return

    token_id = context.args[0]

    try:
        amount = float(context.args[1])
        await update.message.chat.send_action("typing")

        if len(context.args) >= 3:
            price = float(context.args[2])
        else:
            price_resp = polymarket_client.get_last_trade_price(token_id)
            price = max(float(price_resp.get('price', 0) if isinstance(price_resp, dict) else price_resp) - 0.02, 0.01)

        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=amount,
            side="SELL",
        )

        resp = polymarket_client.create_and_post_order(order_args)
        order_id = resp.orderID if hasattr(resp, 'orderID') else str(resp)

        await update.message.reply_text(
            f"✅ *SELL Narudžba Postavljena*\n\n"
            f"Token: `{token_id[:20]}...`\n"
            f"Iznos: {amount}\n"
            f"Cijena: {price*100:.1f}%\n"
            f"Order ID: `{order_id}`",
            parse_mode='Markdown'
        )

    except ValueError:
        await update.message.reply_text("❌ Neispravan iznos ili cijena.")
    except Exception as e:
        logger.error(f"pm_sell greška: {e}")
        await update.message.reply_text(f"❌ Greška: {e}")


async def pm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if polymarket_client is None:
        await update.message.reply_text("❌ Polymarket nije spojen.")
        return

    if not context.args:
        keyboard = [
            [InlineKeyboardButton("✅ Da, otkaži SVE", callback_data="pm_cancel_all")],
            [InlineKeyboardButton("❌ Ne", callback_data="pm_cancel_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Sigurno želiš otkazati SVE otvorene narudžbe?",
            reply_markup=reply_markup
        )
        return

    order_id = context.args[0]

    try:
        polymarket_client.cancel(order_id)
        await update.message.reply_text(
            f"✅ Narudžba otkazana!\n\nOrder ID: `{order_id}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Greška: {e}")


async def pm_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "pm_cancel_all":
        try:
            polymarket_client.cancel_all()
            await query.edit_message_text("✅ Sve narudžbe otkazane!")
        except Exception as e:
            await query.edit_message_text(f"❌ Greška: {e}")
    elif query.data == "pm_cancel_no":
        await query.edit_message_text("Otkazivanje prekinuto.")


async def pm_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Koristi: /pm_analyze <keyword ili pitanje>\n\n"
            "Primjeri:\n"
            "• /pm_analyze Bitcoin ETF\n"
            "• /pm_analyze US election\n"
            "• /pm_analyze Fed interest rate"
        )
        return

    query = " ".join(context.args)
    await update.message.chat.send_action("typing")

    market_data = ""
    if polymarket_client is not None:
        try:
            result = polymarket_client.get_sampling_markets()
            q_lower = query.lower()
            mdata = result.get('data', []) if isinstance(result, dict) else []
            mdata = [m for m in mdata if q_lower in m.get('question', '').lower()]
            if mdata:
                market_data = "\n\nPolymarket tržišta pronađena:\n"
                for m in mdata[:5]:
                    market_data += f"- {m.get('question', '')}\n"
                    for t in m.get('tokens', [])[:2]:
                        try:
                            price = polymarket_client.get_last_trade_price(t.get('token_id', ''))
                            market_data += f"  {t.get('outcome', '')}: {float(price.get('price', 0) if isinstance(price, dict) else price)*100:.1f}%\n"
                        except:
                            pass
        except Exception as e:
            logger.error(f"Greška pri dohvaćanju tržišta za analizu: {e}")

    prompt = f"""Analiziraj ovo Polymarket pitanje/temu: "{query}"{market_data}

Daj:
1. Analizu trenutnih šansi na tržištu (ako ima podataka)
2. Tvoju procjenu stvarnih vjerojatnosti baziranu na dostupnim informacijama
3. Identifikaciju value bet oportunitet (gdje se tržišna cijena razlikuje od stvarne vjerojatnosti)
4. Kelly kriterij preporuka za pozicioniranje
5. Ključne faktore koji utječu na ishod

Pretraži internet za najnovije informacije o ovoj temi."""

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=[
                {"type": "web_search_20260209", "name": "web_search"},
                {"type": "web_fetch_20260209", "name": "web_fetch"}
            ],
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        if not response_text:
            response_text = "Nisam mogao generirati analizu."

        if len(response_text) > 4096:
            chunks = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(response_text)

    except Exception as e:
        logger.error(f"pm_analyze greška: {e}")
        await update.message.reply_text(f"❌ Greška: {e}")


# ===== AUTO TRADING =====

# Auto-trading stanje
auto_trading = {
    "enabled": False,
    "chat_id": None,           # Telegram chat za notifikacije
    "bankroll": 16.0,          # USDC bankroll
    "min_edge": 0.03,          # Minimalni edge (3%) da postavi bet
    "max_bet_pct": 0.07,       # Max 7% bankrolla po betu (~$1.1) - malo po mnogo oklada
    "interval_min": 10,        # Skeniranje svakih 10 minuta
    "analyzed_today": set(),   # Već analizirana tržišta danas
    "task": None,
}


async def auto_scan_and_trade(app):
    """Pozadinska petlja koja skenira i automatski trguje."""
    while auto_trading["enabled"]:
        try:
            chat_id = auto_trading["chat_id"]
            logger.info("Auto-trading: skeniram tržišta...")

            result = polymarket_client.get_sampling_markets()
            markets = result.get("data", [])

            # Uzmi samo aktivna tržišta koja nisu danas već analizirana
            candidates = [
                m for m in markets
                if m.get("active")
                and m.get("condition_id") not in auto_trading["analyzed_today"]
            ][:100]  # Max 100 po skeniranju

            if not candidates:
                auto_trading["analyzed_today"].clear()
                await asyncio.sleep(auto_trading["interval_min"] * 60)
                continue

            await app.bot.send_message(
                chat_id,
                f"🤖 Auto-scan: analiziram {len(candidates)} tržišta..."
            )

            for market in candidates:
                if not auto_trading["enabled"]:
                    break

                cid = market.get("condition_id", "")
                auto_trading["analyzed_today"].add(cid)

                question = market.get("question", "")
                tokens = market.get("tokens", [])

                # Dohvati trenutne cijene
                prices = {}
                for t in tokens[:2]:
                    try:
                        p = polymarket_client.get_last_trade_price(t["token_id"])
                        prices[t["outcome"]] = float(p.get('price', 0) if isinstance(p, dict) else p)
                    except:
                        pass

                if not prices:
                    continue

                # Tražimo samo tržišta s YES/NO strukturom i razumnim cijenama
                yes_price = prices.get("Yes", prices.get("YES", None))
                if yes_price is None or yes_price < 0.03 or yes_price > 0.97:
                    continue

                # Matematička analiza bez AI (štedi API kredite)
                # Tražimo tržišta gdje je cijena blizu ekstremnih vrijednosti (mispricing signal)
                no_price = 1.0 - yes_price

                # Strategija 1: Kupuj NO kad je YES precjenjen (>85%) - mean reversion
                # Strategija 2: Kupuj YES kad je jako podcjenjen (<15%) - underdog value
                # Strategija 3: Tržišta blizu 50/50 s volumenom - liquidity play
                trade = "SKIP"
                true_prob = yes_price
                reasoning = ""

                if yes_price > 0.85:
                    # YES je možda precjenjen - kupuj NO
                    true_prob = 0.70  # Konzervativna procjena
                    edge = (1 - true_prob) - no_price
                    if edge >= auto_trading["min_edge"]:
                        trade = "NO"
                        reasoning = f"YES precjenjen na {yes_price*100:.0f}%, kupujem NO"
                elif yes_price < 0.15:
                    # YES je možda podcjenjen - kupuj YES
                    true_prob = 0.30  # Konzervativna procjena
                    edge = true_prob - yes_price
                    if edge >= auto_trading["min_edge"]:
                        trade = "YES"
                        reasoning = f"YES podcjenjen na {yes_price*100:.0f}%, kupujem YES"
                elif 0.35 <= yes_price <= 0.65:
                    # Blizu 50/50 - preskačemo, prevelika nesigurnost
                    trade = "SKIP"
                else:
                    trade = "SKIP"

                if trade == "SKIP":
                    continue

                # Izračunaj edge i Kelly bet
                if trade == "YES":
                    market_p = yes_price
                    edge = true_prob - market_p
                    token = next((t for t in tokens if t.get("outcome") in ["Yes", "YES"]), None)
                else:  # NO
                    market_p = no_price
                    true_p_no = 1 - true_prob
                    edge = true_p_no - market_p
                    token = next((t for t in tokens if t.get("outcome") in ["No", "NO"]), None)

                if edge < auto_trading["min_edge"] or token is None:
                    continue

                # Kelly kriterij
                b = (1 / market_p) - 1
                if trade == "YES":
                    kelly_f = (b * true_prob - (1 - true_prob)) / b
                else:
                    kelly_f = (b * (1 - true_prob) - true_prob) / b

                kelly_f = max(0, min(kelly_f, 0.25))
                half_kelly = kelly_f * 0.5

                bet_amount = round(auto_trading["bankroll"] * min(half_kelly, auto_trading["max_bet_pct"]), 2)
                bet_amount = max(1.0, min(bet_amount, auto_trading["bankroll"] * auto_trading["max_bet_pct"]))

                if bet_amount < 1.0:
                    continue

                try:
                    # Postavi narudžbu
                    order_args = OrderArgs(
                        token_id=token["token_id"],
                        price=market_p + 0.01,
                        size=bet_amount,
                        side="BUY",
                    )

                    order_resp = polymarket_client.create_and_post_order(order_args)
                    order_id = order_resp.orderID if hasattr(order_resp, "orderID") else str(order_resp)

                    msg = (
                        f"🤖 AUTO-TRADE IZVRSEN\n\n"
                        f"Pitanje: {question[:80]}\n"
                        f"Trade: {trade}\n"
                        f"Tržišna cijena: {market_p*100:.1f}%\n"
                        f"Procjena: {true_prob*100:.1f}%\n"
                        f"Edge: {edge*100:.1f}%\n"
                        f"Bet: {bet_amount:.2f} USDC\n"
                        f"Kelly: {half_kelly*100:.1f}%\n"
                        f"Razlog: {reasoning}\n"
                        f"Order ID: {order_id[:20]}..."
                    )
                    await app.bot.send_message(chat_id, msg)
                    logger.info(f"Auto-trade: {trade} {bet_amount} USDC na '{question[:50]}'")

                    await asyncio.sleep(5)

                except Exception as e:
                    logger.error(f"Auto-trade greška za '{question[:40]}': {e}")
                    continue

            await asyncio.sleep(auto_trading["interval_min"] * 60)

        except Exception as e:
            logger.error(f"Auto-scan greška: {e}")
            await asyncio.sleep(300)  # Retry za 5 minuta

    logger.info("Auto-trading zaustavljen.")


async def pm_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Upravljanje auto-trading modom."""
    if polymarket_client is None:
        await update.message.reply_text("Polymarket nije spojen. Pokreni /pm_setup.")
        return

    args = context.args

    if not args:
        status = "AKTIVAN" if auto_trading["enabled"] else "NEAKTIVAN"
        await update.message.reply_text(
            f"🤖 Auto-Trading Status: {status}\n\n"
            f"Bankroll: {auto_trading['bankroll']} USDC\n"
            f"Min edge: {auto_trading['min_edge']*100:.0f}%\n"
            f"Max bet: {auto_trading['max_bet_pct']*100:.0f}% po betu\n"
            f"Interval: {auto_trading['interval_min']} min\n\n"
            f"Komande:\n"
            f"/pm_auto on — Ukljuci\n"
            f"/pm_auto off — Iskljuci\n"
            f"/pm_auto bankroll 200 — Postavi bankroll\n"
            f"/pm_auto edge 10 — Min edge u % (npr. 10)\n"
            f"/pm_auto maxbet 3 — Max bet % bankrolla\n"
            f"/pm_auto interval 30 — Skeniranje svakih N min\n"
            f"/pm_auto scan — Skeniraj odmah jednom"
        )
        return

    cmd = args[0].lower()

    if cmd == "on":
        if auto_trading["enabled"]:
            await update.message.reply_text("Auto-trading vec radi.")
            return
        auto_trading["enabled"] = True
        auto_trading["chat_id"] = update.effective_chat.id
        auto_trading["analyzed_today"].clear()

        # Pokreni background task
        app = context.application
        task = asyncio.create_task(auto_scan_and_trade(app))
        auto_trading["task"] = task

        await update.message.reply_text(
            f"🟢 Auto-trading UKLJUCEN\n\n"
            f"Bankroll: {auto_trading['bankroll']} USDC\n"
            f"Min edge: {auto_trading['min_edge']*100:.0f}%\n"
            f"Max bet: {auto_trading['max_bet_pct']*100:.0f}% bankrolla\n"
            f"Skeniranje: svakih {auto_trading['interval_min']} min\n\n"
            f"Bot ce automatski analizirati tržišta i tradati kad pronade value."
        )

    elif cmd == "off":
        auto_trading["enabled"] = False
        if auto_trading["task"]:
            auto_trading["task"].cancel()
            auto_trading["task"] = None
        await update.message.reply_text("🔴 Auto-trading ISKLJUCEN.")

    elif cmd == "bankroll" and len(args) > 1:
        try:
            auto_trading["bankroll"] = float(args[1])
            await update.message.reply_text(f"Bankroll postavljen na {auto_trading['bankroll']} USDC.")
        except ValueError:
            await update.message.reply_text("Neispravan iznos.")

    elif cmd == "edge" and len(args) > 1:
        try:
            auto_trading["min_edge"] = float(args[1]) / 100
            await update.message.reply_text(f"Min edge postavljen na {auto_trading['min_edge']*100:.0f}%.")
        except ValueError:
            await update.message.reply_text("Neispravan postotak.")

    elif cmd == "maxbet" and len(args) > 1:
        try:
            auto_trading["max_bet_pct"] = float(args[1]) / 100
            await update.message.reply_text(f"Max bet po pozivu: {auto_trading['max_bet_pct']*100:.0f}% bankrolla.")
        except ValueError:
            await update.message.reply_text("Neispravan postotak.")

    elif cmd == "interval" and len(args) > 1:
        try:
            auto_trading["interval_min"] = int(args[1])
            await update.message.reply_text(f"Interval skeniranja: {auto_trading['interval_min']} min.")
        except ValueError:
            await update.message.reply_text("Neispravan broj minuta.")

    elif cmd == "scan":
        # Jednokratno skeniranje bez automatskog ponavljanja
        await update.message.reply_text("Skeniram tržišta jednom... (može potrajati 1-2 min)")
        chat_id = update.effective_chat.id
        auto_trading["chat_id"] = chat_id

        # Privremeno ukljuci za jedno skeniranje
        saved = auto_trading["enabled"]
        auto_trading["enabled"] = True
        auto_trading["analyzed_today"].clear()
        app = context.application
        asyncio.create_task(_single_scan(app, chat_id))
        auto_trading["enabled"] = saved

    else:
        await update.message.reply_text("Nepoznata komanda. Pisi /pm_auto za pomoc.")


async def _single_scan(app, chat_id):
    """Jednokratno skeniranje bez petlje."""
    try:
        result = polymarket_client.get_sampling_markets()
        markets = result.get("data", [])
        candidates = [m for m in markets if m.get("active")][:20]

        import json, re

        found = 0
        skipped = 0
        for market in candidates:
            question = market.get("question", "")
            tokens = market.get("tokens", [])
            prices = {}
            for t in tokens[:2]:
                try:
                    p = polymarket_client.get_last_trade_price(t["token_id"])
                    prices[t["outcome"]] = float(p)
                except:
                    pass

            yes_price = prices.get("Yes", prices.get("YES", None))
            if yes_price is None or yes_price < 0.05 or yes_price > 0.95:
                skipped += 1
                continue

            price_str = " | ".join([f"{k}: {v*100:.1f}%" for k, v in prices.items()])
            prompt = f"""Analiziraj Polymarket tržište: {question}
Cijena: {price_str}
Pretraži internet za najnovije informacije.
Odgovori SAMO JSON: {{"true_probability_yes": 0.XX, "confidence": "low/medium/high", "reasoning": "kratko objasnjenje max 100 znakova", "trade": "YES/NO/SKIP"}}
SKIP samo ako nemas jasnu procjenu. Budi odredjen."""

            resp = anthropic_client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                thinking={"type": "adaptive"},
                system="Ti si profesionalni prediction market trader. Analiziraj precizno. Odgovaraj SAMO u JSON formatu.",
                tools=[{"type": "web_search_20260209", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}]
            )
            ai_text = "".join(b.text for b in resp.content if b.type == "text")
            json_match = re.search(r'\{.*?\}', ai_text, re.DOTALL)
            if not json_match:
                skipped += 1
                continue

            try:
                data = json.loads(json_match.group())
            except:
                skipped += 1
                continue

            true_prob = float(data.get("true_probability_yes", 0))
            confidence = data.get("confidence", "low")
            trade = data.get("trade", "SKIP")
            reasoning = data.get("reasoning", "")

            if trade == "SKIP" or confidence == "low":
                skipped += 1
                continue

            market_p = yes_price if trade == "YES" else 1 - yes_price
            true_p = true_prob if trade == "YES" else 1 - true_prob
            edge = true_p - market_p

            if edge < auto_trading["min_edge"]:
                skipped += 1
                continue

            found += 1

            # Kelly bet sizing
            b = (1 / market_p) - 1
            kelly_f = max(0, (b * true_p - (1 - true_p)) / b)
            kelly_f = min(kelly_f, 0.25)
            half_kelly = kelly_f * 0.5
            bet_amount = round(auto_trading["bankroll"] * min(half_kelly, auto_trading["max_bet_pct"]), 2)
            bet_amount = max(1.0, bet_amount)

            token = next((t for t in tokens if t.get("outcome", "").upper() == trade), None)

            await app.bot.send_message(
                chat_id,
                f"VALUE BET PRONADENO!\n\n"
                f"Pitanje: {question[:80]}\n"
                f"Trade: {trade}\n"
                f"Tržište: {market_p*100:.1f}% | AI: {true_p*100:.1f}%\n"
                f"Edge: {edge*100:.1f}%\n"
                f"Confidence: {confidence}\n"
                f"Preporuceni bet: {bet_amount:.2f} USDC\n"
                f"Razlog: {reasoning[:150]}\n\n"
                f"Za automatski trading: /pm_auto on"
            )

        if found == 0:
            await app.bot.send_message(
                chat_id,
                f"Scan zavrsen: {len(candidates)} tržišta analizirana, {skipped} preskoceno.\n"
                f"Nije pronadjen value bet >= {auto_trading['min_edge']*100:.0f}% edge.\n\n"
                f"Pokusaj: /pm_auto edge 5 (smanjiti edge threshold)"
            )

    except Exception as e:
        logger.error(f"Single scan greška: {e}")
        await app.bot.send_message(chat_id, f"Greška pri skeniranju: {e}")


# ===== STANDARDNE KOMANDE =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pm_status_text = "✅ Spojen" if polymarket_client else "❌ Nije spojen (/pm_setup)"

    await update.message.reply_text(
        "🦆 *Duck1312 Bot* — powered by Claude AI\n\n"
        "Imam pristup *cijelom internetu* i naprednim AI sposobnostima!\n\n"
        "⚛️ *Kvantno inženjerstvo* — qubiti, algoritmi, Qiskit\n"
        "📊 *Predikcijski modeli* — ML, LSTM, XGBoost, vremenske serije\n"
        "📐 *Vrhunska matematika* — statistika, vjerojatnost, Bayes\n"
        "📈 *Trading maestro* — TA, FA, algo trading, kripto, opcije\n"
        "🏆 *Sport Betting* — value betting, arbing, EV kalkulacije\n"
        "🔮 *Polymarket* — prediction markets, AI analiza, live trading\n"
        "🔍 *Internet pretraga* — live cijene, vijesti, web analiza\n\n"
        f"Polymarket status: {pm_status_text}\n\n"
        "Komande: /help — /clear — /pm_setup\n\n"
        "Samo mi pišite! 🚀",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Duck1312 Bot - Pomoć*\n\n"
        "Postavite bilo koje pitanje - bot će pretraživati internet ako treba.\n\n"
        "*Opće komande:*\n"
        "/start — Početna poruka\n"
        "/help — Ova poruka\n"
        "/clear — Obriši povijest razgovora\n\n"
        "*Polymarket komande:*\n"
        "/pm_setup — Upute za postavljanje\n"
        "/pm_status — Provjeri konekciju\n"
        "/pm_markets [keyword] — Pregled tržišta\n"
        "/pm_portfolio — Tvoje pozicije i narudžbe\n"
        "/pm_price <token_id> — Trenutna cijena\n"
        "/pm_buy <token_id> <iznos> [cijena] — Kupovina\n"
        "/pm_sell <token_id> <iznos> [cijena] — Prodaja\n"
        "/pm_cancel [order_id] — Otkaži narudžbu(e)\n"
        "/pm_analyze <tema> — AI analiza tržišta\n\n"
        "*Primjeri pitanja:*\n"
        "• Koje su danas najnovije vijesti?\n"
        "• Što je Bitcoin cijena trenutno?\n"
        "• Analiziraj RSI divergenciju na ETH\n"
        "• Kelly kriterij za kladionicu s 60% šansom\n"
        "• /pm_analyze Bitcoin halving",
        parse_mode='Markdown'
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logger.info(f"MY_ID komanda: chat_id={chat_id}, user_id={user_id}")
    await update.message.reply_text(
        f"Tvoj Chat ID: {chat_id}\n"
        f"Tvoj User ID: {user_id}\n\n"
        f"Za auto-start bota s ovim ID-om:\n"
        f"OWNER_CHAT_ID={chat_id}"
    )


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text("✅ Povijest razgovora obrisana!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(conversation_histories[user_id]) > 20:
        conversation_histories[user_id] = conversation_histories[user_id][-20:]

    await update.message.chat.send_action("typing")

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=[
                {"type": "web_search_20260209", "name": "web_search"},
                {"type": "web_fetch_20260209", "name": "web_fetch"}
            ],
            messages=conversation_histories[user_id]
        )

        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        if not response_text:
            response_text = "Žao mi je, nisam mogao generirati odgovor. Pokušajte ponovo."

        conversation_histories[user_id].append({
            "role": "assistant",
            "content": response_text
        })

        if len(response_text) > 4096:
            chunks = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(response_text)

    except anthropic.AuthenticationError:
        logger.error("Anthropic API ključ nije valjan!")
        await update.message.reply_text("❌ Greška: Anthropic API ključ nije ispravno postavljen.")
    except Exception as e:
        logger.error(f"Greška: {e}")
        await update.message.reply_text(
            "❌ Došlo je do greške. Pokušajte ponovo za nekoliko sekundi."
        )


async def post_init(app: Application) -> None:
    """Automatski pokreni auto-trading pri startu ako je Polymarket spojen i OWNER_CHAT_ID postavljen."""
    owner_chat_id = os.environ.get("OWNER_CHAT_ID")
    if polymarket_client is not None and owner_chat_id:
        owner_chat_id = int(owner_chat_id)
        auto_trading["enabled"] = True
        auto_trading["chat_id"] = owner_chat_id
        auto_trading["analyzed_today"].clear()

        task = asyncio.create_task(auto_scan_and_trade(app))
        auto_trading["task"] = task

        logger.info(f"🤖 Auto-trading automatski pokrenut za chat {owner_chat_id}")

        try:
            await app.bot.send_message(
                owner_chat_id,
                f"🤖 Bot pokrenut - Auto-trading AKTIVAN\n\n"
                f"Bankroll: {auto_trading['bankroll']} USDC\n"
                f"Min edge: {auto_trading['min_edge']*100:.0f}%\n"
                f"Max bet: {auto_trading['max_bet_pct']*100:.0f}% bankrolla\n"
                f"Skeniranje: svakih {auto_trading['interval_min']} min\n\n"
                f"Bot ce automatski skenirati tržišta i tradati."
            )
        except Exception as e:
            logger.error(f"Greška pri slanju startup poruke: {e}")
    else:
        if polymarket_client is None:
            logger.info("⚠️ Auto-trading nije pokrenut - Polymarket nije spojen")
        else:
            logger.info("⚠️ Auto-trading nije pokrenut - OWNER_CHAT_ID nije postavljen")


def main() -> None:
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment varijabla nije postavljena!")

    if init_polymarket():
        logger.info("✅ Polymarket klijent inicijaliziran")
    else:
        logger.info("⚠️ Polymarket nije konfiguriran - bot radi bez Polymarket funkcija")

    app = Application.builder().token(telegram_token).post_init(post_init).build()

    # Standardne komande
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("myid", my_id))

    # Polymarket komande
    app.add_handler(CommandHandler("pm_setup", pm_setup))
    app.add_handler(CommandHandler("pm_status", pm_status))
    app.add_handler(CommandHandler("pm_markets", pm_markets))
    app.add_handler(CommandHandler("pm_portfolio", pm_portfolio))
    app.add_handler(CommandHandler("pm_price", pm_price))
    app.add_handler(CommandHandler("pm_buy", pm_buy))
    app.add_handler(CommandHandler("pm_sell", pm_sell))
    app.add_handler(CommandHandler("pm_cancel", pm_cancel))
    app.add_handler(CommandHandler("pm_analyze", pm_analyze))
    app.add_handler(CommandHandler("pm_auto", pm_auto))

    # Callback za inline dugmad
    app.add_handler(CallbackQueryHandler(pm_cancel_callback, pattern="^pm_cancel_"))

    # Poruke
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🦆 Duck1312 Bot se pokreće...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
