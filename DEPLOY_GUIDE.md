# راهنمای کامل دیپلوی MedCardy Bot (۰ تا ۱۰۰)

این سند **تنها مرجع** راه‌اندازی و انتشار پروژه MedCardy است — از نصب روی لپ‌تاپ (ویندوز/لینوکس) تا سرور پروداکشن، **پرداخت کارت‌به‌کارت**، درگاه زیبال، پنل ادمین تلگرام، و چک‌لیست نهایی.

> **مرجع‌های مرتبط:** [README.md](README.md) (توسعه و فرایندهای ادمین) · [DATABASE_GUIDE.md](DATABASE_GUIDE.md) (PostgreSQL روی ویندوز) · [.env.example](.env.example)

---

## فهرست

1. [معماری پروژه](#۱-معماری-پروژه)
2. [سرور چه چیزی لازم دارد؟](#۲-سرور-چه-چیزی-لازم-دارد)
3. [کال‌بک زیبال به کجا برود؟](#۳-کال‌بک-زیبال-به-کجا-برود)
4. [پیکربندی روش پرداخت (کارت‌به‌کارت vs زیبال)](#۴-پیکربندی-روش-پرداخت-کارتبهکارت-vs-زیبال)
5. [مرحله ۰ — پیش‌نیازها](#۵-مرحله-۰--پیش‌نیازها)
6. [مرحله ۱ — ساخت بات در تلگرام](#۶-مرحله-۱--ساخت-بات-در-تلگرام)
7. [مرحله ۲ — نصب پروژه (محلی)](#۷-مرحله-۲--نصب-پروژه-محلی)
8. [مرحله ۳ — پیکربندی `.env`](#۸-مرحله-۳--پیکربندی-env)
9. [مرحله ۴ — دیتابیس PostgreSQL](#۹-مرحله-۴--دیتابیس-postgresql)
10. [مرحله ۵ — راه‌اندازی اولیه Django و ربات](#۱۰-مرحله-۵--راهاندازی-اولیه-django-و-ربات)
11. [مرحله ۶ — پیکربندی ادمین تلگرام](#۱۱-مرحله-۶--پیکربندی-ادمین-تلگرام)
12. [مرحله ۷ — تست پرداخت (Sandbox و کارت‌به‌کارت)](#۱۲-مرحله-۷--تست-پرداخت-sandbox-و-کارتبهکارت)
13. [مرحله ۸ — خرید سرور و دامنه](#۱۳-مرحله-۸--خرید-سرور-و-دامنه)
14. [مرحله ۹ — آماده‌سازی سرور لینوکس](#۱۴-مرحله-۹--آمادهسازی-سرور-لینوکس)
15. [مرحله ۱۰ — دیپلوی روی سرور](#۱۵-مرحله-۱۰--دیپلوی-روی-سرور)
16. [مرحله ۱۱ — Nginx و SSL](#۱۶-مرحله-۱۱--nginx-و-ssl)
17. [مرحله ۱۲ — اجرای دائمی با systemd](#۱۷-مرحله-۱۲--اجرای-دائمی-با-systemd)
18. [مرحله ۱۳ — زیبال پروداکشن](#۱۸-مرحله-۱۳--زیبال-پروداکشن)
19. [مرحله ۱۴ — چک‌لیست انتشار](#۱۹-مرحله-۱۴--چکلیست-انتشار)
20. [فرایندهای ادمین بعد از دیپلوی](#۲۰-فرایندهای-ادمین-بعد-از-دیپلوی)
21. [پشتیبان‌گیری و به‌روزرسانی](#۲۱-پشتیبانگیری-و-بهروزرسانی)
22. [امنیت پروداکشن](#۲۲-امنیت-پروداکشن)
23. [عیب‌یابی](#۲۳-عیبیابی)
24. [خلاصه سریع](#۲۴-خلاصه-سریع)

---

## ۱. معماری پروژه

این پروژه **دو پروسه جدا** دارد که هر دو باید همزمان اجرا شوند:

```
┌──────────────────────────────────────────────────────────────────┐
│                          سرور شما                                 │
│                                                                   │
│  ┌─────────────────────┐       ┌─────────────────────────────┐  │
│  │ Django (Gunicorn)   │       │ ربات تلگرام (runbot)         │  │
│  │ پورت 8000 (داخلی)   │       │ Polling از Telegram API      │  │
│  │                     │       │                              │  │
│  │ • پنل ادمین وب      │       │ • منو و دکمه‌های کاربران     │  │
│  │ • Callback زیبال    │       │ • آپلود فایل سفارش          │  │
│  │ • اعلان پرداخت      │       │ • آپلود رسید کارت‌به‌کارت   │  │
│  │ • تأیید رسید (ادمین)│       │ • پنل ادمین تلگرام (/admin) │  │
│  └──────────┬──────────┘       └──────────────┬──────────────┘  │
│             │                                  │                  │
│             └──────────────┬───────────────────┘                  │
│                            ▼                                      │
│                   ┌─────────────────┐                             │
│                   │   PostgreSQL    │                             │
│                   └─────────────────┘                             │
│                            │                                      │
│                   ┌────────┴────────┐                             │
│                   │  media/         │  فایل سفارش، کاور، رسید   │
│                   │  • orders/files │  پرداخت                     │
│                   │  • payment_receipts/                        │
│                   └─────────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
          ▲ HTTPS                              ▲ Polling
          │                                    │
     ┌────┴────┐                          ┌────┴────┐
     │  زیبال  │                          │ تلگرام  │
     │ (پرداخت)│                          │  API    │
     └─────────┘                          └─────────┘
```

| بخش | نقش | دستور اجرا |
|-----|-----|------------|
| **Django** | پنل ادمین وب، دیتابیس، **callback پرداخت زیبال**، ارسال پیام تأیید پرداخت | `gunicorn` (پروداکشن) یا `runserver` (توسعه) |
| **ربات تلگرام** | دریافت پیام‌ها، سفارش، کیف پول، **آپلود رسید پرداخت**، **پنل ادمین تلگرام** | `python manage.py runbot` |
| **PostgreSQL** | کاربران، دوره‌ها، سفارش‌ها، پرداخت‌ها، تنظیمات | سرویس سیستمی |
| **Nginx** | HTTPS، سرو فایل‌های `static/` و `media/` | سرویس سیستمی |

> ربات در حالت **Polling** کار می‌کند — خودش مرتب از سرورهای تلگرام پیام می‌گیرد. برای MVP نیازی به Webhook تلگرام ندارید.

### دو روش پرداخت (قابل تعویض از ادمین)

| روش | تنظیم | نیاز به SSL/زیبال؟ | جریان |
|-----|-------|-------------------|--------|
| **کارت‌به‌کارت (پیش‌فرض)** | `enable_payment_gateway=false` | ❌ خیر — می‌توانید بدون دامنه هم شروع کنید | کاربر واریز می‌کند → رسید در بات → ادمین تأیید |
| **درگاه زیبال** | `enable_payment_gateway=true` | ✅ بله — HTTPS + callback | کاربر به درگاه می‌رود → callback به Django → تأیید خودکار |

> **توصیه MVP:** ابتدا با کارت‌به‌کارت راه بیندازید؛ بعد از آماده شدن دامنه و SSL، درگاه را فعال کنید.

### پشته فناوری

| فناوری | نسخه | کاربرد |
|--------|------|--------|
| Python | 3.11+ | اجرای Django و ربات |
| Django | 5.0.6 | بک‌اند، ادمین، callback |
| PostgreSQL | 14+ (۱۶ توصیه می‌شود) | دیتابیس |
| Aiogram | 3.7 | ربات تلگرام |
| Gunicorn | آخرین | اجرای Django در پروداکشن |
| Nginx + Certbot | — | HTTPS و reverse proxy |
| Zibal IPG | — | درگاه پرداخت |

---

## ۲. سرور چه چیزی لازم دارد؟

### حداقل مشخصات VPS (برای شروع / MVP)

| مورد | حداقل پیشنهادی | توضیح |
|------|----------------|-------|
| **سیستم‌عامل** | Ubuntu 22.04 LTS | لینوکس پایدار؛ ویندوز فقط برای توسعه محلی |
| **CPU** | ۱ vCPU | کافی برای MVP با ترافیک کم |
| **RAM** | ۱ GB | ۲ GB راحت‌تر است (PostgreSQL + Django + Bot) |
| **دیسک** | ۲۰ GB SSD | فایل‌های آپلودشده در `media/orders/files/` ذخیره می‌شوند |
| **پهنای باند** | نامحدود یا ۱ TB/ماه | معمولاً در VPSهای ایرانی/خارجی کافی است |

### نرم‌افزارهای لازم روی سرور

| نرم‌افزار | نسخه | چرا لازم است |
|-----------|------|--------------|
| **Python** | 3.11+ | اجرای Django و ربات |
| **PostgreSQL** | 14+ | دیتابیس اصلی |
| **Nginx** | آخرین نسخه پایدار | Reverse proxy + SSL + سرو media |
| **Gunicorn** | آخرین | اجرای Django در پروداکشن |
| **Certbot** | — | گواهی SSL رایگان (Let's Encrypt) |
| **Git** | — | دریافت کد از ریپازیتوری |

### چیزهایی که **حتماً** باید داشته باشید

| مورد | الزامی؟ | دلیل |
|------|---------|------|
| **دامنه** (مثلاً `medcardy.ir`) | ⚠️ برای زیبال بله | callback زیبال بدون دامنه عمومی کار نمی‌کند؛ **کارت‌به‌کارت بدون دامنه هم ممکن است** |
| **SSL / HTTPS** | ⚠️ برای زیبال بله | زیبال فقط به آدرس HTTPS callback می‌زند؛ کارت‌به‌کارت نیازی ندارد |
| **IP عمومی (Public IP)** | ✅ بله | سرور باید از اینترنت قابل دسترسی باشد |
| **توکن بات تلگرام** | ✅ بله | از BotFather |
| **حساب مرچنت زیبال** | ⚠️ فقط برای درگاه آنلاین | در حالت کارت‌به‌کارت لازم نیست؛ تست زیبال با `zibal` |
| **ADMIN_TELEGRAM_IDS** | ✅ توصیه‌شده | پنل ادمین تلگرام و اعلان سفارش‌های جدید |

### ارائه‌دهندگان VPS پیشنهادی

- **ایران:** ابر آروان، پارس‌پک، لیارا (سرور ابری)
- **خارج:** Hetzner، DigitalOcean

> **نکته:** اگر فقط می‌خواهید روی لپ‌تاپ تست کنید (بدون پرداخت واقعی)، سرور لازم نیست — فقط `runserver` + `runbot` کافی است.

---

## ۳. کال‌بک زیبال به کجا برود؟

### پاسخ کوتاه

```
https://YOUR-DOMAIN.com/api/payments/zibal/callback/
```

`YOUR-DOMAIN.com` را با دامنه واقعی خود جایگزین کنید.

### جزئیات فنی

| مورد | مقدار |
|------|-------|
| **مسیر (Path)** | `/api/payments/zibal/callback/` |
| **متد HTTP** | `GET` |
| **پروتکل** | فقط `HTTPS` (در پروداکشن) |
| **CSRF** | غیرفعال برای این endpoint (زیبال redirect می‌زند) |
| **پروسه‌ای که جواب می‌دهد** | **Django** (نه ربات تلگرام) |
| **فایل view** | `apps/payments/views.py` → `ZibalCallbackView` |
| **URL config** | `config/urls.py` → `api/payments/` → `apps/payments/urls.py` |

### این آدرس را در **سه جا** تنظیم کنید

**۱. فایل `.env` روی سرور:**

```env
ZIBAL_CALLBACK_URL=https://medcardy.ir/api/payments/zibal/callback/
SITE_BASE_URL=https://medcardy.ir
```

**۲. داشبورد زیبال** (اگر فیلد Callback URL دارد):

همان آدرس بالا را در پنل مرچنت زیبال ثبت کنید.

**۳. Nginx** — فقط مطمئن شوید ترافیک HTTPS به Django می‌رسد:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

> نیازی به `location` جدا برای callback نیست — همان proxy عمومی کافی است.

### جریان کامل پرداخت

```
کاربر در بات «پرداخت» می‌زند
        ↓
ربات → Payment در DB می‌سازد
        ↓
Django → API زیبال POST /v1/request
        ↓
زیبال → trackId برمی‌گرداند
        ↓
کاربر → https://gateway.zibal.ir/start/{trackId} (صفحه پرداخت)
        ↓
بعد از پرداخت، زیبال کاربر را redirect می‌کند به:
        ↓
GET https://medcardy.ir/api/payments/zibal/callback/?trackId=...&success=1
        ↓
Django → API زیبال POST /v1/verify
        ↓
اگر موفق (result=100 یا 201) → خرید/کیف‌پول/سفارش فعال
        ↓
Django → پیام تأیید از طریق Telegram Bot API به کاربر
        ↓
صفحه HTML موفقیت/شکست به کاربر نمایش داده می‌شود
```

### قانون مبلغ

- قیمت‌ها در DB به **تومان** ذخیره می‌شوند
- قبل از ارسال به زیبال × ۱۰ می‌شود (تبدیل به **ریال**)

### تست محلی callback (بدون سرور)

برای تست روی لپ‌تاپ از **ngrok** استفاده کنید:

```bash
# ترمینال ۱
python manage.py runserver

# ترمینال ۲
ngrok http 8000
```

آدرسی که ngrok می‌دهد (مثلاً `https://abc123.ngrok-free.app`) را در `.env` بگذارید:

```env
SITE_BASE_URL=https://abc123.ngrok-free.app
ZIBAL_CALLBACK_URL=https://abc123.ngrok-free.app/api/payments/zibal/callback/
ZIBAL_TEST_MODE=True
ZIBAL_MERCHANT=zibal
```

---

## ۴. پیکربندی روش پرداخت (کارت‌به‌کارت vs زیبال)

این تنظیمات در **Django Admin → تنظیمات** (`apps/settings_app`) ذخیره می‌شوند — نه در `.env`. بعد از `seed_initial_data` از پنل ادمین وب ویرایش کنید.

### حالت ۱ — کارت‌به‌کارت (پیش‌فرض، بدون نیاز به زیبال)

مناسب برای **شروع سریع** یا وقتی هنوز دامنه/SSL/مرچنت زیبال ندارید.

| کلید تنظیم | مقدار پیشنهادی | توضیح |
|------------|----------------|-------|
| `enable_payment_gateway` | `false` | درگاه آنلاین خاموش |
| `payment_card_number` | `6037xxxxxxxxxxxx` | شماره کارت مقصد (۱۶ رقم) |
| `payment_card_holder` | نام صاحب حساب | در پیام بات نمایش داده می‌شود |
| `payment_bank_name` | مثلاً `ملی` | نام بانک |
| `payment_sheba_number` | `IR...` (اختیاری) | شماره شبا |
| `payment_transfer_note` | متن هشدار | مثلاً «کد پرداخت را در توضیحات واریز بنویسید» |
| `payment_review_hours` | `24` | در پیام «رسید دریافت شد» به کاربر نشان داده می‌شود |

**جریان کاربر:**

```
انتخاب محصول → کد پرداخت (MCP-YYMMDD-0001) + شماره کارت
        ↓
واریز کارت‌به‌کارت
        ↓
دکمه «📸 ارسال رسید پرداخت» → آپلود عکس/PDF
        ↓
وضعیت: receipt_submitted
        ↓
اعلان خودکار به ADMIN_TELEGRAM_IDS
        ↓
ادمین در /admin → «پرداخت‌های در انتظار تأیید» → تأیید یا رد
        ↓
خرید/سفارش/کیف‌پول فعال + پیام به کاربر
```

**فایل رسید** در `media/payment_receipts/YYYY/MM/` ذخیره می‌شود — روی سرور باید `www-data` دسترسی نوشتن داشته باشد.

### حالت ۲ — درگاه آنلاین زیبال

وقتی دامنه، SSL و مرچنت زیبال آماده است:

| کلید تنظیم | مقدار |
|------------|-------|
| `enable_payment_gateway` | `true` |

همچنین در `.env` سرور:

```env
ZIBAL_MERCHANT=شناسه-مرچنت-واقعی
ZIBAL_TEST_MODE=False
ZIBAL_CALLBACK_URL=https://yourdomain.com/api/payments/zibal/callback/
SITE_BASE_URL=https://yourdomain.com
```

جزئیات callback در [بخش ۳](#۳-کال‌بک-زیبال-به-کجا-برود) آمده است.

### تأیید رسید توسط ادمین

| محل | روش |
|-----|-----|
| **بات تلگرام** | `/admin` → «💳 پرداخت‌های در انتظار تأیید» → تأیید / رد |
| **پنل وب** | Django Admin → Payments → action «Approve receipt» / «Reject receipt» |

پیام‌های مرتبط با پرداخت (`manual_payment_instructions`, `receipt_received`, ...) از **Django Admin → پیام‌های بات** قابل ویرایش هستند.

---

## ۵. مرحله ۰ — پیش‌نیازها

### روی لپ‌تاپ (توسعه)

| مورد | ویندوز | لینوکس/مک |
|------|--------|-----------|
| Python | 3.11+ از [python.org](https://python.org) یا `winget install Python.Python.3.11` | `sudo apt install python3.11 python3.11-venv` |
| PostgreSQL | 14+ — راهنمای کامل: [DATABASE_GUIDE.md](DATABASE_GUIDE.md) | `sudo apt install postgresql` |
| Git | `winget install Git.Git` | `sudo apt install git` |
| اکانت تلگرام | برای BotFather و تست بات | همان |

### روی سرور (پروداکشن)

- VPS با Ubuntu 22.04 LTS
- دامنه متصل به IP سرور (رکورد A)
- دسترسی SSH به سرور
- (اختیاری) کاربر deploy جدا از root

---

## ۶. مرحله ۱ — ساخت بات در تلگرام

### ۶.۱ ساخت بات

1. به [@BotFather](https://t.me/BotFather) بروید.
2. `/newbot` بزنید.
3. **نام نمایشی:** `MedCardy`
4. **یوزرنیم:** مثلاً `MedCardyBot` (باید به `bot` ختم شود)
5. توکن را کپی کنید:

```
7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### ۶.۲ تنظیمات BotFather

| دستور | مقدار پیشنهادی |
|-------|----------------|
| `/setdescription` | پلتفرم آموزش پزشکی MedCardy — تبدیل جزوه به پادکست |
| `/setabouttext` | دوره‌های پزشکی، سفارش پادکست، کیف پول و پشتیبانی |
| `/setuserpic` | لوگوی MedCardy |
| `/setcommands` | لیست دستورات (پایین) |
| `/setjoingroups` | Disable |
| `/setprivacy` | Enable |

**لیست دستورات برای `/setcommands`:**

```
start - شروع و منوی اصلی
admin - پنل ادمین (فقط برای ادمین‌ها)
```

> بقیه تعامل‌ها از طریق دکمه‌های منو انجام می‌شود.

---

## ۷. مرحله ۲ — نصب پروژه (محلی)

```bash
# کلون پروژه
git clone <آدرس-ریپازیتوری> medcardy
cd medcardy

# محیط مجازی
python -m venv venv
```

**فعال‌سازی محیط مجازی:**

```powershell
# ویندوز (PowerShell)
venv\Scripts\activate
```

```bash
# لینوکس/مک
source venv/bin/activate
```

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# برای تست پروداکشن محلی (اختیاری)
pip install gunicorn
```

### وابستگی‌های پروژه (`requirements.txt`)

| پکیج | کاربرد |
|------|--------|
| Django 5.0.6 | بک‌اند و ادمین |
| psycopg2-binary | اتصال PostgreSQL |
| aiogram 3.7 | ربات تلگرام |
| python-decouple | خواندن `.env` |
| requests | API زیبال و ارسال پیام تلگرام از Django |
| aiohttp | درخواست‌های async ربات |
| Pillow | تصاویر کاور دوره |
| pypdf | آنالیز تعداد صفحات PDF |
| python-docx | آنالیز فایل Word |
| python-slugify | اسلاگ‌سازی |

---

## ۸. مرحله ۳ — پیکربندی `.env`

```bash
cp .env.example .env
```

### تمام متغیرهای `.env` — توضیح کامل

```env
# ─── Django ───────────────────────────────────────────
DEBUG=True
# در پروداکشن: False

SECRET_KEY=یک-رشته-تصادفی-خیلی-بلند-حداقل-۵۰-کاراکتر
# تولید: python -c "import secrets; print(secrets.token_urlsafe(50))"

ALLOWED_HOSTS=localhost,127.0.0.1
# در پروداکشن: medcardy.ir,www.medcardy.ir
# ⚠️ پیش‌فرض کد: * — در پروداکشن حتماً دامنه واقعی بگذارید

# ─── دیتابیس ─────────────────────────────────────────
DATABASE_URL=postgres://medcardy_user:YOUR_PASSWORD@localhost:5432/medcardy

# ─── تلگرام ──────────────────────────────────────────
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_BOT_USERNAME=MedCardyBot
# بدون @ — برای deep link سفارش گروهی و صفحه callback

# ─── سایت ────────────────────────────────────────────
SITE_BASE_URL=https://medcardy.ir
# در توسعه محلی: http://localhost:8000

# ─── زیبال ───────────────────────────────────────────
ZIBAL_BASE_URL=https://gateway.zibal.ir
ZIBAL_MERCHANT=zibal
# پروداکشن: شناسه مرچنت واقعی از پنل زیبال

ZIBAL_CALLBACK_URL=https://medcardy.ir/api/payments/zibal/callback/
# ⚠️ حتماً HTTPS و با / در انتها

ZIBAL_TEST_MODE=True
# پروداکشن: False

# ─── پشتیبانی ────────────────────────────────────────
DEFAULT_SUPPORT_USERNAME=@MedCardySupport

# ─── ادمین تلگرام ────────────────────────────────────
ADMIN_TELEGRAM_IDS=123456789,987654321
# شناسه عددی تلگرام ادمین‌ها (بدون @، با کاما جدا)
# برای پنل /admin و اعلان سفارش‌های جدید
```

### جدول مقادیر: توسعه vs پروداکشن

| متغیر | توسعه (لپ‌تاپ) | پروداکشن (سرور) |
|-------|----------------|-----------------|
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `yourdomain.com,www.yourdomain.com` |
| `SITE_BASE_URL` | `http://localhost:8000` | `https://yourdomain.com` |
| `ZIBAL_TEST_MODE` | `True` | `False` |
| `ZIBAL_MERCHANT` | `zibal` | شناسه واقعی |
| `ZIBAL_CALLBACK_URL` | ngrok یا localhost | `https://domain/api/payments/zibal/callback/` |
| `ADMIN_TELEGRAM_IDS` | شناسه خودتان | شناسه همه ادمین‌ها |

> **تنظیمات پرداخت** (شماره کارت، فعال/غیرفعال بودن درگاه) در Django Admin → **تنظیمات** است — نه در `.env`.

---

## ۹. مرحله ۴ — دیتابیس PostgreSQL

### ویندوز (توسعه محلی)

راهنمای کامل: **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)**

**روش سریع با اسکریپت پروژه:**

```powershell
.\scripts\database\psql.ps1 -File scripts\database\setup_medcardy.sql
```

سپس در `.env`:

```env
DATABASE_URL=postgres://medcardy_user:medcardymedcardy20252025@localhost:5432/medcardy
```

> برای توسعه سریع می‌توانید از کاربر `postgres` هم استفاده کنید — جزئیات در DATABASE_GUIDE.

### لینوکس / سرور

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib

sudo -u postgres psql
```

```sql
CREATE DATABASE medcardy;
CREATE USER medcardy_user WITH PASSWORD 'یک-رمز-قوی';
ALTER DATABASE medcardy OWNER TO medcardy_user;
GRANT ALL PRIVILEGES ON DATABASE medcardy TO medcardy_user;
\c medcardy
GRANT ALL ON SCHEMA public TO medcardy_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO medcardy_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO medcardy_user;
\q
```

> **PostgreSQL 15+:** اگر خطای permission روی `public` schema دیدید، دستورات `GRANT` بالا را حتماً بعد از `\c medcardy` اجرا کنید.

سپس در `.env`:

```env
DATABASE_URL=postgres://medcardy_user:یک-رمز-قوی@localhost:5432/medcardy
```

---

## ۱۰. مرحله ۵ — راه‌اندازی اولیه Django و ربات

```bash
# مایگریشن
python manage.py migrate

# سوپریوزر (برای پنل ادمین وب)
python manage.py createsuperuser

# داده‌های اولیه (دسته‌بندی‌ها، پیام‌های بات، دوره‌های نمونه، تنظیمات)
python manage.py seed_initial_data
```

`seed_initial_data` موارد زیر را ایجاد می‌کند:
- تنظیمات پیش‌فرض (قیمت‌گذاری، فلگ‌ها، حالت تعمیر، **پرداخت کارت‌به‌کارت**)
- تمام پیام‌های بات (قابل ویرایش از ادمین)
- ۸ دسته‌بندی پیش‌فرض
- بیش از ۳۰ درس
- ۲ دوره نمونه (۱ رایگان، ۱ پولی)

> بعد از seed، حتماً در **Django Admin → تنظیمات** شماره کارت (`payment_card_number`) را پر کنید.

### اجرای دو پروسه (توسعه)

**ترمینال ۱ — Django:**

```bash
python manage.py runserver
```

پنل ادمین: http://localhost:8000/admin/

**ترمینال ۲ — ربات:**

```bash
python manage.py runbot
```

خروجی موفق:

```
✅ Bot running: @MedCardyBot
```

در تلگرام `/start` بزنید — باید منوی اصلی نمایش داده شود.

---

## ۱۱. مرحله ۶ — پیکربندی ادمین تلگرام

### ۱۱.۱ پیدا کردن شناسه عددی تلگرام (Telegram User ID)

یکی از این روش‌ها:

1. به [@userinfobot](https://t.me/userinfobot) پیام `/start` بدهید — عدد `Id` را کپی کنید.
2. یا از [@getidsbot](https://t.me/getidsbot) استفاده کنید.

### ۱۱.۲ تنظیم در `.env`

```env
ADMIN_TELEGRAM_IDS=123456789,987654321
```

- فقط **اعداد** — بدون `@`
- چند ادمین با **کاما** جدا می‌شوند
- بعد از تغییر `.env`، `runbot` را ری‌استارت کنید

### ۱۱.۳ قابلیت‌های پنل ادمین تلگرام

با دستور `/admin` (فقط برای IDهای مجاز):

| قابلیت | توضیح |
|--------|-------|
| **پرداخت‌های در انتظار تأیید** | رسیدهای کارت‌به‌کارت با وضعیت `receipt_submitted` — تأیید یا رد |
| سفارش‌های در انتظار بررسی | لیست سفارش‌های `waiting_admin_review` |
| تغییر وضعیت تولید | `in_production` → `delivered` |
| حالت تعمیر | فعال/غیرفعال `maintenance_mode` از داخل بات |

وقتی **رسید پرداخت** یا **سفارش جدید** به حالت بررسی برسد، **اعلان خودکار** به همه `ADMIN_TELEGRAM_IDS` ارسال می‌شود (همراه با تصویر رسید در صورت وجود).

> ادمین‌ها در حالت تعمیر همچنان به بات دسترسی دارند.

---

## ۱۲. مرحله ۷ — تست پرداخت (Sandbox و کارت‌به‌کارت)

### ۱۲.۱ تست کارت‌به‌کارت (بدون زیبال)

1. در Django Admin → تنظیمات:
   - `enable_payment_gateway` = `false`
   - `payment_card_number` و `payment_card_holder` را پر کنید
2. `runserver` + `runbot` را اجرا کنید
3. در بات یک خرید/شارژ کیف پول تست کنید
4. رسید (عکس) ارسال کنید
5. با `/admin` → «پرداخت‌های در انتظار تأیید» → تأیید کنید
6. باید پیام تأیید به کاربر برسد و خرید/سفارش فعال شود

### ۱۲.۲ تست درگاه زیبال (Sandbox)

در Django Admin → تنظیمات: `enable_payment_gateway` = `true`

```env
ZIBAL_TEST_MODE=True
ZIBAL_MERCHANT=zibal
```

در حالت تست، کد به‌صورت خودکار `merchant=zibal` استفاده می‌کند (نیازی به whitelist IP نیست).

### ۱۲.۳ تست callback با ngrok

1. `runserver` را اجرا کنید
2. `ngrok http 8000` را در ترمینال دیگر اجرا کنید
3. آدرس ngrok را در `ZIBAL_CALLBACK_URL` و `SITE_BASE_URL` بگذارید
4. `runbot` را اجرا کنید
5. در بات یک خرید تست انجام دهید
6. بعد از پرداخت باید:
   - صفحه HTML موفقیت در مرورگر نمایش داده شود
   - پیام تأیید در تلگرام برسد

---

## ۱۳. مرحله ۸ — خرید سرور و دامنه

> **نکته:** اگر فقط از **پرداخت کارت‌به‌کارت** استفاده می‌کنید، می‌توانید ابتدا با IP سرور و بدون دامنه شروع کنید. برای **زیبال** دامنه و SSL الزامی است.

### DNS

در پنل دامنه، رکورد **A** بسازید:

```
نوع: A
نام: @
مقدار: IP-سرور-شما
TTL: 3600
```

برای `www`:

```
نوع: A (یا CNAME به @)
نام: www
مقدار: IP-سرور-شما
```

### بررسی اتصال

```bash
ping medcardy.ir
ssh root@IP-سرور-شما
```

---

## ۱۴. مرحله ۹ — آماده‌سازی سرور لینوکس

اتصال SSH و نصب پکیج‌ها:

```bash
ssh root@YOUR_SERVER_IP

# به‌روزرسانی
apt update && apt upgrade -y

# پکیج‌های پایه
apt install -y git ufw nginx certbot python3-certbot-nginx \
  postgresql postgresql-contrib \
  build-essential libpq-dev
```

### نصب Python 3.11+ (الزامی)

Ubuntu 22.04 به‌طور پیش‌فرض Python 3.10 دارد؛ پروژه به **3.11+** نیاز دارد:

```bash
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev

# بررسی نسخه
python3.11 --version
```

> **Ubuntu 24.04 LTS:** Python 3.12 از قبل نصب است — می‌توانید `python3.12 -m venv venv` استفاده کنید.

### فایروال

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status
```

### ساخت کاربر deploy (اختیاری ولی امن‌تر)

```bash
adduser medcardy
usermod -aG sudo medcardy
su - medcardy
```

---

## ۱۵. مرحله ۱۰ — دیپلوی روی سرور

مسیر پیشنهادی پروژه: `/var/www/medcardy`

```bash
# دریافت کد
sudo mkdir -p /var/www/medcardy
sudo chown $USER:$USER /var/www/medcardy
git clone <آدرس-ریپازیتوری> /var/www/medcardy
cd /var/www/medcardy

# محیط مجازی (Python 3.11)
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# فایل .env (دستی بسازید — هرگز در git نگذارید)
nano .env
```

محتوای `.env` پروداکشن (نمونه):

```env
DEBUG=False
SECRET_KEY=تولید-با-secrets-token-urlsafe
ALLOWED_HOSTS=medcardy.ir,www.medcardy.ir

DATABASE_URL=postgres://medcardy_user:رمز-قوی@localhost:5432/medcardy

TELEGRAM_BOT_TOKEN=توکن-واقعی
TELEGRAM_BOT_USERNAME=MedCardyBot

SITE_BASE_URL=https://medcardy.ir

ZIBAL_BASE_URL=https://gateway.zibal.ir
ZIBAL_MERCHANT=شناسه-مرچنت-واقعی
ZIBAL_CALLBACK_URL=https://medcardy.ir/api/payments/zibal/callback/
ZIBAL_TEST_MODE=False

DEFAULT_SUPPORT_USERNAME=@MedCardySupport
ADMIN_TELEGRAM_IDS=123456789
```

```bash
# مایگریشن و استاتیک
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_initial_data   # فقط بار اول

# پوشه‌های media (فایل سفارش، کاور دوره، رسید پرداخت)
mkdir -p media/orders/files media/courses/covers media/payment_receipts
chmod -R 755 media
```

### پیکربندی پرداخت بعد از seed

1. وارد `https://yourdomain.com/admin/` شوید (یا موقتاً `http://IP:8000/admin/` قبل از SSL)
2. **تنظیمات** → `payment_card_number`, `payment_card_holder`, `payment_bank_name` را پر کنید
3. برای شروع MVP: `enable_payment_gateway` = `false` (کارت‌به‌کارت)
4. وقتی زیبال آماده شد: `enable_payment_gateway` = `true` + تنظیمات `.env` زیبال

### تست موقت Gunicorn

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

اگر `curl http://127.0.0.1:8000/admin/` پاسخ داد، آماده Nginx هستید.

---

## ۱۶. مرحله ۱۱ — Nginx و SSL

> اگر فعلاً فقط کارت‌به‌کارت دارید و دامنه ندارید، می‌توانید موقتاً Gunicorn را روی پورت داخلی نگه دارید و فقط systemd را فعال کنید. برای دسترسی عمومی به ادمین وب یا زیبال، Nginx + SSL لازم است.

### مرحله ۱ — Nginx اولیه (فقط HTTP برای دریافت SSL)

```bash
sudo nano /etc/nginx/sites-available/medcardy
```

```nginx
server {
    listen 80;
    server_name medcardy.ir www.medcardy.ir;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/medcardy /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### مرحله ۲ — دریافت گواهی SSL

```bash
sudo certbot --nginx -d medcardy.ir -d www.medcardy.ir
```

Certbot به‌صورت خودکار بلوک HTTPS اضافه می‌کند. سپس فایل Nginx را برای static/media تکمیل کنید:

### مرحله ۳ — پیکربندی نهایی Nginx

```bash
sudo nano /etc/nginx/sites-available/medcardy
```

```nginx
server {
    listen 80;
    server_name medcardy.ir www.medcardy.ir;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name medcardy.ir www.medcardy.ir;

    ssl_certificate     /etc/letsencrypt/live/medcardy.ir/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/medcardy.ir/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/medcardy/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/medcardy/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

> `client_max_body_size 50M` برای آپلود فایل‌های سفارش (PDF/Word) و **رسید پرداخت** از طریق بات لازم است.

### تست دسترسی

- پنل ادمین: `https://medcardy.ir/admin/`
- callback:

```bash
curl -I "https://medcardy.ir/api/payments/zibal/callback/"
```

باید `HTTP/2 200` برگرداند (صفحه HTML موفقیت/شکست).

---

## ۱۷. مرحله ۱۲ — اجرای دائمی با systemd

### سرویس Django (Gunicorn)

```bash
sudo nano /etc/systemd/system/medcardy-web.service
```

```ini
[Unit]
Description=MedCardy Django (Gunicorn)
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/medcardy
Environment="PATH=/var/www/medcardy/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
ExecStart=/var/www/medcardy/venv/bin/gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **نکته:** پروژه از `python-decouple` برای خواندن `.env` از `WorkingDirectory` استفاده می‌کند — فایل `.env` باید در `/var/www/medcardy/.env` باشد.

### سرویس ربات تلگرام

```bash
sudo nano /etc/systemd/system/medcardy-bot.service
```

```ini
[Unit]
Description=MedCardy Telegram Bot (Polling)
After=network.target medcardy-web.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/medcardy
Environment="PATH=/var/www/medcardy/venv/bin"
ExecStart=/var/www/medcardy/venv/bin/python manage.py runbot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> تعداد worker: معمولاً `(2 × CPU) + 1` — برای ۱ vCPU، ۳ worker مناسب است.

### دسترسی فایل‌ها به www-data

```bash
sudo chown -R www-data:www-data /var/www/medcardy/media
sudo chown -R www-data:www-data /var/www/medcardy/staticfiles
sudo chown -R www-data:www-data /var/www/medcardy/venv
sudo chmod 600 /var/www/medcardy/.env
sudo chown www-data:www-data /var/www/medcardy/.env
# دسترسی خواندن/نوشتن کد و media برای سرویس‌ها
sudo chown -R www-data:www-data /var/www/medcardy
```

> پوشه `media/payment_receipts/` باید برای آپلود رسید از ربات قابل نوشتن باشد.

### فعال‌سازی

```bash
sudo systemctl daemon-reload
sudo systemctl enable medcardy-web medcardy-bot
sudo systemctl start medcardy-web medcardy-bot

# بررسی وضعیت
sudo systemctl status medcardy-web
sudo systemctl status medcardy-bot

# لاگ زنده ربات
sudo journalctl -u medcardy-bot -f

# لاگ Django
sudo journalctl -u medcardy-web -f
```

---

## ۱۸. مرحله ۱۳ — زیبال پروداکشن

> **فقط اگر** `enable_payment_gateway=true` در تنظیمات ادمین فعال کرده‌اید.

### مراحل ثبت‌نام

1. به [zibal.ir](https://zibal.ir) بروید و ثبت‌نام کنید
2. احراز هویت و دریافت **شناسه مرچنت** (merchant ID)
3. در Django Admin → تنظیمات: `enable_payment_gateway` = `true`
4. در `.env` سرور:

```env
ZIBAL_MERCHANT=xxxxxxxxxxxx
ZIBAL_TEST_MODE=False
ZIBAL_CALLBACK_URL=https://medcardy.ir/api/payments/zibal/callback/
```

4. در داشبورد زیبال، آدرس callback را ثبت کنید (اگر فیلد جدا دارد)
5. سرویس‌ها را ری‌استارت کنید:

```bash
sudo systemctl restart medcardy-web medcardy-bot
```

6. یک پرداخت واقعی کوچک تست کنید

### نکات مهم زیبال

| نکته | توضیح |
|------|-------|
| HTTPS الزامی | callback بدون SSL کار نمی‌کند |
| `/` در انتهای URL | `.../callback/` — با اسلش تمام شود |
| Django باید روشن باشد | فقط ربات کافی نیست — callback به Django می‌خورد |
| `TELEGRAM_BOT_TOKEN` | Django برای ارسال پیام تأیید بعد از پرداخت به آن نیاز دارد |
| IP Whitelist | در حالت تست (`zibal`) لازم نیست؛ در پروداکشن طبق راهنمای زیبال |
| کدهای موفق verify | `result=100` (تأیید اول) یا `201` (قبلاً تأیید شده) |

---

## ۱۹. مرحله ۱۴ — چک‌لیست انتشار

### زیرساخت

- [ ] سرور Ubuntu (22.04 یا 24.04) با IP عمومی
- [ ] Python 3.11+ نصب شده (`python3.11 --version`)
- [ ] دامنه به IP اشاره می‌کند (برای زیبال؛ برای کارت‌به‌کارت اختیاری)
- [ ] SSL فعال (`https://` کار می‌کند) — برای زیبال الزامی
- [ ] PostgreSQL نصب و دیتابیس ساخته شده
- [ ] فایروال: پورت 22, 80, 443 باز
- [ ] پوشه‌های `media/orders/files/` و `media/payment_receipts/` با دسترسی نوشتن برای `www-data`

### پیکربندی

- [ ] `.env` پروداکشن روی سرور (نه در git)
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` قوی و یکتا
- [ ] `ALLOWED_HOSTS` شامل دامنه واقعی (نه `*`)
- [ ] `TELEGRAM_BOT_TOKEN` صحیح
- [ ] `TELEGRAM_BOT_USERNAME` بدون @ و مطابق BotFather
- [ ] `ADMIN_TELEGRAM_IDS` با شناسه‌های واقعی ادمین‌ها
- [ ] **تنظیمات پرداخت:** `payment_card_number` و `payment_card_holder` پر شده
- [ ] `enable_payment_gateway` مطابق استراتژی شما (`false` = کارت‌به‌کارت، `true` = زیبال)
- [ ] (اگر زیبال) `ZIBAL_CALLBACK_URL=https://domain/api/payments/zibal/callback/`
- [ ] (اگر زیبال) `SITE_BASE_URL=https://domain` و `ZIBAL_TEST_MODE=False`
- [ ] `DEFAULT_SUPPORT_USERNAME` به اکانت واقعی اشاره دارد

### سرویس‌ها

- [ ] `medcardy-web` (Gunicorn) active است
- [ ] `medcardy-bot` (runbot) active است
- [ ] **فقط یک** نمونه `runbot` در حال اجراست
- [ ] `migrate` و `seed_initial_data` اجرا شده
- [ ] `collectstatic` اجرا شده

### تست عملکرد

- [ ] `/start` در تلگرام منوی اصلی را نشان می‌دهد
- [ ] `/admin` برای ادمین‌ها پنل را باز می‌کند (شامل «پرداخت‌های در انتظار تأیید»)
- [ ] `https://domain/admin/` باز می‌شود
- [ ] (کارت‌به‌کارت) آپلود رسید + تأیید ادمین + فعال شدن خرید
- [ ] (زیبال) `curl -I https://domain/api/payments/zibal/callback/` → 200
- [ ] (زیبال) پرداخت تست موفق + پیام تأیید در تلگرام
- [ ] آپلود فایل سفارش در بات کار می‌کند
- [ ] اعلان سفارش/رسید جدید به ادمین‌ها می‌رسد

### انتشار

- [ ] لینک بات: `https://t.me/MedCardyBot`
- [ ] پیام خوش‌آمد از ادمین ویرایش شده
- [ ] دوره‌ها و قیمت‌ها در ادمین تنظیم شده
- [ ] `maintenance_mode=false` در تنظیمات

---

## ۲۰. فرایندهای ادمین بعد از دیپلوی

### تأیید پرداخت کارت‌به‌کارت

1. کاربر رسید را در بات ارسال می‌کند → `Payment.status=receipt_submitted`
2. اعلان (با تصویر رسید) به `ADMIN_TELEGRAM_IDS` می‌رسد
3. `/admin` → «💳 پرداخت‌های در انتظار تأیید» → جزئیات → **تأیید** یا **رد**
4. با تأیید: خرید دوره / سفارش / شارژ کیف پول به‌صورت خودکار فعال می‌شود
5. با رد: کاربر پیام رد دریافت می‌کند و می‌تواند رسید جدید بفرستد

### تحویل دوره پولی

1. کاربر دوره می‌خرد → `CoursePurchase` با `access_status=waiting_personal_panel`
2. کانال تلگرام `MedCardy | پنل شخصی MCU-000001` بسازید
3. در ادمین → Personal Panels → `channel_link`, `invite_link`, `status=active`
4. در Course Purchases → `access_status=delivered`

### تحویل سفارش انفرادی

1. پرداخت → `ServiceOrder` با `status=waiting_admin_review`
2. اعلان به ادمین‌های تلگرام (یا `/admin` در بات)
3. فایل را از ادمین دانلود کنید (`media/orders/files/`)، پادکست بسازید
4. به PersonalPanel کاربر اضافه کنید
5. `status=delivered`, `production_status=done`

### تحویل سفارش گروهی

1. حداقل اعضا پرداخت کردند → `waiting_admin_review`
2. کانال `MedCardy | [عنوان] | MCS-G-YYMMDD-0001` بسازید
3. `private_channel_link` را تنظیم کنید → `status=delivered`

### حالت تعمیر قبل از به‌روزرسانی

از پنل ادمین تلگرام (`/admin` → حالت تعمیر) یا Django Admin → تنظیمات → `maintenance_mode=true` فعال کنید. ادمین‌ها همچنان دسترسی دارند.

---

## ۲۱. پشتیبان‌گیری و به‌روزرسانی

### پشتیبان‌گیری دیتابیس

```bash
# ایجاد بکاپ
sudo -u postgres pg_dump medcardy > backup_$(date +%Y%m%d).sql

# بازیابی
sudo -u postgres psql medcardy < backup_20250710.sql
```

### پشتیبان‌گیری فایل‌های media

```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz -C /var/www/medcardy media/
```

### به‌روزرسانی کد بعد از دیپلوی

```bash
cd /var/www/medcardy

# (اختیاری) فعال کردن حالت تعمیر از بات یا ادمین

git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart medcardy-web medcardy-bot

# بررسی
sudo systemctl status medcardy-web medcardy-bot
sudo journalctl -u medcardy-bot -n 20 --no-pager
```

### بکاپ خودکار (cron — اختیاری)

```bash
sudo crontab -e
```

```cron
# هر شب ساعت ۳ — بکاپ DB
0 3 * * * sudo -u postgres pg_dump medcardy > /var/backups/medcardy_$(date +\%Y\%m\%d).sql

# هر یکشنبه — بکاپ media
0 4 * * 0 tar -czf /var/backups/medcardy_media_$(date +\%Y\%m\%d).tar.gz -C /var/www/medcardy media/
```

```bash
sudo mkdir -p /var/backups
```

### تمدید SSL

Certbot به‌صورت خودکار cron دارد. تست دستی:

```bash
sudo certbot renew --dry-run
```

---

## ۲۲. امنیت پروداکشن

| مورد | اقدام |
|------|-------|
| `.env` | `chmod 600` — هرگز در git commit نکنید |
| `DEBUG` | حتماً `False` |
| `ALLOWED_HOSTS` | فقط دامنه‌های واقعی |
| `SECRET_KEY` | یکتا و تصادفی — با `secrets.token_urlsafe(50)` تولید کنید |
| SSH | کلید عمومی به‌جای رمز؛ غیرفعال کردن login با root (اختیاری) |
| فایروال | فقط 22, 80, 443 |
| PostgreSQL | فقط localhost — پورت 5432 را به اینترنت باز نکنید |
| توکن بات | در صورت لو رفتن از BotFather `/revoke` بزنید |
| بکاپ | هفتگی `pg_dump` + `media/` (شامل `payment_receipts/`) |

---

## ۲۳. عیب‌یابی

### ربات `/start` را جواب نمی‌دهد

```bash
sudo systemctl status medcardy-bot
sudo journalctl -u medcardy-bot -n 50
```

- `TELEGRAM_BOT_TOKEN` را چک کنید
- مطمئن شوید دو `runbot` همزمان اجرا نشده
- `maintenance_mode` را در ادمین چک کنید

### `/admin` کار نمی‌کند

- `ADMIN_TELEGRAM_IDS` باید شامل شناسه عددی **شما** باشد (نه یوزرنیم)
- بعد از تغییر `.env`، `runbot` را ری‌استارت کنید

### `Conflict: terminated by other getUpdates request`

دو پروسه ربات دارید — یکی را متوقف کنید:

```bash
sudo systemctl stop medcardy-bot
# پروسه‌های اضافی را kill کنید
sudo systemctl start medcardy-bot
```

### پرداخت انجام شد ولی تأیید نمی‌شود

1. `ZIBAL_CALLBACK_URL` باید HTTPS و از اینترنت در دسترس باشد
2. Django (Gunicorn) باید روشن باشد — نه فقط ربات
3. لاگ Django را ببینید:

```bash
sudo journalctl -u medcardy-web -f
# باید ببینید: Zibal callback received: ...
```

4. `curl` تست:

```bash
curl "https://medcardy.ir/api/payments/zibal/callback/?trackId=TEST&success=1"
```

### پیام تأیید پرداخت در تلگرام نمی‌رسد

- `TELEGRAM_BOT_TOKEN` در `.env` سرور درست باشد
- Django (نه فقط ربات) باید توکن را بخواند — هر دو سرویس از همان `.env` استفاده می‌کنند
- کاربر باید حداقل یک‌بار `/start` زده باشد تا بات بتواند پیام بفرستد

### خطای 502 Bad Gateway

- Gunicorn خاموش است: `sudo systemctl start medcardy-web`
- پورت اشتباه در Nginx
- لاگ: `sudo journalctl -u medcardy-web -n 30`

### خطای دیتابیس

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"
```

### `TELEGRAM_BOT_TOKEN is not set`

`.env` باید در همان پوشه `manage.py` باشد و مقدار توکن پر شده باشد. `WorkingDirectory` در systemd باید `/var/www/medcardy` باشد.

### فایل سفارش در ادمین نیست

- `media/orders/files/` روی سرور وجود دارد؟
- `www-data` دسترسی نوشتن دارد؟
- `client_max_body_size` در Nginx کافی است؟

### رسید پرداخت ذخیره نمی‌شود

- پوشه `media/payment_receipts/` وجود دارد؟
- `www-data` دسترسی نوشتن دارد؟ (`sudo chown -R www-data:www-data /var/www/medcardy/media`)
- `medcardy-bot` active است؟ (آپلود از ربات انجام می‌شود)

### شماره کارت در بات خالی است

- Django Admin → **تنظیمات** → `payment_card_number` را پر کنید
- نیازی به ری‌استارت سرویس نیست — مقدار از DB خوانده می‌شود

### پرداخت کارت‌به‌کارت تأیید نمی‌شود

- `/admin` → «پرداخت‌های در انتظار تأیید» را چک کنید
- یا Django Admin → Payments → فیلتر `receipt_submitted`
- `ADMIN_TELEGRAM_IDS` باید شامل شناسه ادمین تأییدکننده باشد

### آنالیز فایل PDF/Word کار نمی‌کند

- `pypdf` و `python-docx` در `requirements.txt` نصب شده باشند
- `pip install -r requirements.txt` را دوباره اجرا کنید

---

## ۲۴. خلاصه سریع

```
┌─────────────────────────────────────────────────────────┐
│  ۰. VPS (1GB RAM) + Python 3.11+ + PostgreSQL           │
│  ۱. BotFather → توکن + یوزرنیم                          │
│  ۲. git clone + venv + pip install + .env               │
│  ۳. migrate + seed + superuser                          │
│  ۴. تنظیمات ادمین: شماره کارت + ADMIN_TELEGRAM_IDS      │
│  ۵. Gunicorn (Django) + runbot (ربات) — systemd         │
│  ۶. (اختیاری) Nginx + SSL + دامنه                       │
│  ۷. MVP: کارت‌به‌کارت (enable_payment_gateway=false)    │
│  ۸. (بعداً) زیبال: enable_payment_gateway=true        │
│     Callback → https://DOMAIN/api/payments/zibal/callback/ │
│  ۹. تست /start + /admin + پرداخت + رسید                 │
│ ۱۰. انتشار https://t.me/YourBot                         │
└─────────────────────────────────────────────────────────┘
```

### یک خط جواب سوالات اصلی

| سوال | جواب |
|------|------|
| **سرور چی لازمه؟** | VPS Ubuntu 22.04/24.04، 1GB RAM، **Python 3.11+**، PostgreSQL 14+، Nginx |
| **بدون دامنه می‌شه؟** | **بله** — با پرداخت کارت‌به‌کارت (`enable_payment_gateway=false`) |
| **کال‌بک زیبال کجا بره؟** | `https://دامنه/api/payments/zibal/callback/` روی **Django** (Gunicorn) |
| **پرداخت پیش‌فرض چیه؟** | **کارت‌به‌کارت** — رسید در بات، تأیید از `/admin` |
| **ادمین تلگرام چطور؟** | `ADMIN_TELEGRAM_IDS` در `.env` + `/admin` در بات |
| **چند پروسه؟** | **دو تا:** `gunicorn` + `runbot` — هر دو همزمان |

---

*آخرین به‌روزرسانی: ژوئیه ۲۰۲۶ — مطابق کدبیس MedCardy Bot V1 (Django 5 + Aiogram 3 + پرداخت کارت‌به‌کارت + Zibal IPG + پنل ادمین تلگرام)*
