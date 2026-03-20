# Telegram Botu

---

## Telegram botu nədir?

Telegram-da @BotFather ilə tanış olmamış hər kəs var. Amma fikirləş — əvvəllər @BotFather-a yazmısan, `/newbot` yazmısan, sənə bir token vermişdir. O token bir hərf yığınıdır, amma arxasında bir şey var: sənin adından yazıb-oxuyan bir Telegram hesabı.

Bot texniki olaraq **telefon nömrəsi olmayan xüsusi bir Telegram hesabıdır.** Normal hesab deyil. Amma yazışmaq olur, qrup əlavə etmək olur, kanal idarə etmək olur, fayl göndərə bilir, ödəniş qəbul edə bilir. Fərqi budur ki, onun arxasında bir insan yox, sənin serverdə işləyən kod dayanır.

İstifadə halları:

- İstifadəçi bot ilə yazışır → bot cavab verir (müştəri dəstəyi, FAQ, satış)
- Hər gün saat 08:00-da avtomatik xəbər göndərir (bildiriş sistemi)
- Fayl qəbul edir, emal edir, geri göndərir (alət botu)
- Komanda işləndirir (`/backup`, `/status`, `/deploy`) (admin botu)
- Qrupda moderator kimi işləyir (spam silmə, qeydiyyat)

---

## Telegram Bot API nədir?

Telegram-ın botlarla danışmaq üçün açdığı bir HTTP interfeysidir.

Sən Telegram-ın içinə birbaşa girə bilmirsən. Onların serverlərinin içini, şifrələmə protokollarını (MTProto) bilmək lazım deyil. Telegram deyir ki: "Mən sənə sadə bir API verirəm, sən ora HTTP sorğusu göndər, mən işi görürəm."

Əsas URL belədir:

```
https://api.telegram.org/bot<TOKEN>/<METHOD>
```

Məsələn, botun özü haqqında məlumat almaq:

```
https://api.telegram.org/bot123456:ABC-DEF/getMe
```

Bu URL-ə brauzerdən belə girsən, JSON cavab gəlir:

```json
{
  "ok": true,
  "result": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "Hoca Botu",
    "username": "hoca_bot"
  }
}
```

Beləcə sadədir. Hər bot əməliyyatı bu URL formatına uyğundur.

---

## İlk addım: BotFather

Bot yaratmaq üçün Telegram-da `@BotFather`-a yaz:

```
/newbot
```

Sual verəcək:
1. Botun adı nə olsun? → `Hoca Bot`
2. Botun istifadəçi adı nə olsun? → `hoca_bot` (mütləq `bot` ilə bitməlidir)

BotFather sənə belə bir şey verir:

```
Done! Congratulations on your new bot.
Use this token to access the HTTP API:
5839201847:AAHjt2kX9...
```

Bu token sənin "açarın"dır. Bunu heç kimə vermə, git-ə yükləmə, `.env`-də saxla.

---

## Ham API ilə mesaj göndərmək

Token əlindədir. İndi bir mesaj göndər — hər hansı bir proqram, curl, Postman, Python `requests` — fərq etməz.

```python
import requests

TOKEN = "5839201847:AAHjt2kX9..."
CHAT_ID = 123456789  # Alıcının chat id-si

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": "Salam hocam"
    }
)
```

Bu qədər. Telegram API-ya bir HTTP POST sorğusu atdın, Telegram o mesajı göndərdi.

Amma burada bir sual yaranır: **CHAT_ID haradan gəldi?**

### Update-lər və chat_id

Bota bir mesaj göndərildikdə, Telegram o hadisəni bir **update** (yenilik) kimi saxlayır. Bu update-i əldə etmək üçün `getUpdates` metoduna bax:

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

Cavab belə görünür:

```json
{
  "ok": true,
  "result": [
    {
      "update_id": 100000001,
      "message": {
        "message_id": 1,
        "from": {
          "id": 123456789,
          "first_name": "Mecgec",
          "username": "mecgec_user"
        },
        "chat": {
          "id": 123456789,
          "type": "private"
        },
        "text": "Salam hocam"
      }
    }
  ]
}
```

Budur — `chat.id` sənin lazım olan CHAT_ID-dir. Bota yazan adamın ID-si.

---

## Ham API ilə işin çətinliyi

`requests.post(...)` ilə bot yazmaq mümkündür. Amma bir müddət sonra yorursan:

- Hər gələn mesajı özün parse etməlisən (`result[0]["message"]["text"]` kimi JSON qazırsın)
- Komutları özün ayrışdırmalısan (`/start` mı, `/help` mi?)
- Xətaları özün idarə etməlisən
- Update-ləri özün sorğulayıb gözləməlisən

Bunu daha gözəl göstərmək üçün bir analogiya: ham API-la bot yazmaq, Python-da web sayt yazmaq üçün `socket` açıb HTTP başlıqlarını əl ilə yazmağa bənzəyir. Mümkündür, amma kimə lazımdır ki?

İşte buna görə kitabxanalar var.

---

## Kitabxanalar — "sənin yerinə düşünür"

Kitabxana sadəcə bir "sarğı"dır (wrapper). Arxada yenə eyni HTTP sorğuları gedir, yenə eyni Telegram API-ya toxunulur. Amma sən bunları görmürsən. Sən yalnız:

```python
async def start(update, context):
    await update.message.reply_text("Iyi oxumalar yawru, sualın olsa çəkinmə")
```

yazırsan — kitabxana qalanını özü edir.

**Python üçün əsas kitabxanalar:**

| Kitabxana | Xülasə |
|-----------|--------|
| **python-telegram-bot** | Ən məşhur, tam xüsusiyyətli, Telegram Bot API-nı tam əhatə edir |
| **aiogram** | Async-first, sürətli, böyük miqyaslı botlar üçün |
| **Telebot (pyTelegramBotAPI)** | Sadə, sürətli başlanğıc, sinxron |

Biz **python-telegram-bot**-u işlədəcəyik.

---

## python-telegram-bot

**Rəsmi sayt:** https://python-telegram-bot.org
**GitHub:** https://github.com/python-telegram-bot/python-telegram-bot
**Sənədlər:** https://docs.python-telegram-bot.org
**PyPI:** https://pypi.org/project/python-telegram-bot

Hal-hazırda **v22.x** versiyasındadır, Telegram Bot API 9.5-i tam dəstəkləyir. Python 3.10+ tələb edir, tam asinxrondur (`asyncio`).

**Qurulum:**

```bash
pip install python-telegram-bot
```

Webhook istifadə edəcəksənsə:

```bash
pip install "python-telegram-bot[webhooks]"
```

---

## Update mexanizması: Polling vs Webhook

Botun mesajları necə aldığını anlamaq lazımdır. İki üsul var.

### Polling (Sorğulama)

Bot hər birkaç saniyədə Telegram-a soruşur: "Mənim üçün yeni mesaj var mı?"

```
Bot → Telegram: getUpdates?
Telegram → Bot: [yeni mesajlar]
Bot → Telegram: getUpdates?
Telegram → Bot: []
Bot → Telegram: getUpdates?
...
```

Poçt anologiyası ilə desək: sən hər 5 dəqiqədə qutunu yoxlayırsan.

**Üstünlüyü:** Lokal kompüterdə, statik IP olmadan işləyir. Test üçün idealdır.
**Dezavantajı:** Resurs istehlakı yüksəkdir. Heç mesaj olmasa belə daim sorğu gedir.

### Webhook

Sən bir dəfə Telegram-a deyirsən ki: "Yeni mesaj gəldikdə bunu bu URL-ə göndər." Bundan sonra Telegram özü sənin serverinə POST edir.

```
İstifadəçi → Telegram: "Salam hocam"
Telegram → Sənin server: POST https://qiyas.cc/webhook (JSON)
Sənin kod: mesajı oxu, cavabı ver
```

Poçt anologiyası ilə desək: postacı gəlib qapını döyür.

**Üstünlüyü:** Daha sürətli, daha az resurs, production üçün standart.
**Dezavantajı:** HTTPS tələb edir, public URL lazımdır (localhost işləmir).

---

## İlk bot — polling ilə

```python
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    İstifadəçi /start yazdıqda çağırılır.
    """
    await update.message.reply_text(
        f"Salam, {update.effective_user.first_name}! "
        "Nə soruşmaq istəyirsən?"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    İstifadəçi adi mətn yazdıqda çağırılır.
    Mesajı alır, cavab verir.
    """
    gelen_metin = update.message.text
    await update.message.reply_text(
        f"Iyi oxumalar yawru, sualın olsa çəkinmə"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # /start komutuna handler bağla
    app.add_handler(CommandHandler("start", start))

    # Komut olmayan bütün mətnlərə handler bağla
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Botu başlat (polling rejimində)
    app.run_polling()


if __name__ == "__main__":
    main()
```

Bunu işlətmək üçün:

```bash
export BOT_TOKEN="5839201847:AAHjt2kX9..."
python bot.py
```

---

## Handler-lər necə işləyir?

Handler — "bu tip hadisə gəldikdə bu funksiyanı çağır" deyən bir qaydadır.

```python
app.add_handler(CommandHandler("start", start))
```

Bu sətir deyir: `/start` komutunu gördükdə `start` funksiyasını çağır.

```python
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
```

Bu sətir deyir: komut olmayan mətn gəldikdə `echo` funksiyasını çağır.

Handler növləri:

| Handler | Nə zaman işləyir |
|---------|-----------------|
| `CommandHandler("start", fn)` | `/start` yazıldıqda |
| `MessageHandler(filters.TEXT, fn)` | Mətn mesajı gəldikdə |
| `MessageHandler(filters.PHOTO, fn)` | Foto gəldikdə |
| `MessageHandler(filters.DOCUMENT, fn)` | Fayl gəldikdə |
| `CallbackQueryHandler(fn)` | Inline düymə basıldıqda |
| `ConversationHandler(...)` | Çox addımlı söhbət axını üçün |

---

## Komutlar əlavə etmək

```python
async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metn = (
        "📚 Mövcud komutlar:\n\n"
        "/start — Botu başlat\n"
        "/yardim — Bu mesajı göstər\n"
        "/haqqinda — Bot haqqında məlumat\n"
    )
    await update.message.reply_text(metn)


async def haqqinda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bu bot Qiyas tərəfindən hazırlanmışdır.\n"
        "Texniki suallar üçün @qiyas_cc"
    )


# main() içərisində:
app.add_handler(CommandHandler("yardim", yardim))
app.add_handler(CommandHandler("haqqinda", haqqinda))
```

BotFather-da komutların siyahısını da göstərmək olar. BotFather-a yaz:

```
/setcommands
```

Botu seç, sonra:

```
start - Botu başlat
yardim - Kömək mesajı
haqqinda - Bot haqqında
```

İndi Telegram-da `/` yazanda komutların siyahısı görünəcək.

---

## context.args — komut arqumentləri

```python
async def salam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # İstifadəçi "/salam Mecgec" yazdısa
    # context.args = ["Mecgec"]
    if context.args:
        ad = context.args[0]
        await update.message.reply_text(f"Salam, {ad}!")
    else:
        await update.message.reply_text("Kimə salam deyim? /salam <ad> yaz")
```

---

## Inline klaviatura (düymələr)

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    klaviatura = [
        [
            InlineKeyboardButton("📖 Dərs 1", callback_data="ders_1"),
            InlineKeyboardButton("📖 Dərs 2", callback_data="ders_2"),
        ],
        [InlineKeyboardButton("❓ Sual ver", callback_data="sual")],
    ]
    markup = InlineKeyboardMarkup(klaviatura)
    await update.message.reply_text("Nə etmək istəyirsən?", reply_markup=markup)


async def dugme_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorgu = update.callback_query
    await sorgu.answer()  # Telegram-a "aldım" de

    if sorgu.data == "ders_1":
        await sorgu.edit_message_text("Dərs 1 başladı! 📚")
    elif sorgu.data == "ders_2":
        await sorgu.edit_message_text("Dərs 2 başladı! 📚")
    elif sorgu.data == "sual":
        await sorgu.edit_message_text("Sualını yaz, cavablayacağam.")


# main() içərisində:
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CallbackQueryHandler(dugme_callback))
```

---

## Botdan mesaj göndərmək (proaktiv)

Bot yalnız cavab vermək məcburiyyətində deyil. Sən istədiyin anda botdan mesaj göndərə bilərsən — hadisə baş verdikdə, zamanlayıcı işə düşdükdə, webhook-dan gəldikdə:

```python
import asyncio
from telegram import Bot

async def bildiris_gonder():
    bot = Bot(token="5839201847:AAHjt2kX9...")
    await bot.send_message(
        chat_id=123456789,
        text="🔔 Sistem yeniləndi. Yeni dərs əlavə edildi!"
    )

asyncio.run(bildiris_gonder())
```

Django-dan, FastAPI-dan, cron job-dan — hər yerdən çağıra bilərsən.

---

## İstifadəçi haqqında məlumat almaq

```python
async def menim_melumatim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    metn = (
        f"👤 Adın: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📛 Username: @{user.username or 'yoxdur'}\n"
        f"💬 Chat ID: {chat.id}\n"
        f"📂 Chat növü: {chat.type}"
    )
    await update.message.reply_text(metn)
```

---

## Tam bot nümunəsi

Bu nümunə hər şeyi bir araya gətirir:

```python
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ["BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    klaviatura = [
        [InlineKeyboardButton("📋 Mövzular", callback_data="movzular")],
        [InlineKeyboardButton("❓ Sual ver", callback_data="sual")],
    ]
    markup = InlineKeyboardMarkup(klaviatura)
    await update.message.reply_text(
        f"Salam, {update.effective_user.first_name}! 👋\n"
        "Aşağıdan seç:",
        reply_markup=markup,
    )


async def dugme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "movzular":
        await q.edit_message_text(
            "📚 Mövcud mövzular:\n"
            "1. Server əsasları\n"
            "2. Mail server\n"
            "3. Telegram botu\n\n"
            "/start — Menüyə qayıt"
        )
    elif q.data == "sual":
        await q.edit_message_text("Sualını yaz, cavablayacağam. ✍️")


async def sual_cavab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gelen = update.message.text
    await update.message.reply_text(
        f"Sualın qeydə alındı: '{gelen}'\n"
        "Iyi oxumalar yawru, sualın olsa çəkinmə 📖"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(dugme))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sual_cavab))
    app.run_polling()


if __name__ == "__main__":
    main()
```

---

## Webhook qurulması (production)

Test bitdi, indi production-a keçirik. Webhook üçün public HTTPS URL lazımdır.

```python
import os
from contextlib import asynccontextmanager
from http import HTTPStatus
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # Məs: https://qiyas.cc/telegram/webhook

ptb = ApplicationBuilder().token(TOKEN).updater(None).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salam!")


ptb.add_handler(CommandHandler("start", start))


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ptb.bot.set_webhook(WEBHOOK_URL)
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/telegram/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb.bot)
    await ptb.process_update(update)
    return Response(status_code=HTTPStatus.OK)
```

Telegram hər yeni mesajı `POST https://qiyas.cc/telegram/webhook` ünvanına göndərəcək. FastAPI onu götürür, PTB ona verir, handler cavabı işlədir.

---

## Faydalı linklər

| | |
|---|---|
| 📖 Rəsmi Telegram Bot API sənədləri | https://core.telegram.org/bots/api |
| 🐍 python-telegram-bot GitHub | https://github.com/python-telegram-bot/python-telegram-bot |
| 📚 python-telegram-bot sənədləri | https://docs.python-telegram-bot.org |
| 💬 python-telegram-bot Telegram qrupu | https://t.me/pythontelegrambotgroup |
| 🔔 Bot API xəbərləri | https://t.me/BotNews |
| 🤖 BotFather | https://t.me/BotFather |

---

## Qısa yekun

Telegram botu mürəkkəb görünür, amma mexanizm sadədir:

1. BotFather-dan token alırsan
2. O token ilə Telegram API-ya HTTP sorğusu atırsan
3. Sorğu atırsan → mesaj gedir, foto gedir, düymə gedir
4. Telegram-dan update-lər alırsan (polling ilə özün soruşursan, webhook ilə Telegram sənə göndərir)
5. python-telegram-bot bütün bu HTTP işini sənin adından idarə edir — sən yalnız handler funksiyalarını yazırsan

Başlanğıc üçün polling ilə başla, lokal test et, işi gördükdən sonra webhook-a keçirsən, production-a çıxarırsan.
