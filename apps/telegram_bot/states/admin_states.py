from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_channel_link = State()
    waiting_reject_reason = State()
