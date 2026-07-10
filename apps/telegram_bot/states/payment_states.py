from aiogram.fsm.state import State, StatesGroup


class PaymentReceiptStates(StatesGroup):
    waiting_receipt = State()
