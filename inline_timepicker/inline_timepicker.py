import datetime
import logging
import shelve
from dataclasses import dataclass
from typing import Optional, Dict, Union

from aiogram.utils.callback_data import CallbackData, CallbackDataFilter
from aiogram import types

import inline_timepicker.utils as utils
from inline_timepicker.exceptions import (
    NotInitedException,
    WrongCallbackException
)


@dataclass
class InlineTimepickerData():
    min_time: datetime.time
    max_time: datetime.time
    current_time: datetime.time
    minute_step: int
    hour_step: int


class InlineTimepicker:
    _cb_prefix = 'inline_timepicker'
    BASE_CALLBACK = CallbackData(_cb_prefix, 'action', 'data')
    CALLBACK_WRONG_CHOICE = BASE_CALLBACK.new(action='wrong_choice', data='-')
    CALLBACK_HOUR_DECREASE = BASE_CALLBACK.new(action='dec', data='hour')
    CALLBACK_HOUR_INCREASE = BASE_CALLBACK.new(action='inc', data='hour')
    CALLBACK_MINUTE_DECREASE = BASE_CALLBACK.new(action='dec', data='minute')
    CALLBACK_MINUTE_INCREASE = BASE_CALLBACK.new(action='inc', data='minute')
    CALLBACK_SUCCESS = BASE_CALLBACK.new(action='success', data='-')

    def __init__(self):
        self.data = {}

    def _get_user_info(self, chat_id: int) -> Optional[InlineTimepickerData]:
        return self.data.get(chat_id, None)

    def _set_user_info(self, chat_id: int, data: Optional[InlineTimepickerData]):
        self.data[chat_id] = data

    def filter(self, **full_config) -> CallbackDataFilter:
        return InlineTimepicker.BASE_CALLBACK.filter(**full_config)

    def init(self,
             base_time: datetime.time,
             min_time: datetime.time,
             max_time: datetime.time,
             chat_id: Optional[int] = None,
             minute_step: int = 15,
             hour_step: int = 1):

        if chat_id is None:
            chat_id = types.User.get_current().id

        self._set_user_info(
            chat_id,
            InlineTimepickerData(
                min_time, max_time, base_time, minute_step, hour_step
            )
        )

    def is_inited(self, chat_id: Optional[int] = None) -> bool:
        if chat_id is None:
            chat_id = types.User.get_current().id
        return self._get_user_info(chat_id) is not None

    def reset(self, chat_id: Optional[int] = None):
        if chat_id is None:
            chat_id = types.User.get_current().id
        self._set_user_info(chat_id, None)

    def get_keyboard(self, chat_id: Optional[int] = None) -> types.InlineKeyboardMarkup:
        if chat_id is None:
            chat_id = types.User.get_current().id

        if not self.is_inited(chat_id):
            raise NotInitedException('inline_timepicker is not inited properly')

        kb = utils.create_inline_keyboard()
        user_info = self._get_user_info(chat_id)
        curr_date_time = datetime.datetime.now().replace(hour=user_info.current_time.hour, minute=user_info.current_time.minute)
        min_date_time = datetime.datetime.now().replace(hour=user_info.min_time.hour, minute=user_info.min_time.minute)
        max_date_time = datetime.datetime.now().replace(hour=user_info.max_time.hour, minute=user_info.max_time.minute)

        minute_step_date_time = datetime.timedelta(minutes=user_info.minute_step)
        an_hour_date_time = datetime.timedelta(hours=user_info.hour_step)
        rows = [[] for i in range(4)]

        if curr_date_time + an_hour_date_time <= max_date_time:
            rows[0].append(utils.create_inline_callback_button('↑', InlineTimepicker.CALLBACK_HOUR_INCREASE))
        else:
            rows[0].append(utils.create_inline_callback_button(' ', InlineTimepicker.CALLBACK_WRONG_CHOICE))

        if curr_date_time + minute_step_date_time <= max_date_time:
            rows[0].append(utils.create_inline_callback_button('↑', InlineTimepicker.CALLBACK_MINUTE_INCREASE))
        else:
            rows[0].append(utils.create_inline_callback_button(' ', InlineTimepicker.CALLBACK_WRONG_CHOICE))

        if curr_date_time - an_hour_date_time >= min_date_time:
            rows[2].append(utils.create_inline_callback_button('↓', InlineTimepicker.CALLBACK_HOUR_DECREASE))
        else:
            rows[2].append(utils.create_inline_callback_button(' ', InlineTimepicker.CALLBACK_WRONG_CHOICE))

        if curr_date_time - minute_step_date_time >= min_date_time:
            rows[2].append(utils.create_inline_callback_button('↓', InlineTimepicker.CALLBACK_MINUTE_DECREASE))
        else:
            rows[2].append(utils.create_inline_callback_button(' ', InlineTimepicker.CALLBACK_WRONG_CHOICE))

        rows[1].extend([
            utils.create_inline_callback_button(user_info.current_time.hour, InlineTimepicker.CALLBACK_WRONG_CHOICE),
            utils.create_inline_callback_button(user_info.current_time.minute, InlineTimepicker.CALLBACK_WRONG_CHOICE)
        ])
        rows[-1].append(utils.create_inline_callback_button('OK', InlineTimepicker.CALLBACK_SUCCESS))

        for row in rows:
            kb.row(*row)

        return kb

    def handle(self, chat_id: int, callback_data: Union[Dict[str, str], str]) -> Optional[datetime.time]:
        if not self.is_inited(chat_id):
            raise NotInitedException()

        if isinstance(callback_data, str):
            try:
                callback_data = InlineTimepicker.BASE_CALLBACK.parse(callback_data)
            except ValueError:
                raise WrongCallbackException("wrong callback data")

        user_info = self._get_user_info(chat_id)
        action = callback_data.get('action', None)
        data = callback_data.get('data', None)
        if action is None or data is None:
            raise WrongCallbackException("wrong callback data")

        curr_date_time = datetime.datetime.now().replace(hour=user_info.current_time.hour,
                                                         minute=user_info.current_time.minute)
        minute_step_date_time = datetime.timedelta(minutes=user_info.minute_step)
        hour_step_date_time = datetime.timedelta(hours=user_info.hour_step)

        if action == 'success':
            self.reset(chat_id=chat_id)
            return user_info.current_time

        if action == 'inc':
            if data == 'hour':
                curr_date_time += hour_step_date_time
            elif data == 'minute':
                curr_date_time += minute_step_date_time
        elif action == 'dec':
            if data == 'hour':
                curr_date_time -= hour_step_date_time
            elif data == 'minute':
                curr_date_time -= minute_step_date_time
        else:
            raise WrongCallbackException("wrong callback data")

        curr_time = datetime.time(curr_date_time.hour, curr_date_time.minute)
        if curr_time > user_info.max_time or curr_time < user_info.min_time:
            return

        user_info.current_time = curr_time
        self._set_user_info(chat_id, user_info)
