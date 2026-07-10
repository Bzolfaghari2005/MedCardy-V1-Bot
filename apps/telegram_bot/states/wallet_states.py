from aiogram.fsm.state import State, StatesGroup


class WalletStates(StatesGroup):
    waiting_custom_amount = State()
