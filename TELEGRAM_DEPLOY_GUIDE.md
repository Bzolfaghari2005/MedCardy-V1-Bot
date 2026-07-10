# راهنمای تلگرام MedCardy

> **مرجع اصلی دیپلوی:** برای راهنمای کامل ۰ تا ۱۰۰ (سرور، SSL، زیبال، systemd، امنیت و ...) فایل **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)** را ببینید.  
> این سند فقط بخش‌های **مختص تلگرام** را خلاصه می‌کند.

---

## نمای کلی

| بخش | نقش | دستور |
|-----|-----|-------|
| **Django** | پنل ادمین وب، callback زیبال، ارسال پیام تأیید پرداخت | `gunicorn` یا `runserver` |
| **ربات تلگرام** | منو، سفارش، کیف پول، پنل ادمین `/admin` | `python manage.py runbot` |

ربات در حالت **Polling** کار می‌کند — Webhook لازم نیست.

---

## ۱. BotFather

1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. توکن را در `.env` بگذارید:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_BOT_USERNAME=MedCardyBot
```

`TELEGRAM_BOT_USERNAME` باید **بدون @** باشد.

**دستورات پیشنهادی (`/setcommands`):**

```
start - شروع و منوی اصلی
admin - پنل ادمین (فقط ادمین‌ها)
```

| تنظیم | مقدار |
|-------|-------|
| `/setjoingroups` | Disable |
| `/setprivacy` | Enable |

---

## ۲. ادمین تلگرام (`ADMIN_TELEGRAM_IDS`)

### پیدا کردن شناسه عددی

به [@userinfobot](https://t.me/userinfobot) پیام `/start` بدهید و عدد `Id` را کپی کنید.

### تنظیم در `.env`

```env
ADMIN_TELEGRAM_IDS=123456789,987654321
```

بعد از تغییر، `runbot` را ری‌استارت کنید.

### قابلیت‌های `/admin`

- مشاهده سفارش‌های در انتظار بررسی
- تغییر وضعیت تولید / تحویل
- فعال/غیرفعال کردن **حالت تعمیر** (`maintenance_mode`)

وقتی سفارش جدیدی به `waiting_admin_review` برسد، اعلان خودکار به همه ادمین‌ها ارسال می‌شود.

---

## ۳. اجرای محلی (توسعه)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_initial_data
```

**ترمینال ۱:** `python manage.py runserver`  
**ترمینال ۲:** `python manage.py runbot`

خروجی موفق: `✅ Bot running: @MedCardyBot`

---

## ۴. اجرای پروداکشن

جزئیات کامل Nginx، SSL و systemd در **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)** — بخش‌های ۱۴ تا ۱۶.

خلاصه:

```bash
# روی سرور
gunicorn config.wsgi:application --bind 127.0.0.1:8000
python manage.py runbot   # در systemd جداگانه
```

**فقط یک** نمونه `runbot` همزمان — دو نمونه باعث `Conflict: terminated by other getUpdates request` می‌شود.

---

## ۵. لینک‌های بات

| نوع | آدرس |
|-----|------|
| عمومی | `https://t.me/MedCardyBot` |
| سفارش گروهی | `https://t.me/MedCardyBot?start=GXXXXXXXX` |

---

## ۶. عیب‌یابی سریع

| مشکل | راه‌حل |
|------|--------|
| `/start` جواب نمی‌دهد | `runbot` اجراست؟ توکن درست است؟ `maintenance_mode` خاموش است؟ |
| `/admin` باز نمی‌شود | `ADMIN_TELEGRAM_IDS` شامل شناسه عددی شماست؟ |
| Conflict getUpdates | دو `runbot` همزمان — یکی را متوقف کنید |
| پرداخت OK ولی پیام نمی‌رسد | Django هم روشن است؟ `TELEGRAM_BOT_TOKEN` در `.env` سرور درست است؟ |

جزئیات بیشتر: **[DEPLOY_GUIDE.md — عیب‌یابی](DEPLOY_GUIDE.md#۲۲-عیب‌یابی)**

---

## منابع

- [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) — راهنمای کامل دیپلوی
- [README.md](README.md) — فرایندهای ادمین و منوی بات
- [.env.example](.env.example) — متغیرهای محیطی
- `apps/telegram_bot/management/commands/runbot.py` — نقطه ورود ربات

---

*آخرین به‌روزرسانی: ژوئیه ۲۰۲۶*
