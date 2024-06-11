import asyncio
import logging
import os
import tempfile

import matplotlib.pyplot as plt
import pandas as pd
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from dotenv import dotenv_values
from tortoise import Model, Tortoise, fields, run_async
from tortoise.functions import Sum

from app import constants as const
from app.keyboards import cancel_kb, process_pagination_keyboard, start_kb
from app.utils import CategoriesSimilarity, get_this_day_filter, get_this_month_filter

env_vars = dotenv_values(".env")


class User(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.IntField(unique=True, null=False)
    monthly_limit = fields.FloatField(default=0.0)

    @classmethod
    async def start_command(cls, message: Message):
        await cls.get_or_create(telegram_id=message.chat.id)
        await message.answer(const.DIALOG_WHAT_DOING, reply_markup=start_kb)

    @classmethod
    async def update_monthly_limit(cls, message: Message, state: FSMContext):
        await state.update_data(amount=message.text)
        data = await state.get_data()
        await state.clear()

        user = await cls.get(telegram_id=message.chat.id)
        user.monthly_limit = data["amount"]
        await user.save()
        await message.answer(
            f"✅ Місячний ліміт оновленно до {message.text} грн",
            reply_markup=start_kb,
        )


class Transaction(Model):
    __tablename__ = "transactions"

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="users")
    amount = fields.DecimalField(null=False, max_digits=8, decimal_places=2)
    category = fields.TextField(null=False)
    description = fields.TextField(null=False)
    date = fields.DatetimeField(auto_now_add=True)

    @classmethod
    async def all_records(cls, message: Message, state: FSMContext, pagination_num=1, next=True):
        pagination_num = int(pagination_num)
        limit = 4
        offset = (pagination_num - 1) * 4
        records = await cls.filter(user__telegram_id=message.chat.id).order_by("-date").limit(limit).offset(offset)
        if len(records) == 0:
            await message.answer(const.DIALOG_NO_RECORDS, reply_markup=start_kb)
            return

        for r in records:
            buttons = [
                [
                    types.InlineKeyboardButton(
                        text="Видалити",
                        callback_data=f"record_{r.id}",
                        resize_keyboard=False,
                    ),
                ]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=False)
            await message.answer(
                f'| Дата ->{r.date.strftime("%d:%m:%Y")}|\n| {r.category} {float(r.amount)}грн',
                reply_markup=keyboard,
            )
        if next:
            next = pagination_num + 1 if len(records) > 0 else pagination_num
            prev = pagination_num - 1 if next == pagination_num else pagination_num
            await message.answer("------", reply_markup=process_pagination_keyboard(prev, next))
        else:
            prev = 1 if pagination_num == 1 else pagination_num - 1
            current = 2 if pagination_num == 1 else pagination_num
            await message.answer("------", reply_markup=process_pagination_keyboard(prev, current))

    @classmethod
    async def prepare_amount(cls, message: Message, state: FSMContext):
        from main import FormRecord

        try:
            amount = float(message.text)
        except ValueError:
            await message.answer(const.DIALOG_OLYX, reply_markup=cancel_kb)
            await state.set_state(FormRecord.amount)
            return

        await state.update_data(amount=amount)
        text = const.DIALOG_WHAT_CATEGORY
        await message.answer(text, reply_markup=cancel_kb)
        await state.set_state(FormRecord.category)

    @classmethod
    async def prepare_category(cls, message: Message, state: FSMContext):
        from main import FormRecord

        await state.update_data(category=message.text)
        await message.answer(const.DIALOG_DESCRIBE_CATEGORY, reply_markup=cancel_kb)
        await state.set_state(FormRecord.description)

    @classmethod
    async def add_transaction(cls, message: Message, state: FSMContext):
        try:
            await state.update_data(description=message.text)
            data = await state.get_data()
            user = await User.get_or_none(telegram_id=message.chat.id)
            await Transaction.create(**data, user_id=user.id)
            await state.clear()
            await message.answer(const.DIALOG_SUCCESS_ADD, reply_markup=start_kb)
        except Exception as e:
            logging.error(e)
            await message.answer(const.DIALOG_DECLINE_ADD, reply_markup=start_kb)

    @classmethod
    async def month_report(cls, message: Message):
        user = await User.get(telegram_id=message.chat.id)
        month_filter = get_this_month_filter()
        res = (
            await cls.filter(user_id=user.id, **month_filter)
            .annotate(sum=Sum("amount"))
            .group_by("user_id")
            .values("user_id", "sum")
        )
        res = 0 if len(res) == 0 else float(res[0]["sum"])

        if res == 0:
            text = "Немає даних"

        if user.monthly_limit < res:
            text = (
                f"❗️Ви перевищили витрати на місяць біль ніж на {res - user.monthly_limit} грн\n"
                f"💰Ліміт: {user.monthly_limit} грн\n"
                f"💸Витрачено: {res} грн"
            )

        if user.monthly_limit > res:
            text = (
                f"💸За місяць витрачено {res} грн"
                f"\n⚖️ {round(res / user.monthly_limit * 100, 2)}% від вашого місячного ліміту"
            )
        await message.answer(text, reply_markup=start_kb)

    @classmethod
    async def csv_month_report(cls, message: Message):
        user = await User.get(telegram_id=message.chat.id)
        month_filter = get_this_month_filter()
        res = await cls.filter(user_id=user.id, **month_filter).values("date", "amount", "category", "description")
        await asyncio.sleep(0)
        df = pd.DataFrame(res)

        if len(df) == 0:
            await message.answer("Немає даних!")
            return

        df["date"] = df["date"].dt.strftime("%d, %m, %Y")
        df["amount"] = df["amount"].astype(float)
        df["amount"] = df["amount"].round(2)
        df.rename(
            columns={
                "date": "Дата",
                "amount": "Витрати",
                "category": "Категорія",
                "description": "Опис",
            },
            inplace=True,
        )
        await asyncio.sleep(0)
        temp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        await message.answer_document(FSInputFile(temp_file.name, os.path.split(temp_file.name)[1]))
        os.remove(temp_file.name)

    @classmethod
    async def day_report(cls, message: Message):
        user = await User.get(telegram_id=message.chat.id)
        day_filter = get_this_day_filter()
        res = (
            await cls.filter(user_id=user.id, **day_filter)
            .annotate(sum=Sum("amount"))
            .group_by("user_id")
            .values("user_id", "sum")
        )

        res = 0 if len(res) == 0 else float(res[0]["sum"])
        text = f"💸За сьогодні витрачено {res} грн"
        await message.answer(text, reply_markup=start_kb)

    @classmethod
    async def month_analytics(cls, message: Message):
        user = await User.get(telegram_id=message.chat.id)
        month_filter = get_this_month_filter()
        transactions = await Transaction.filter(user_id=user.id, **month_filter)

        if not transactions:
            await message.answer(const.DIALOG_NO_TRANSACTION, reply_markup=start_kb)
            return

        cat_names = await Transaction.filter(user_id=user.id).values_list("category", flat=True)
        cs = CategoriesSimilarity(words=set(cat_names))
        categories = cs.process()

        # Aggregate data based on categories
        category_sums = {}
        for transaction in transactions:
            await asyncio.sleep(0)
            cat = transaction.category
            for key, values in categories.items():
                if cat in values:
                    cat = key
                    break

            category_sums[cat] = category_sums.get(cat, 0) + float(transaction.amount)

        # Generate a pie chart
        fig, ax = plt.subplots()
        ax.pie(
            category_sums.values(),
            labels=category_sums.keys(),
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.axis("equal")  # Equal aspect ratio ensures pie is drawn as a circle.

        await asyncio.sleep(0)
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        plt.savefig(temp_file.name)
        temp_file.close()
        await message.answer_photo(photo=FSInputFile(temp_file.name, os.path.split(temp_file.name)[1]))
        os.remove(temp_file.name)


async def init():
    db_user = env_vars["DB_USER"]
    password = env_vars["DB_PASSWORD"]
    host = env_vars["DB_HOST"]
    db_name = env_vars["DB_NAME"]

    if int(env_vars["RUN_DOCKER"]):
        url = f"postgres://{db_user}:{password}@{host}:5432/{db_name}"
    else:
        url = f"postgres://{db_user}:{password}@localhost:5432/{db_name}"

    await Tortoise.init(db_url=url, modules={"models": ["app.models.models"]})
    await Tortoise.generate_schemas()


if __name__ == "__main__":
    run_async(init())
