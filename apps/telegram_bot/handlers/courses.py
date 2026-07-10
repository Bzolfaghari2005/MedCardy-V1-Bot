import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async

from apps.telegram_bot.filters import LabelFilter
from apps.telegram_bot.utils import format_toman, get_status_label
from apps.telegram_bot.keyboards import (
    categories_keyboard, lessons_keyboard, courses_keyboard,
    course_detail_keyboard, free_course_received_keyboard, main_menu_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()

# Store last lesson context per user for back navigation
_user_lesson_context: dict = {}
_user_category_context: dict = {}


@router.message(LabelFilter('menu.courses'))
async def courses_menu(message: Message):
    categories = await _get_active_categories()
    if not categories:
        await message.answer('📭 در حال حاضر دوره‌ای در دسترس نیست. به‌زودی دوره‌های جدید اضافه می‌شن!')
        return
    await message.answer('📚 دسته‌بندی مورد نظرت رو انتخاب کن:', reply_markup=categories_keyboard(categories))


@router.callback_query(F.data.startswith('cat:'))
async def category_selected(callback: CallbackQuery):
    cat_id = int(callback.data.split(':')[1])
    _user_category_context[callback.from_user.id] = cat_id
    lessons = await _get_lessons_for_category(cat_id)
    if not lessons:
        await callback.answer('📭 هنوز درسی در این دسته‌بندی اضافه نشده.', show_alert=True)
        return
    await callback.message.edit_text(
        '📖 درس مورد نظرت رو انتخاب کن:',
        reply_markup=await lessons_keyboard(lessons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('les:'))
async def lesson_selected(callback: CallbackQuery):
    lesson_id = int(callback.data.split(':')[1])
    _user_lesson_context[callback.from_user.id] = lesson_id
    courses = await _get_courses_for_lesson(lesson_id)
    if not courses:
        await callback.answer('📭 هنوز دوره‌ای برای این درس منتشر نشده.', show_alert=True)
        return
    await callback.message.edit_text(
        '🎧 دوره مورد نظرت رو انتخاب کن:',
        reply_markup=await courses_keyboard(courses),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('course:'))
async def course_detail(callback: CallbackQuery):
    course_id = int(callback.data.split(':')[1])
    course = await _get_course(course_id)
    if not course:
        await callback.answer('⚠️ دوره پیدا نشد. لطفاً دوباره تلاش کن.', show_alert=True)
        return

    is_favorited = await _is_favorited(callback.from_user.id, 'course', course_id)
    text = _build_course_detail_text(course)
    keyboard = await course_detail_keyboard(course, is_favorited)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data.startswith('free_get:'))
async def free_course_get(callback: CallbackQuery):
    course_id = int(callback.data.split(':')[1])
    course = await _get_course(course_id)
    if not course:
        await callback.answer('⚠️ دوره پیدا نشد. لطفاً دوباره تلاش کن.', show_alert=True)
        return

    if not course.public_channel_post_link:
        await callback.answer('⏳ لینک این دوره هنوز آماده نشده. به‌زودی در دسترس قرار می‌گیره.', show_alert=True)
        return

    is_favorited = await _is_favorited(callback.from_user.id, 'course', course_id)
    text = (
        f'🆓 این دوره کاملاً رایگانه!\n\n'
        f'🎧 از لینک زیر می‌تونی پادکست رو در کانال MedCardy ببینی و گوش بدی:\n\n'
        f'{course.public_channel_post_link}\n\n'
        f'💡 می‌تونی این دوره رو به علاقه‌مندی‌هات اضافه کنی تا بعداً راحت‌تر پیداش کنی.'
    )
    keyboard = await free_course_received_keyboard(course_id, is_favorited)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == 'back:categories')
async def back_to_categories(callback: CallbackQuery):
    categories = await _get_active_categories()
    if not categories:
        await callback.message.edit_text('📭 در حال حاضر دوره‌ای در دسترس نیست.')
        await callback.answer()
        return
    await callback.message.edit_text(
        '📚 دسته‌بندی مورد نظرت رو انتخاب کن:',
        reply_markup=categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(F.data == 'back:lessons')
async def back_to_lessons(callback: CallbackQuery):
    cat_id = _user_category_context.get(callback.from_user.id)
    if not cat_id:
        await back_to_categories(callback)
        return
    lessons = await _get_lessons_for_category(cat_id)
    await callback.message.edit_text(
        '📖 درس مورد نظرت رو انتخاب کن:',
        reply_markup=await lessons_keyboard(lessons),
    )
    await callback.answer()


@router.callback_query(F.data == 'back:courses')
async def back_to_courses(callback: CallbackQuery):
    lesson_id = _user_lesson_context.get(callback.from_user.id)
    if not lesson_id:
        await back_to_categories(callback)
        return
    courses = await _get_courses_for_lesson(lesson_id)
    await callback.message.edit_text(
        '🎧 دوره مورد نظرت رو انتخاب کن:',
        reply_markup=await courses_keyboard(courses),
    )
    await callback.answer()


@router.callback_query(F.data == 'main_menu')
async def back_to_main_inline(callback: CallbackQuery):
    from apps.telegram_bot.utils import aget_bot_message
    text = await aget_bot_message('start_message', default='⬇️ یه گزینه انتخاب کن:')
    await callback.message.answer(text, reply_markup=await main_menu_keyboard())
    await callback.message.delete()
    await callback.answer()


# ─── Favorites callbacks ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith('add_fav:'))
async def add_to_favorites(callback: CallbackQuery):
    parts = callback.data.split(':')
    obj_type, obj_id_str = parts[1], parts[2]
    obj_id = int(obj_id_str) if obj_id_str.isdigit() else 0
    title = await _get_object_title(obj_type, obj_id)
    await _add_favorite(callback.from_user.id, obj_type, obj_id, title)
    await callback.answer('❤️ به علاقه‌مندی‌ها اضافه شد!', show_alert=False)


@router.callback_query(F.data.startswith('rem_fav:'))
async def remove_from_favorites(callback: CallbackQuery):
    parts = callback.data.split(':')
    obj_type, obj_id_str = parts[1], parts[2]
    obj_id = int(obj_id_str) if obj_id_str.isdigit() else 0
    await _remove_favorite(callback.from_user.id, obj_type, obj_id)
    await callback.answer('💔 از علاقه‌مندی‌ها حذف شد.', show_alert=False)


# ─── DB helpers ──────────────────────────────────────────────────────────────

@sync_to_async
def _get_active_categories():
    from apps.catalog.models import Category
    return list(Category.objects.filter(is_active=True, parent=None).order_by('sort_order', 'title'))


@sync_to_async
def _get_lessons_for_category(cat_id: int):
    from apps.catalog.models import Lesson
    return list(Lesson.objects.filter(category_id=cat_id, is_active=True).order_by('sort_order', 'title'))


@sync_to_async
def _get_courses_for_lesson(lesson_id: int):
    from apps.courses.models import Course
    return list(
        Course.objects.filter(lesson_id=lesson_id, status=Course.STATUS_ACTIVE)
        .order_by('sort_order', 'title')
    )


@sync_to_async
def _get_course(course_id: int):
    from apps.courses.models import Course
    try:
        return Course.objects.select_related('category', 'lesson').get(id=course_id)
    except Course.DoesNotExist:
        return None


@sync_to_async
def _is_favorited(telegram_id: int, obj_type: str, obj_id: int) -> bool:
    from apps.users.models import TelegramUser
    from apps.favorites.models import Favorite
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return Favorite.objects.filter(user=user, object_type=obj_type, object_id=obj_id).exists()
    except TelegramUser.DoesNotExist:
        return False


@sync_to_async
def _add_favorite(telegram_id: int, obj_type: str, obj_id: int, title: str = ''):
    from apps.users.models import TelegramUser
    from apps.favorites.models import Favorite
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        Favorite.objects.get_or_create(
            user=user, object_type=obj_type, object_id=obj_id,
            defaults={'title_snapshot': title}
        )
    except TelegramUser.DoesNotExist:
        pass


@sync_to_async
def _remove_favorite(telegram_id: int, obj_type: str, obj_id: int):
    from apps.users.models import TelegramUser
    from apps.favorites.models import Favorite
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        Favorite.objects.filter(user=user, object_type=obj_type, object_id=obj_id).delete()
    except TelegramUser.DoesNotExist:
        pass


@sync_to_async
def _get_object_title(obj_type: str, obj_id: int) -> str:
    if obj_type == 'course':
        from apps.courses.models import Course
        try:
            return Course.objects.get(id=obj_id).title
        except Course.DoesNotExist:
            return ''
    elif obj_type == 'service_order':
        from apps.orders.models import ServiceOrder
        try:
            return ServiceOrder.objects.get(id=obj_id).title
        except ServiceOrder.DoesNotExist:
            return ''
    return ''


def _build_course_detail_text(course) -> str:
    type_label = get_status_label('status.course_type', course.course_type)
    status_label = get_status_label('status.course', course.status)

    lines = [
        f'🎧 <b>{course.title}</b>',
        f'',
        f'🏷️ نوع: {type_label}',
    ]
    if course.category:
        lines.append(f'📂 دسته‌بندی: {course.category.title}')
    if course.lesson:
        lines.append(f'📖 درس: {course.lesson.title}')
    if course.university:
        lines.append(f'🏫 دانشگاه: {course.university}')
    if course.pages_count:
        lines.append(f'📄 تعداد صفحات: {course.pages_count}')
    if course.duration_text:
        lines.append(f'⏱️ مدت زمان: {course.duration_text}')
    if course.episodes_count:
        lines.append(f'🎵 تعداد قسمت‌ها: {course.episodes_count}')
    if course.short_description:
        lines.append(f'')
        lines.append(f'📝 {course.short_description}')
    if course.course_type == 'paid' and course.price_toman:
        lines.append(f'')
        lines.append(f'💰 <b>قیمت: {format_toman(course.price_toman)}</b>')
    lines.append(f'')
    lines.append(f'◉ وضعیت: {status_label}')
    return '\n'.join(lines)
