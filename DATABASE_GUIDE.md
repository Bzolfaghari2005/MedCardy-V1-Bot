# راهنمای دیتابیس MedCardy (PostgreSQL + Django)

## چرا `psql` کار نمی‌کند؟

خطای `psql is not recognized` یعنی **PostgreSQL نصب نیست** یا **مسیر `bin` آن در PATH ویندوز نیست**.

روی سیستم شما PostgreSQL 16 نصب است، اما PowerShell فقط وقتی `psql` را می‌شناسد که در PATH باشد. فایل اجرایی اینجاست:

```
C:\Program Files\PostgreSQL\16\bin\psql.exe
```

---

## روش‌های اتصال (ویندوز)

### ۱) اسکریپت آماده پروژه (ساده‌ترین)

از ریشه پروژه:

```powershell
.\scripts\database\psql.ps1
.\scripts\database\psql.ps1 -Database medcardy
.\scripts\database\psql.ps1 -File scripts\database\setup_medcardy.sql
```

### ۲) مسیر کامل

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

### ۳) SQL Shell از منوی استارت

`Start` → جستجو: **SQL Shell (psql)** → Enter برای پیش‌فرض‌ها → رمز `postgres`.

### ۴) pgAdmin 4

`Start` → **pgAdmin 4** → راست‌کلیک روی `Databases` → `Query Tool`.

### ۵) اضافه کردن دائمی به PATH (اختیاری)

`Win + R` → `sysdm.cpl` → Advanced → Environment Variables → در `Path` کاربر این را اضافه کنید:

```
C:\Program Files\PostgreSQL\16\bin
```

ترمینال را ببندید و دوباره باز کنید. بعد `psql -U postgres` کار می‌کند.

---

## نصب PostgreSQL (اگر اصلاً نصب نیست)

```powershell
winget install PostgreSQL.PostgreSQL.16
```

در نصب، رمز کاربر `postgres` را یادداشت کنید. سرویس باید روی پورت `5432` بالا باشد.

---

## راه‌اندازی اولیه MedCardy

### گزینه A — با کاربر `postgres` (توسعه سریع)

`.env` فعلی شما:

```env
DATABASE_URL=postgres://postgres:postgres@localhost:5432/medcardy
```

فقط دیتابیس را بسازید:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE medcardy;"
```

### گزینه B — کاربر اختصاصی `medcardy_user` (نزدیک به پروداکشن)

```powershell
.\scripts\database\psql.ps1 -File scripts\database\setup_medcardy.sql
```

سپس در `.env`:

```env
DATABASE_URL=postgres://medcardy_user:medcardymedcardy20252025@localhost:5432/medcardy
```

---

## دستورات Django (پرکاربرد)

از ریشه پروژه (`MedCardy Bot V1`):

```powershell
# ساخت/به‌روزرسانی جداول
python manage.py migrate

# داده اولیه (تنظیمات، پیام‌ها، دسته‌ها، دوره‌های نمونه)
python manage.py seed_initial_data

# سوپریوزر پنل ادمین
python manage.py createsuperuser

# بررسی اتصال دیتابیس
python manage.py dbshell

# ساخت migration جدید بعد از تغییر models
python manage.py makemigrations
python manage.py migrate
```

ترتیب پیشنهادی اولین بار:

```powershell
python manage.py migrate
python manage.py seed_initial_data
python manage.py createsuperuser
python manage.py runserver
```

---

## فایل‌های SQL پروژه

| فایل | کاربرد |
|------|--------|
| `scripts/database/setup_medcardy.sql` | ساخت دیتابیس + کاربر + دسترسی‌ها |
| `scripts/database/common_queries.sql` | کوئری‌های روزمره (کاربران، سفارش، کیف پول) |
| `scripts/database/reset_medcardy.sql` | پاک کردن کامل دیتابیس (فقط توسعه) |
| `scripts/database/psql.ps1` | اجرای psql بدون PATH |

---

## کوئری‌های سریع داخل psql

```sql
-- اتصال به دیتابیس
\c medcardy

-- لیست جداول
\dt

-- خروج
\q
```

بقیه کوئری‌ها در `scripts/database/common_queries.sql`.

---

## خطاهای رایج

| خطا | علت احتمالی | راه‌حل |
|-----|-------------|--------|
| `psql is not recognized` | PATH تنظیم نیست | از `psql.ps1` یا مسیر کامل استفاده کنید |
| `password authentication failed` | رمز اشتباه در `.env` | رمز نصب PostgreSQL را در `DATABASE_URL` بگذارید |
| `database "medcardy" does not exist` | دیتابیس ساخته نشده | `setup_medcardy.sql` یا `CREATE DATABASE medcardy` |
| `permission denied for schema public` | دسترسی کاربر کم است | بخش GRANT در `setup_medcardy.sql` را اجرا کنید |
| `connection refused` | سرویس PostgreSQL خاموش است | Services → `postgresql-x64-16` → Start |
| `migrate` خطا می‌دهد | دیتابیس/کاربر اشتباه | `DATABASE_URL` را با psql تست کنید |

---

## دو نسخه PostgreSQL روی یک ویندوز

اگر هم **9.6** و هم **16** نصب باشد:

| نسخه | پورت پیش‌فرض | توضیح |
|------|-------------|--------|
| PostgreSQL 9.6 | **5432** | قدیمی — برای MedCardy استفاده نکنید |
| PostgreSQL 16 | **5433** | همین را استفاده کنید (نیاز پروژه: 14+) |

`localhost:5432` به نسخه ۹.۶ وصل می‌شود، نه ۱۶. در `.env` باید پورت **5433** باشد:

```env
DATABASE_URL=postgres://postgres:YOUR_PASSWORD@localhost:5433/medcardy
```

اسکریپت `psql.ps1` پورت را خودکار از `postgresql.conf` می‌خواند.

---

## فراموشی رمز postgres

موقع نصب PostgreSQL یک رمز برای کاربر `postgres` انتخاب می‌شود. اگر یادتان نیست:

### روش خودکار (پیشنهادی)

1. **PowerShell را Run as administrator** باز کنید
2. از ریشه پروژه اجرا کنید:

```powershell
cd "C:\Users\Benyamin\Desktop\MedCardy Bot V1"
.\scripts\database\reset_postgres_password.ps1
```

رمز جدید پیش‌فرض: `postgres` (قابل تغییر با `-NewPassword "..."`).

3. همان رمز را در `.env` بگذارید:

```env
DATABASE_URL=postgres://postgres:postgres@localhost:5432/medcardy
```

### روش دستی

1. فایل را با Notepad **Run as administrator** باز کنید:
   `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`
2. خطوط `scram-sha-256` مربوط به `127.0.0.1` و `::1` را موقتاً به `trust` تغییر دهید
3. سرویس `postgresql-x64-16` را Restart کنید
4. بدون رمز وصل شوید و رمز جدید بگذارید:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h 127.0.0.1 -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

5. `pg_hba.conf` را به حالت قبل برگردانید و دوباره Restart کنید

---

## بکاپ و بازیابی

```powershell
# بکاپ
& "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" -U postgres -d medcardy -F c -f medcardy_backup.dump

# بازیابی
& "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -d medcardy -c medcardy_backup.dump
```

---

## چک‌لیست سریع

- [ ] PostgreSQL نصب و سرویس `postgresql-x64-16` در حال اجراست
- [ ] دیتابیس `medcardy` ساخته شده
- [ ] `DATABASE_URL` در `.env` با رمز درست تنظیم شده
- [ ] `python manage.py migrate` بدون خطا اجرا شده
- [ ] `python manage.py seed_initial_data` اجرا شده (اختیاری ولی توصیه می‌شود)
