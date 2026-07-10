# MedCardy Bot MVP

پلتفرم آموزش پزشکی فارسی‌زبان با تمرکز بر تلگرام که جزوات دانشگاهی را به دوره‌های پادکست تبدیل می‌کند.

## پشته فناوری

- **Python 3.11+**
- **Django 5.x** — بک‌اند، پنل ادمین، REST callback
- **PostgreSQL** — پایگاه داده
- **Aiogram 3.x** — ربات تلگرام
- **Zibal IPG** — درگاه پرداخت آنلاین
- **python-decouple** — پیکربندی محیط (environment)

## ساختار پروژه

```
medcardy_bot/
  config/               # settings, urls, wsgi, asgi
  apps/
    users/              # TelegramUser, PersonalPanel
    catalog/            # Category, Lesson
    courses/            # Course, CoursePurchase
    orders/             # ServiceOrder, ServiceOrderMember
    payments/           # Payment, ZibalService, callback view
    wallet/             # WalletTransaction
    favorites/          # Favorite
    bot_messages/       # BotMessage (قابل ویرایش از ادمین)
    settings_app/       # Setting + دستور seed_initial_data
    telegram_bot/       # هندلرهای Aiogram، حالت‌های FSM، دستور runbot
  manage.py
  requirements.txt
  .env.example
```

## دیپلوی و انتشار

راهنمای کامل دیپلوی روی سرور (SSL، Nginx، systemd، زیبال پروداکشن): **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)**  
بخش مختص تلگرام: **[TELEGRAM_DEPLOY_GUIDE.md](TELEGRAM_DEPLOY_GUIDE.md)**

---

## راه‌اندازی

### ۱. پیش‌نیازها

- Python 3.11+
- PostgreSQL 14+

### ۲. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### ۳. راه‌اندازی PostgreSQL

راهنمای کامل ویندوز + دستورات پرکاربرد: **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)**

```powershell
# سریع (بدون نیاز به PATH)
.\scripts\database\psql.ps1 -File scripts\database\setup_medcardy.sql
```

```sql
CREATE DATABASE medcardy;
CREATE USER medcardy_user WITH PASSWORD 'medcardymedcardy20252025';
GRANT ALL PRIVILEGES ON DATABASE medcardy TO medcardy_user;
```

### ۴. پیکربندی محیط

```bash
cp .env.example .env
```

فایل `.env` را ویرایش کنید:

```env
DEBUG=True
SECRET_KEY=your-very-long-secret-key

DATABASE_URL=postgres://medcardy_user:your_password@localhost:5432/medcardy

TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_BOT_USERNAME=YourBotUsername

SITE_BASE_URL=https://yourdomain.com

ZIBAL_BASE_URL=https://gateway.zibal.ir
ZIBAL_MERCHANT=zibal            # برای تست از 'zibal' استفاده کنید؛ در پروداکشن شناسه واقعی مرچنت
ZIBAL_CALLBACK_URL=https://yourdomain.com/api/payments/zibal/callback/
ZIBAL_TEST_MODE=True            # در پروداکشن False بگذارید

DEFAULT_SUPPORT_USERNAME=@YourSupportUsername

# شناسه عددی ادمین‌های تلگرام (برای /admin و اعلان سفارش‌ها)
ADMIN_TELEGRAM_IDS=123456789
```

### ۵. اجرای مایگریشن‌ها

```bash
python manage.py migrate
```

### ۶. ساخت سوپریوزر

```bash
python manage.py createsuperuser
```

### ۷. بارگذاری داده‌های اولیه

```bash
python manage.py seed_initial_data
```

این دستور موارد زیر را ایجاد می‌کند:
- تنظیمات پیش‌فرض (قیمت‌گذاری، فلگ‌های قابلیت)
- تمام پیام‌های بات (قابل ویرایش از ادمین)
- ۸ دسته‌بندی پیش‌فرض (علوم پایه پزشکی و غیره)
- بیش از ۳۰ درس
- ۲ دوره نمونه (۱ رایگان، ۱ پولی)

### ۸. اجرای سرور Django

```bash
python manage.py runserver
```

پنل ادمین: http://localhost:8000/admin/

### ۹. اجرای ربات تلگرام

در یک **ترمینال جداگانه**:

```bash
python manage.py runbot
```

ربات و سرور Django به‌صورت دو پروسه جدا اجرا می‌شوند. Django endpoint مربوط به callback زیبال را مدیریت می‌کند و ربات پیام‌های تلگرام را پردازش می‌کند.

---

## راه‌اندازی پرداخت زیبال

### حالت تست

در `.env` مقدارهای `ZIBAL_MERCHANT=zibal` و `ZIBAL_TEST_MODE=True` را تنظیم کنید.

در حالت تست می‌توانید از sandbox زیبال برای آزمایش پرداخت بدون پول واقعی استفاده کنید.

### حالت پروداکشن

1. در [zibal.ir](https://zibal.ir) ثبت‌نام کنید
2. شناسه مرچنت را از داشبورد زیبال دریافت کنید
3. `ZIBAL_MERCHANT=your_real_merchant_id` را تنظیم کنید
4. `ZIBAL_TEST_MODE=False` را تنظیم کنید

### تنظیم آدرس Callback

آدرس callback باید از اینترنت قابل دسترسی باشد. در محیط توسعه از تونلی مثل [ngrok](https://ngrok.com) استفاده کنید:

```bash
ngrok http 8000
```

سپس تنظیم کنید:
```env
ZIBAL_CALLBACK_URL=https://your-ngrok-url.ngrok.io/api/payments/zibal/callback/
SITE_BASE_URL=https://your-ngrok-url.ngrok.io
```

---

## جریان پرداخت

```
کاربر محصول را انتخاب می‌کند
    → سیستم رکورد Payment ایجاد می‌کند
    → API زیبال /v1/request را فراخوانی می‌کند
    → trackId دریافت می‌شود
    → لینک پرداخت به کاربر ارسال می‌شود (https://gateway.zibal.ir/start/{trackId})
    → کاربر در زیبال پرداخت می‌کند
    → زیبال به /api/payments/zibal/callback/ هدایت می‌کند
    → بک‌اند API زیبال /v1/verify را فراخوانی می‌کند
    → اگر result=100 یا 201 باشد: خرید/سفارش/کیف پول فعال می‌شود
    → ربات از طریق پیام تلگرام به کاربر اطلاع می‌دهد
```

### قانون مبلغ زیبال

تمام قیمت‌ها به **تومان** ذخیره می‌شوند. قبل از ارسال به زیبال، در ۱۰ ضرب کنید تا به **ریال** تبدیل شود.

---

## فرایندهای ادمین

### تحویل دوره‌های پولی به پنل شخصی

1. کاربر دوره پولی می‌خرد → `CoursePurchase` با `access_status=waiting_personal_panel` ایجاد می‌شود
2. ادمین Django Admin → Course Purchases را باز می‌کند و خرید را پیدا می‌کند
3. به‌صورت دستی کانال تلگرامی با نام `MedCardy | پنل شخصی MCU-000001` بسازید
4. محتوای دوره را به کانال اضافه کنید
5. Django Admin → Personal Panels را باز کنید و کاربر را پیدا کنید
6. `channel_link` و `invite_link` را تنظیم کنید
7. `status = active` را تنظیم کنید
8. در Course Purchases: `access_status = delivered` و `access_link` را تنظیم کنید
9. ربات به کاربر اطلاع می‌دهد (یا ادمین می‌تواند اکشن notify سفارشی اجرا کند)

### تحویل سفارش‌های انفرادی

1. کاربر برای سفارش انفرادی پرداخت می‌کند → `ServiceOrder` با `status=waiting_admin_review` ایجاد می‌شود
2. ادمین فایل آپلودشده را از Django Admin دانلود می‌کند
3. پادکست را به‌صورت خارجی تولید می‌کند
4. ادمین کانال PersonalPanel کاربر را باز می‌کند و فایل‌های پادکست را اضافه می‌کند
5. Django Admin → Service Orders → سفارش را پیدا کنید
6. در صورت نیاز `private_channel_link` را تنظیم کنید (یا از پنل شخصی استفاده کنید)
7. `status = delivered` و `production_status = done` را تنظیم کنید
8. فیلد `personal_panel` نشان می‌دهد محتوا باید به کدام پنل تحویل شود

### تحویل سفارش‌های گروهی

1. حداقل اعضای پرداخت‌کننده رسید → `ServiceOrder.status = waiting_admin_review`
2. ادمین فایل را دانلود می‌کند و پادکست را تولید می‌کند
3. کانال تلگرام جدیدی با نام `MedCardy | [Short Title] | MCS-G-YYMMDD-0001` بسازید
4. محتوای پادکست را به این کانال اضافه کنید
5. Django Admin → Service Orders → سفارش را پیدا کنید
6. `private_channel_link` را به لینک کانال گروهی جدید تنظیم کنید
7. `status = delivered` را تنظیم کنید
8. ربات به همه اعضای پرداخت‌کننده اطلاع می‌دهد (با اکشن ادمین فعال می‌شود)

---

## دستورات ربات

| دستور | توضیح |
|---------|-------------|
| `/start` | شروع ربات، ثبت‌نام کاربر، نمایش منوی اصلی |
| `/start G...` | پیوستن به سفارش گروهی از طریق deep link |

## منوی اصلی

| دکمه | توضیح |
|--------|-------------|
| دوره‌ها | مرور دسته‌بندی‌ها → درس‌ها → دوره‌ها |
| سفارش ساخت پادکست | سفارش پادکست انفرادی یا گروهی |
| دوره‌های من | مشاهده دوره‌های خریداری‌شده |
| سرویس‌های من | مشاهده سفارش‌های سرویس |
| علاقه‌مندی‌ها | موارد ذخیره‌شده |
| کیف پول | موجودی کیف پول و شارژ از طریق زیبال |
| نظرات و پشتیبانی | تماس با پشتیبانی |
| راهنما | سوالات متداول |

---

## ویرایش پیام‌های ربات

تمام پیام‌های ربات از Django Admin → **پیام‌های بات** قابل ویرایش هستند.

کلیدهای مهم پیام:
- `start_message` — پیام خوش‌آمدگویی
- `support_message` — متن بخش پشتیبانی
- `individual_order_intro` — مقدمه سفارش انفرادی
- `group_order_intro` — مقدمه سفارش گروهی
- `help_message` — مقدمه سوالات متداول

---

## ویرایش تنظیمات

تنظیمات غیرحساس از Django Admin → **تنظیمات** قابل ویرایش هستند:
- `price_per_page_toman` — قیمت به ازای هر صفحه
- `group_min_members` — حداقل اعضای گروه
- `group_discount_percent` — تخفیف گروهی
- `enable_individual_orders` / `enable_group_orders` — فلگ‌های قابلیت
- `maintenance_mode` — حالت تعمیر و نگهداری

تنظیمات حساس (شناسه مرچنت، توکن بات) در `.env` باقی می‌مانند.

---

## توسعه آینده

معماری برای یکپارچه‌سازی با وب‌سایت طراحی شده است:
- تمام مدل‌ها مستقل از فریم‌ورک هستند (بدون فرض تلگرام‌محور)
- لایه سرویس از هندلرهای ربات جدا است
- سرویس پرداخت هر کانالی را پشتیبانی می‌کند (زیبال، کیف پول، درگاه‌های آینده)
- پنل ادمین مستقل از ربات کار می‌کند
#   M e d C a r d y - B o t - V 1  
 