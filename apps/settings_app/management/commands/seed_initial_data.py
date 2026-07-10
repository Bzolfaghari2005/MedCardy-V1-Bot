"""
Seed initial data: settings, bot messages, categories, lessons, sample courses.
Run: python manage.py seed_initial_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed initial data for MedCardy bot'

    def handle(self, *args, **options):
        self._seed_settings()
        self._seed_bot_messages()
        self._seed_bot_labels()
        self._seed_categories_and_lessons()
        self._seed_sample_courses()
        self.stdout.write(self.style.SUCCESS('[OK] Seed data created successfully.'))

    def _seed_settings(self):
        from apps.settings_app.models import Setting
        defaults = [
            ('support_username', '@MedCardySupport', 'آیدی تلگرام پشتیبانی'),
            ('price_per_page_toman', '2500', 'قیمت هر صفحه آموزش کامل (تومان) — سازگاری با نسخه قبل'),
            ('full_price_per_page_toman', '2500', 'قیمت هر صفحه آموزش کامل (تومان)'),
            ('review_price_per_page_toman', '1250', 'قیمت هر صفحه نسخه مروری (تومان)'),
            ('base_price_per_100_pages_toman', '250000', 'قیمت پایه ۱۰۰ صفحه آموزش کامل (تومان)'),
            ('chars_per_normal_page', '2500', 'کاراکتر مرجع برای هر صفحه عادی'),
            ('group_min_members', '5', 'حداقل اعضای سفارش گروهی'),
            ('group_discount_percent', '30', 'درصد تخفیف سفارش گروهی'),
            ('enable_individual_orders', 'true', 'فعال‌سازی سفارش فردی'),
            ('enable_group_orders', 'true', 'فعال‌سازی سفارش گروهی'),
            ('enable_wallet', 'true', 'فعال‌سازی کیف پول'),
            ('enable_paid_courses', 'true', 'فعال‌سازی خرید دوره'),
            ('maintenance_mode', 'false', 'حالت تعمیر'),
            ('maintenance_message', 'بات در حال به‌روزرسانی است. لطفاً کمی صبر کنید.', 'پیام تعمیر'),
            ('enable_payment_gateway', 'false', 'فعال‌سازی درگاه آنلاین زیبال (true/false)'),
            ('payment_card_number', '', 'شماره کارت مقصد — ویرایش از پنل ادمین > تنظیمات'),
            ('payment_card_holder', '', 'نام صاحب حساب کارت'),
            ('payment_bank_name', '', 'نام بانک'),
            ('payment_sheba_number', '', 'شماره شبا (اختیاری)'),
            ('payment_transfer_note', 'حتماً کد پرداخت را در توضیحات واریز بنویسید.', 'یادداشت هشدار برای کاربر هنگام واریز'),
            ('payment_review_hours', '24', 'حداکثر ساعت انتظار برای تأیید رسید (در پیام receipt_received)'),
        ]
        for key, value, description in defaults:
            Setting.objects.get_or_create(key=key, defaults={'value': value, 'description': description})
        self.stdout.write('  [OK] Settings seeded')

    def _seed_bot_messages(self):
        from apps.bot_messages.models import BotMessage
        messages = [
            ('start_message',
             'پیام خوش‌آمدگویی',
             '✨ سلام، خوش اومدی به MedCardy!\n\n'
             '🎙️ MedCardy جزوه‌های پزشکی رو به پادکست‌های آموزشی حرفه‌ای تبدیل می‌کنه.\n\n'
             'از منوی پایین می‌تونی:\n'
             '📚 دوره‌های آماده رو مشاهده کنی\n'
             '🎙️ جزوه‌ات رو برای ساخت پادکست اختصاصی بفرستی\n'
             '👥 با همکلاسی‌هات سفارش گروهی بدی\n'
             '💳 کیف پولت رو مدیریت کنی\n\n'
             '⬇️ یه گزینه انتخاب کن:'),
            ('support_message',
             'پیام پشتیبانی',
             '💬 <b>پشتیبانی MedCardy</b>\n\n'
             'تیم ما همیشه اینجاست! برای هر سوال، پیشنهاد یا گزارش مشکل می‌تونی از طریق آیدی زیر پیام بدی:\n\n'
             '👤 <b>@MedCardySupport</b>\n\n'
             '💡 <i>برای پیگیری سریع‌تر، کد سفارش یا کد پرداخت رو در پیامت ذکر کن.</i>'),
            ('course_free_message',
             'دوره رایگان',
             '🆓 این دوره کاملاً رایگانه!\n\n'
             '🎧 از لینک زیر می‌تونی پادکست رو در کانال MedCardy ببینی و گوش بدی:'),
            ('course_paid_payment_message',
             'پیام خرید دوره',
             '💳 <b>پرداخت کارت‌به‌کارت</b>\n\n'
             'مبلغ را به شماره کارت اعلام‌شده واریز کن و رسید پرداخت را ارسال کن.\n\n'
             '⚠️ <i>حتماً کد پرداخت را در توضیحات واریز بنویس.</i>\n\n'
             '⏳ <i>بعد از تأیید پرداخت توسط ادمین:\n'
             '• پنل نداری؟ ظرف چند ساعت برات ساخته می‌شه\n'
             '• پنل داری؟ دوره ظرف چند ساعت به پنلت اضافه می‌شه\n'
             'لطفاً کمی صبر کن 🙏</i>'),
            ('individual_order_intro',
             'معرفی سفارش فردی',
             '🎙️ <b>ساخت پادکست اختصاصی</b>\n\n'
             'جزوه یا فایل درسی‌ات رو آپلود کن، ما ازش یه پادکست آموزشی حرفه‌ای می‌سازیم.\n\n'
             '👤 <b>سفارش فردی:</b> خروجی فقط برای شما، داخل پنل شخصی MedCardy.\n'
             '👥 <b>سفارش گروهی:</b> با همکلاسی‌ها هزینه رو تقسیم کنید، خروجی داخل یه کانال اختصاصی مشترک.\n\n'
             '⏰ <i>آماده‌سازی سفارش ممکنه ۴۸ ساعت یا بیشتر طول بکشه — هر چه زودتر اقدام کنید.</i>\n\n'
             'کدوم نوع سفارش می‌خوای؟'),
            ('group_order_intro',
             'معرفی سفارش گروهی',
             '👥 <b>سفارش گروهی</b>\n\n'
             'یه سفارش بساز، لینکش رو برای همکلاسی‌ها بفرست و هزینه رو بینتون تقسیم کنید.\n\n'
             '✔️ هر نفر جداگانه پرداخت می‌کنه\n'
             '✔️ بعد از تکمیل حداقل اعضا، سفارش وارد تولید می‌شه\n'
             '✔️ خروجی داخل یه کانال اختصاصی گروهی قرار می‌گیره\n\n'
             '⏰ <i>آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه — هر چه زودتر اقدام کنید.</i>\n\n'
             '🎁 <b>تخفیف ویژه گروهی</b> برای تمام سفارش‌های گروهی اعمال می‌شه!'),
            ('wallet_intro',
             'معرفی کیف پول',
             '💳 <b>کیف پول MedCardy</b>\n\n'
             'کیف پولت رو با واریز کارت‌به‌کارت شارژ کن و برای خرید دوره‌ها یا ثبت سفارش ازش استفاده کن.\n\n'
             '📸 بعد از واریز، رسید پرداخت را ارسال کن تا ادمین تأیید کند.'),
            ('help_message',
             'راهنما',
             '❓ <b>راهنمای کامل MedCardy</b>\n\n'
             '📚 <b>دوره‌های آماده:</b>\n'
             '• دوره‌های رایگان: لینک کانال عمومی ارسال می‌شه\n'
             '• دوره‌ها: بعد از خرید، ظرف چند ساعت در پنل شخصی شما\n\n'
             '🎙️ <b>سفارش ساخت پادکست:</b>\n'
             '• فردی: جزوه بفرستید، پادکست اختصاصی بسازید\n'
             '• گروهی: با دوستان هزینه رو تقسیم کنید\n'
             '• زمان آماده‌سازی: معمولاً ۴۸ ساعت یا بیشتر\n\n'
             '💳 <b>کیف پول:</b> شارژ و مدیریت موجودی\n\n'
             'برای هر سوالی، پشتیبانی آماده‌ست 👇'),
            ('rules_message',
             'قوانین',
             '📋 <b>قوانین و مقررات MedCardy</b>\n\n'
             '۱. پس از پرداخت موفق، محتوا توسط تیم MedCardy آماده می‌شه و در پنل شما قرار می‌گیره.\n'
             '۲. خرید دوره: ظرف چند ساعت در پنل قرار می‌گیره (یا پنل ساخته می‌شه).\n'
             '۳. سفارش فردی/گروهی: آماده‌سازی ممکنه ۴۸ ساعت یا بیشتر طول بکشه.\n'
             '۴. در صورت هرگونه مشکل یا سوال، از طریق پشتیبانی با ما در تماس باش.\n'
             '۵. فایل‌های ارسالی محرمانه بوده و فقط برای ساخت پادکست استفاده می‌شن.'),
            ('manual_payment_instructions',
             'پرداخت — راهنمای کارت‌به‌کارت',
             '💳 <b>راهنمای پرداخت کارت‌به‌کارت</b>\n\n'
             '🔑 کد پرداخت: <code>{payment_code}</code>\n'
             '💰 مبلغ: <code>{amount_copy}</code> تومان\n\n'
             '🏦 شماره کارت: <code>{card_number_copy}</code>\n'
             '👤 به نام: {card_holder}\n'
             '🏛️ بانک: {bank_name}\n'
             '🔢 شبا: {sheba_number}\n\n'
             '⚠️ <i>{transfer_note}</i>\n\n'
             '📸 سپس با دکمه زیر، عکس رسید پرداخت را ارسال کنید.\n'
             '<i>👆 روی مبلغ و شماره کارت بزن تا کپی بشه.</i>'),
            ('receipt_upload_prompt',
             'پرداخت — درخواست ارسال رسید',
             '📸 <b>ارسال رسید پرداخت</b>\n\n'
             '🔑 کد پرداخت: <code>{payment_code}</code>\n'
             '💰 مبلغ: <code>{amount_copy}</code> تومان\n\n'
             'لطفاً <b>عکس یا فایل رسید</b> واریز را ارسال کن.\n'
             '<i>برای لغو: دکمه بازگشت یا /start</i>'),
            ('receipt_received',
             'پرداخت — رسید دریافت شد',
             '✅ <b>رسید دریافت شد!</b>\n\n'
             '🔑 کد پرداخت: <code>{payment_code}</code>\n'
             '◉ وضعیت: ⏳ در انتظار تأیید ادمین\n\n'
             '<i>بررسی و تأیید پرداخت ممکن است تا {review_hours} ساعت طول بکشد. '
             'نتیجه به شما اطلاع داده می‌شود.</i>'),
            ('receipt_rejected',
             'پرداخت — رسید رد شد',
             '❌ <b>رسید پرداخت رد شد</b>\n\n'
             '🔑 کد پرداخت: <code>{payment_code}</code>\n'
             '💰 مبلغ: <code>{amount_copy}</code> تومان{reason}\n\n'
             'می‌تونی دوباره واریز کنی و رسید جدید ارسال کنی.\n'
             '💬 برای راهنمایی با پشتیبانی تماس بگیر: @MedCardySupport'),
            ('payment_request_failed',
             'پرداخت — خطا در ساخت درخواست',
             '❌ ساخت درخواست پرداخت با مشکل مواجه شد.\n\n'
             'چند دقیقه صبر کن و دوباره تلاش کن یا با پشتیبانی در تماس باش.'),
            ('gateway_payment_instructions',
             'پرداخت — راهنمای درگاه آنلاین',
             '🔐 برای پرداخت آنلاین از طریق درگاه امن زیبال روی دکمه زیر بزن.\n\n'
             '🔑 کد پرداخت: <code>{payment_code}</code>\n'
             '💰 مبلغ: <code>{amount_copy}</code> تومان'),
        ]
        for key, title, text in messages:
            BotMessage.objects.update_or_create(
                key=key,
                defaults={'title': title, 'text': text},
            )
        self.stdout.write('  [OK] Bot messages seeded')

    def _seed_bot_labels(self):
        from apps.bot_messages.models import BotLabel
        from apps.telegram_bot.utils import LABEL_DEFAULTS

        LABEL_META = {
            'menu.courses': ('منوی اصلی — دوره‌ها', BotLabel.CATEGORY_MENU, 1),
            'menu.order': ('منوی اصلی — سفارش پادکست', BotLabel.CATEGORY_MENU, 2),
            'menu.my_courses': ('منوی اصلی — دوره‌های من', BotLabel.CATEGORY_MENU, 3),
            'menu.my_services': ('منوی اصلی — سرویس‌های من', BotLabel.CATEGORY_MENU, 4),
            'menu.favorites': ('منوی اصلی — علاقه‌مندی‌ها', BotLabel.CATEGORY_MENU, 5),
            'menu.wallet': ('منوی اصلی — کیف پول', BotLabel.CATEGORY_MENU, 6),
            'menu.support': ('منوی اصلی — پشتیبانی', BotLabel.CATEGORY_MENU, 7),
            'menu.help': ('منوی اصلی — راهنما', BotLabel.CATEGORY_MENU, 8),
            'btn.back': ('دکمه — بازگشت', BotLabel.CATEGORY_BUTTON, 10),
            'btn.main': ('دکمه — منوی اصلی', BotLabel.CATEGORY_BUTTON, 11),
            'btn.back_to_main': ('دکمه — بازگشت به منوی اصلی', BotLabel.CATEGORY_BUTTON, 12),
            'btn.view_other_courses': ('دکمه — مشاهده دوره‌های دیگر', BotLabel.CATEGORY_BUTTON, 13),
            'btn.back_to_help': ('دکمه — بازگشت به راهنما', BotLabel.CATEGORY_BUTTON, 14),
            'btn.free_get': ('دکمه — دریافت رایگان', BotLabel.CATEGORY_BUTTON, 20),
            'btn.buy': ('دکمه — خرید دوره', BotLabel.CATEGORY_BUTTON, 21),
            'btn.add_favorite': ('دکمه — افزودن علاقه‌مندی', BotLabel.CATEGORY_BUTTON, 22),
            'btn.remove_favorite': ('دکمه — حذف علاقه‌مندی', BotLabel.CATEGORY_BUTTON, 23),
            'btn.individual_order': ('دکمه — سفارش فردی', BotLabel.CATEGORY_BUTTON, 24),
            'btn.group_order': ('دکمه — سفارش گروهی', BotLabel.CATEGORY_BUTTON, 25),
            'btn.pricing_guide': ('دکمه — راهنمای قیمت', BotLabel.CATEGORY_BUTTON, 26),
            'btn.charge_wallet': ('دکمه — شارژ کیف پول', BotLabel.CATEGORY_BUTTON, 27),
            'btn.transactions': ('دکمه — تراکنش‌ها', BotLabel.CATEGORY_BUTTON, 28),
            'btn.pay_online': ('دکمه — پرداخت آنلاین', BotLabel.CATEGORY_BUTTON, 29),
            'btn.submit_receipt': ('دکمه — ارسال رسید پرداخت', BotLabel.CATEGORY_BUTTON, 39),
            'btn.pay_my_share': ('دکمه — پرداخت سهم من', BotLabel.CATEGORY_BUTTON, 30),
            'btn.join_and_pay': ('دکمه — پرداخت و عضویت', BotLabel.CATEGORY_BUTTON, 31),
            'btn.skip': ('دکمه — رد کردن', BotLabel.CATEGORY_BUTTON, 32),
            'btn.confirm_pay': ('دکمه — تأیید و ثبت سفارش', BotLabel.CATEGORY_BUTTON, 33),
            'btn.cancel': ('دکمه — انصراف', BotLabel.CATEGORY_BUTTON, 34),
            'btn.custom_amount': ('دکمه — مبلغ دلخواه', BotLabel.CATEGORY_BUTTON, 35),
            'btn.view_my_orders': ('دکمه — کد سفارش‌های من', BotLabel.CATEGORY_BUTTON, 36),
            'btn.confirm_pages': ('دکمه — تأیید صفحات', BotLabel.CATEGORY_BUTTON, 37),
            'btn.edit_pages': ('دکمه — ویرایش صفحات', BotLabel.CATEGORY_BUTTON, 38),
            'wallet.amount.100000': ('کیف پول — ۱۰۰ هزار تومان', BotLabel.CATEGORY_WALLET, 1),
            'wallet.amount.250000': ('کیف پول — ۲۵۰ هزار تومان', BotLabel.CATEGORY_WALLET, 2),
            'wallet.amount.500000': ('کیف پول — ۵۰۰ هزار تومان', BotLabel.CATEGORY_WALLET, 3),
            'wallet.amount.1000000': ('کیف پول — ۱ میلیون تومان', BotLabel.CATEGORY_WALLET, 4),
            'tier.review': ('نسخه — مروری', BotLabel.CATEGORY_TIER, 1),
            'tier.full': ('نسخه — آموزش کامل', BotLabel.CATEGORY_TIER, 2),
            'tier.review_inline': ('نسخه — مروری (اینلاین)', BotLabel.CATEGORY_TIER, 3),
            'tier.full_inline': ('نسخه — کامل (اینلاین)', BotLabel.CATEGORY_TIER, 4),
        }

        sort = 100
        for key, text in LABEL_DEFAULTS.items():
            if key in LABEL_META:
                title, category, order = LABEL_META[key]
            elif key.startswith('status.'):
                title = f'وضعیت — {key.split(".", 2)[-1]}'
                category = BotLabel.CATEGORY_STATUS
                order = sort
                sort += 1
            else:
                title = key
                category = BotLabel.CATEGORY_BUTTON
                order = sort
                sort += 1
            BotLabel.objects.get_or_create(
                key=key,
                defaults={'text': text, 'title': title, 'category': category, 'sort_order': order},
            )
        self.stdout.write('  [OK] Bot labels seeded')

    def _seed_categories_and_lessons(self):
        from apps.catalog.models import Category, Lesson

        categories_data = [
            ('علوم پایه پزشکی', ['آناتومی', 'فیزیولوژی', 'بیوشیمی', 'ایمونولوژی', 'میکروب‌شناسی', 'پاتولوژی', 'ژنتیک', 'بافت‌شناسی', 'جنین‌شناسی']),
            ('علوم پایه دندانپزشکی', ['آناتومی سر و گردن', 'فیزیولوژی دهان', 'بیوشیمی']),
            ('فیزیوپاتولوژی', ['فیزیوپات قلب', 'فیزیوپات تنفس', 'فیزیوپات گوارش']),
            ('استاجری', ['استاجری داخلی', 'استاجری جراحی', 'استاجری اطفال', 'استاجری زنان']),
            ('پره‌انترنی', ['پره‌انترنی داخلی', 'پره‌انترنی جراحی']),
            ('دستیاری', ['کاردیولوژی', 'نورولوژی', 'ارتوپدی']),
            ('لیسانس به پزشکی', ['بیوشیمی', 'فیزیولوژی']),
            ('سایر دوره‌ها', ['دوره‌های متفرقه']),
        ]

        for idx, (cat_title, lesson_titles) in enumerate(categories_data, start=1):
            cat_slug = slugify(cat_title, allow_unicode=True) or f'cat-{idx}'
            category, _ = Category.objects.get_or_create(
                title=cat_title,
                defaults={'slug': cat_slug, 'sort_order': idx}
            )
            for l_idx, lesson_title in enumerate(lesson_titles, start=1):
                Lesson.objects.get_or_create(
                    title=lesson_title,
                    category=category,
                    defaults={'sort_order': l_idx}
                )
        self.stdout.write('  [OK] Categories and lessons seeded')

    def _seed_sample_courses(self):
        from apps.catalog.models import Category, Lesson
        from apps.courses.models import Course

        try:
            cat = Category.objects.get(title='علوم پایه پزشکی')
            lesson = Lesson.objects.get(title='فیزیولوژی', category=cat)
        except (Category.DoesNotExist, Lesson.DoesNotExist):
            self.stdout.write('  ⚠ Sample courses skipped (category/lesson not found)')
            return

        Course.objects.get_or_create(
            title='فیزیولوژی غدد و تولیدمثل - نمونه رایگان',
            defaults={
                'category': cat,
                'lesson': lesson,
                'course_type': Course.TYPE_FREE,
                'price_toman': 0,
                'short_description': 'پادکست رایگان فیزیولوژی غدد - مناسب برای پایه‌پزشکی',
                'pages_count': 50,
                'duration_text': '۴۵ دقیقه',
                'episodes_count': 3,
                'public_channel_post_link': 'https://t.me/MedCardyChannel/1',
                'status': Course.STATUS_ACTIVE,
                'is_featured': True,
                'sort_order': 1,
            }
        )

        Course.objects.get_or_create(
            title='فیزیولوژی گردش خون - دوره کامل',
            defaults={
                'category': cat,
                'lesson': lesson,
                'course_type': Course.TYPE_PAID,
                'price_toman': 250000,
                'short_description': 'پادکست کامل فیزیولوژی گردش خون با کیفیت بالا',
                'pages_count': 100,
                'duration_text': '۲ ساعت',
                'episodes_count': 8,
                'status': Course.STATUS_ACTIVE,
                'is_featured': True,
                'sort_order': 2,
            }
        )
        self.stdout.write('  [OK] Sample courses seeded')
