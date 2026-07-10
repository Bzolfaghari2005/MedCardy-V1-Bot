from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from apps.telegram_bot.utils import aget_label, get_label


async def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=await aget_label('menu.courses')),
                KeyboardButton(text=await aget_label('menu.order')),
            ],
            [
                KeyboardButton(text=await aget_label('menu.my_courses')),
                KeyboardButton(text=await aget_label('menu.my_services')),
            ],
            [
                KeyboardButton(text=await aget_label('menu.favorites')),
                KeyboardButton(text=await aget_label('menu.wallet')),
            ],
            [
                KeyboardButton(text=await aget_label('menu.support')),
                KeyboardButton(text=await aget_label('menu.help')),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )


async def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=await aget_label('btn.back')),
            KeyboardButton(text=await aget_label('btn.back_to_main')),
        ]],
        resize_keyboard=True,
    )


async def back_to_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=await aget_label('btn.back_to_main'))]],
        resize_keyboard=True,
    )


async def skip_keyboard(back: bool = True) -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text=await aget_label('btn.skip'))]
    if back:
        row.append(KeyboardButton(text=await aget_label('btn.back')))
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


def categories_keyboard(categories) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=cat.title, callback_data=f'cat:{cat.id}')]
        for cat in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def lessons_keyboard(lessons) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=les.title, callback_data=f'les:{les.id}')]
        for les in lessons
    ]
    buttons.append([InlineKeyboardButton(
        text=await aget_label('btn.back'), callback_data='back:categories',
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def courses_keyboard(courses) -> InlineKeyboardMarkup:
    free_prefix = await aget_label('status.course_type.free')
    paid_prefix = await aget_label('status.course_type.paid')
    buttons = []
    for course in courses:
        if course.course_type == 'free':
            label = f'{free_prefix} {course.title}'
        else:
            label = f'{paid_prefix} {course.title}'
        buttons.append([InlineKeyboardButton(text=label, callback_data=f'course:{course.id}')])
    buttons.append([InlineKeyboardButton(
        text=await aget_label('btn.back'), callback_data='back:lessons',
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def course_detail_keyboard(course, is_favorited: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if course.course_type == 'free':
        buttons.append([InlineKeyboardButton(
            text=await aget_label('btn.free_get'), callback_data=f'free_get:{course.id}',
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text=await aget_label('btn.buy'), callback_data=f'buy_course:{course.id}',
        )])

    fav_key = 'btn.remove_favorite' if is_favorited else 'btn.add_favorite'
    fav_data = f'rem_fav:course:{course.id}' if is_favorited else f'add_fav:course:{course.id}'
    buttons.append([InlineKeyboardButton(text=await aget_label(fav_key), callback_data=fav_data)])
    buttons.append([InlineKeyboardButton(
        text=await aget_label('btn.back'), callback_data='back:courses',
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def free_course_received_keyboard(course_id: int, is_favorited: bool = False) -> InlineKeyboardMarkup:
    fav_key = 'btn.remove_favorite' if is_favorited else 'btn.add_favorite'
    fav_data = f'rem_fav:course:{course_id}' if is_favorited else f'add_fav:course:{course_id}'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await aget_label(fav_key), callback_data=fav_data)],
        [InlineKeyboardButton(
            text=await aget_label('btn.view_other_courses'), callback_data='back:categories',
        )],
        [InlineKeyboardButton(
            text=await aget_label('btn.back_to_main'), callback_data='main_menu',
        )],
    ])


async def payment_link_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=await aget_label('btn.pay_online'), url=payment_url)],
    ])


async def manual_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await aget_label('btn.submit_receipt'),
            callback_data=f'pay:submit_receipt:{payment_id}',
        )],
    ])


async def order_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=await aget_label('btn.individual_order')),
                KeyboardButton(text=await aget_label('btn.group_order')),
            ],
            [KeyboardButton(text=await aget_label('btn.pricing_guide'))],
            [KeyboardButton(text=await aget_label('btn.back'))],
        ],
        resize_keyboard=True,
    )


async def confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=await aget_label('btn.confirm_pay')),
            KeyboardButton(text=await aget_label('btn.cancel')),
        ]],
        resize_keyboard=True,
    )


async def wallet_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=await aget_label('btn.charge_wallet'))],
            [KeyboardButton(text=await aget_label('btn.transactions'))],
            [KeyboardButton(text=await aget_label('btn.back_to_main'))],
        ],
        resize_keyboard=True,
    )


async def wallet_amounts_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=await aget_label('wallet.amount.100000')),
                KeyboardButton(text=await aget_label('wallet.amount.250000')),
            ],
            [
                KeyboardButton(text=await aget_label('wallet.amount.500000')),
                KeyboardButton(text=await aget_label('wallet.amount.1000000')),
            ],
            [KeyboardButton(text=await aget_label('btn.custom_amount'))],
            [KeyboardButton(text=await aget_label('btn.back'))],
        ],
        resize_keyboard=True,
    )


async def group_join_keyboard(order_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await aget_label('btn.join_and_pay'), callback_data=f'join_group:{order_code}',
        )],
        [InlineKeyboardButton(
            text=await aget_label('btn.add_favorite'), callback_data=f'add_fav:service_order:{order_code}',
        )],
    ])


async def pay_my_share_keyboard(order_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=await aget_label('btn.pay_my_share'), callback_data=f'join_group:{order_code}',
        )],
    ])


async def select_category_inline(categories) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=cat.title, callback_data=f'ord_cat:{cat.id}')]
        for cat in categories
    ]
    buttons.append([InlineKeyboardButton(
        text=await aget_label('btn.back'), callback_data='cancel_order',
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def select_lesson_inline(lessons) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=les.title, callback_data=f'ord_les:{les.id}')]
        for les in lessons
    ]
    buttons.append([InlineKeyboardButton(
        text=await aget_label('btn.back'), callback_data='cancel_order',
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def confirm_pages_inline(suggested_pages: int) -> InlineKeyboardMarkup:
    confirm_prefix = await aget_label('btn.confirm_pages')
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f'{confirm_prefix} ({suggested_pages} صفحه)',
            callback_data='ord_pages:confirm',
        )],
        [InlineKeyboardButton(
            text=await aget_label('btn.edit_pages'),
            callback_data='ord_pages:edit',
        )],
        [InlineKeyboardButton(
            text=await aget_label('btn.back'), callback_data='cancel_order',
        )],
    ])


async def select_service_tier_inline(pages: int) -> InlineKeyboardMarkup:
    from apps.orders.models import ServiceOrder
    from apps.orders.services import (
        calculate_individual_price,
        get_full_price_per_page,
        get_review_price_per_page,
    )
    from apps.telegram_bot.utils import format_toman

    review_price = calculate_individual_price(pages, ServiceOrder.TIER_REVIEW)
    full_price = calculate_individual_price(pages, ServiceOrder.TIER_FULL)
    review_label = await aget_label('tier.review_inline')
    full_label = await aget_label('tier.full_inline')
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f'{review_label} — {format_toman(review_price)} ({format_toman(get_review_price_per_page())}/صفحه)',
            callback_data='ord_tier:review',
        )],
        [InlineKeyboardButton(
            text=f'{full_label} — {format_toman(full_price)} ({format_toman(get_full_price_per_page())}/صفحه)',
            callback_data='ord_tier:full',
        )],
        [InlineKeyboardButton(
            text=await aget_label('btn.back'), callback_data='cancel_order',
        )],
    ])


async def select_service_tier_group_inline(pages: int) -> InlineKeyboardMarkup:
    from apps.orders.models import ServiceOrder
    from apps.orders.services import calculate_group_price
    from apps.telegram_bot.utils import format_toman

    review_price = calculate_group_price(pages, ServiceOrder.TIER_REVIEW)
    full_price = calculate_group_price(pages, ServiceOrder.TIER_FULL)
    review_label = await aget_label('tier.review_inline')
    full_label = await aget_label('tier.full_inline')
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f'{review_label} — {format_toman(review_price)}/نفر',
            callback_data='ord_tier:review',
        )],
        [InlineKeyboardButton(
            text=f'{full_label} — {format_toman(full_price)}/نفر',
            callback_data='ord_tier:full',
        )],
        [InlineKeyboardButton(
            text=await aget_label('btn.back'), callback_data='cancel_order',
        )],
    ])
