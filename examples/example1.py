import logging
import datetime
from typing import Dict

from aiogram import Bot, Dispatcher, executor, types
from inline_timepicker.inline_timepicker import InlineTimepicker

API_TOKEN = 'BOT TOKEN API'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

logging.getLogger('aiogram').setLevel(logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
inline_timepicker = InlineTimepicker()


@dp.message_handler(commands=['time'])
async def send_welcome(message: types.Message):
    inline_timepicker.init(
        datetime.time(12),
        datetime.time(1),
        datetime.time(23),
    )

    await bot.send_message(message.from_user.id,
                           text='test',
                           reply_markup=inline_timepicker.get_keyboard())


@dp.callback_query_handler(inline_timepicker.filter())
async def cb_handler(query: types.CallbackQuery, callback_data: Dict[str, str]):
    await query.answer()
    handle_result = inline_timepicker.handle(query.from_user.id, callback_data)

    if handle_result is not None:
        await bot.edit_message_text(handle_result,
                                    chat_id=query.from_user.id,
                                    message_id=query.message.message_id)
    else:
        await bot.edit_message_reply_markup(chat_id=query.from_user.id,
                                            message_id=query.message.message_id,
                                            reply_markup=inline_timepicker.get_keyboard())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
