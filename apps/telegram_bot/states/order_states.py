from aiogram.fsm.state import State, StatesGroup


class IndividualOrderStates(StatesGroup):
    waiting_title = State()
    waiting_category = State()
    waiting_lesson = State()
    waiting_university = State()
    waiting_file = State()
    waiting_pages_confirm = State()
    waiting_pages = State()
    waiting_service_tier = State()
    waiting_notes = State()
    waiting_confirm = State()


class GroupOrderStates(StatesGroup):
    waiting_title = State()
    waiting_category = State()
    waiting_lesson = State()
    waiting_university = State()
    waiting_file = State()
    waiting_pages_confirm = State()
    waiting_pages = State()
    waiting_service_tier = State()
    waiting_notes = State()
    waiting_confirm = State()
