import asyncio
import logging
import re
import sys
from datetime import datetime

import pytz

try:
    import uvloop
except ModuleNotFoundError:
    pass

from os import getenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from dotenv import load_dotenv

from app import constants as const
from app.actions import ACTIONS
from app.keyboards import cancel_kb, start_kb
from app.models.models import Transaction, User

load_dotenv()

TOKEN = getenv("BOT_TOKEN")


class FormRecord(StatesGroup):
    amount = State()
    category = State()


class NewMonthlyLimit(StatesGroup):
    amount = State()


dp = Dispatcher()
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await User.start_command(message)


@dp.message(F.text.casefold() == ACTIONS[const.CANCEL].lower())
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(const.DIALOG_CANCEL, reply_markup=start_kb)


@dp.message(F.text.lower() == ACTIONS[const.ADD_RECORD].lower())
async def add_new_record(message: types.Message, state: FSMContext):
    await message.answer(const.DIALOG_SPEND, reply_markup=cancel_kb)
    await state.set_state(FormRecord.amount)


@dp.message(FormRecord.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    await Transaction.prepare_amount(message, state)


@dp.message(FormRecord.category)
async def process_category(message: Message, state: FSMContext) -> None:
    await Transaction.add_transaction(message, state)


@dp.message(F.text.lower() == ACTIONS[const.UPDATE_BUDGET].lower())
async def update_budget(message: types.Message):
    buttons = [
        [
            types.InlineKeyboardButton(text=const.DIALOG_CHANGE_LIMIT, callback_data="change_limit"),
        ],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    user = await User.get(telegram_id=message.chat.id)
    await message.answer(f"💳Ліміт: {user.monthly_limit} грн", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "change_limit")
async def process_callback_button0(callback_query: types.CallbackQuery, state):
    await bot.send_message(
        callback_query.message.chat.id,
        text=const.DIALOG_SET_NEW_VALUE,
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(NewMonthlyLimit.amount)


@dp.message(NewMonthlyLimit.amount)
async def process_monthly_amount(message: Message, state: FSMContext) -> None:
    await User.update_monthly_limit(message, state)


@dp.message(F.text.lower() == ACTIONS[const.MONTHLY_COSTS].lower())
async def monthly_costs(message: types.Message):
    buttons = [
        [
            types.InlineKeyboardButton(text="Сьогодні", callback_data="day_analytics"),
            types.InlineKeyboardButton(text="Місяць", callback_data="month_analytics"),
        ],
        [
            types.InlineKeyboardButton(text="CSV звіт за місяць", callback_data="csv_report"),
        ],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Витрати за", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "day_analytics")
async def process_callback_button1(callback_query: types.CallbackQuery):
    await Transaction.day_report(callback_query.message)


@dp.callback_query(lambda c: c.data == "month_analytics")
async def process_callback_button2(callback_query: types.CallbackQuery):
    await Transaction.month_report(callback_query.message)


@dp.callback_query(lambda c: c.data == "csv_report")
async def process_callback_button3(callback_query: types.CallbackQuery):
    await Transaction.csv_month_report(callback_query.message)


@dp.message(F.text.lower() == ACTIONS[const.MONTHLY_ANALYTICS].lower())
async def monthly_costs2(message: types.Message):
    await Transaction.month_analytics(message)


@dp.message(F.text.lower() == ACTIONS[const.ALL_RECORDS].lower())
async def all_records(message: types.Message, state):
    await Transaction.all_records(message, state)


@dp.callback_query(lambda c: re.match(r"record_\d+", c.data))
async def process_callback_button4(callback_query: types.CallbackQuery, _):
    record_id = callback_query.data.split("_")[-1]
    tr = await Transaction.get(id=record_id)

    await tr.delete()
    await callback_query.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.bot.answer_callback_query(
        callback_query.id,
        const.DIALOG_DELETE_RECORD,
    )


@dp.message(F.text.regexp(f".*{const.DIALOG_LEFT_PAGINATION}"))
async def process_callback_button5(message: types.Message, state):
    pagination_num = message.text.split("<-")[0]
    await Transaction.all_records(message, state, pagination_num=pagination_num, next=False)


@dp.message(F.text.regexp(f"{const.DIALOG_RIGHT_PAGINATION}.*"))
async def process_callback_button6(message: types.Message, state):
    pagination_num = message.text.split("->")[-1]
    await Transaction.all_records(message, state, pagination_num=pagination_num)


async def bot_pulling() -> None:
    await dp.start_polling(bot)


async def db_init() -> None:
    from app.models.models import init

    await init()


async def notification_init() -> None:
    from app.models.models import User

    async def _send_message() -> None:
        users = await User.all().values_list("telegram_id", flat=True)
        message = "Привіт☺️\nБули нові витрати💸?"
        for user in users:
            await asyncio.sleep(0)
            try:
                await bot.send_message(str(user), message)
            except Exception as e:
                logging.error(f"Error sending to {user}\n {e}")

        await asyncio.sleep(60 * 60)

    while True:
        await asyncio.sleep(60 * 5)

        kiev_timezone = pytz.timezone("Europe/Kiev")
        current_time_kiev = datetime.now(kiev_timezone)

        mid_st = current_time_kiev.replace(hour=14, minute=0, second=0, microsecond=0)
        mid_et = current_time_kiev.replace(hour=14, minute=30, second=0, microsecond=0)

        night_st = current_time_kiev.replace(hour=21, minute=30, second=0, microsecond=0)
        night_et = current_time_kiev.replace(hour=22, minute=00, second=0, microsecond=0)

        if mid_st <= current_time_kiev < mid_et or night_st <= current_time_kiev < night_et:
            await _send_message()


async def main() -> None:
    await asyncio.gather(bot_pulling(), db_init(), notification_init())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        uvloop.install()
    except NameError:
        pass

    asyncio.run(main())
