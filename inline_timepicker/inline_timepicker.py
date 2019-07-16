import datetime
import logging
import shelve
import utils


class WrongCallbackException(Exception):
    pass


class WrongChoiceCallbackException(Exception):
    pass


class NotInitedException(Exception):
    pass


_INLINE_TIMEPICKER_NAME = 'inline_timepicker'
_SHELVE_DB_NAME = "inline_timepicker_shelve_db"

_MIN_TIME = '_MIN_TIME'
_MAX_TIME = '_MAX_TIME'
_CURRENT_TIME = '_CURRENT_TIME'
_MINUTE_STEP = '_MINUTE_STEP'
_HOUR_STEP = '_HOUR_STEP'

CALLBACK_HOUR_PICKED = '{}_HOUR_'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_HOUR_DECREASE = '{}_HOUR_DEC'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_HOUR_INCREASE = '{}_HOUR_INC'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_MINUTE_PICKED = '{}_MINUTE_'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_MINUTE_DECREASE = '{}_MINUTE_DECR'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_MINUTE_INCREASE = '{}_MINUTE_INC'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_WRONG_CHOICE = '{}_WRONG_CHOICE'.format(_INLINE_TIMEPICKER_NAME)
CALLBACK_SUCCESS = '{}_SUCCESS'.format(_INLINE_TIMEPICKER_NAME)


def _db_read(chat_id, attr_name):
    chat_id = str(chat_id)
    attr_name = str(attr_name)
    try:
        with shelve.open(_SHELVE_DB_NAME) as db:
            t = db[chat_id]
            return t[attr_name]
    except KeyError:
        logging.log(level=logging.CRITICAL, msg='KeyError was raised while getting attribute {} for {}'
                    .format(attr_name, chat_id))


def _db_write(chat_id, attr_name, data):
    chat_id = str(chat_id)
    attr_name = str(attr_name)
    with shelve.open(_SHELVE_DB_NAME) as db:
        if chat_id not in db.keys():
            # first time creation of dictionary
            db[chat_id] = {}
        t = db[chat_id]
        t[attr_name] = data
        db[chat_id] = t


def _init_db(chat_id):
    chat_id = str(chat_id)
    with shelve.open(_SHELVE_DB_NAME) as db:
        db[chat_id] = {}


def _check_callback(cb):
    if cb == CALLBACK_HOUR_DECREASE or \
            cb == CALLBACK_HOUR_INCREASE or \
            cb == CALLBACK_HOUR_PICKED:
        return True
    if cb == CALLBACK_MINUTE_DECREASE or \
            cb == CALLBACK_MINUTE_INCREASE or \
            cb == CALLBACK_MINUTE_PICKED:
        return True
    if cb == CALLBACK_WRONG_CHOICE:
        return True
    if cb == CALLBACK_SUCCESS:
        return True
    return False


def is_inited(chat_id):
    chat_id = str(chat_id)
    with shelve.open(_SHELVE_DB_NAME) as db:
        if chat_id not in db.keys():
            return False

    return _db_read(chat_id, _CURRENT_TIME) is not None


def reset(chat_id):
    chat_id = str(chat_id)
    _db_write(chat_id, _CURRENT_TIME, None)
    _db_write(chat_id, _MIN_TIME, None)
    _db_write(chat_id, _MAX_TIME, None)


def init(chat_id, base_time, min_time, max_time, minute_step=15, hour_step=1):
    _init_db(chat_id)
    _db_write(chat_id, _CURRENT_TIME, base_time)
    _db_write(chat_id, _MIN_TIME, min_time)
    _db_write(chat_id, _MAX_TIME, max_time)
    _db_write(chat_id, _MINUTE_STEP, minute_step)
    _db_write(chat_id, _HOUR_STEP, hour_step)


def get_keyboard(chat_id):
    if not is_inited(chat_id):
        raise NotInitedException('inline_timepicker is not inited properly')

    kb = utils.create_inline_keyboard()
    curr_time = _db_read(chat_id, _CURRENT_TIME)
    min_time = _db_read(chat_id, _MIN_TIME)
    max_time = _db_read(chat_id, _MAX_TIME)
    min_step = _db_read(chat_id, _MINUTE_STEP)

    curr_date_time = datetime.datetime.now().replace(hour=curr_time.hour, minute=curr_time.minute)
    min_date_time = datetime.datetime.now().replace(hour=min_time.hour, minute=min_time.minute)
    max_date_time = datetime.datetime.now().replace(hour=max_time.hour, minute=max_time.minute)

    minute_step_date_time = datetime.timedelta(minutes=min_step)
    an_hour_date_time = datetime.timedelta(hours=1)
    rows = [[] for i in range(4)]

    if curr_date_time + an_hour_date_time <= max_date_time:
        rows[0].append(utils.create_inline_callback_button('↑', CALLBACK_HOUR_INCREASE))
    else:
        rows[0].append(utils.create_inline_callback_button(' ', CALLBACK_WRONG_CHOICE))

    if curr_date_time + minute_step_date_time <= max_date_time:
        rows[0].append(utils.create_inline_callback_button('↑', CALLBACK_MINUTE_INCREASE))
    else:
        rows[0].append(utils.create_inline_callback_button(' ', CALLBACK_WRONG_CHOICE))

    if curr_date_time - an_hour_date_time >= min_date_time:
        rows[2].append(utils.create_inline_callback_button('↓', CALLBACK_HOUR_DECREASE))
    else:
        rows[2].append(utils.create_inline_callback_button(' ', CALLBACK_WRONG_CHOICE))

    if curr_date_time - minute_step_date_time >= min_date_time:
        rows[2].append(utils.create_inline_callback_button('↓', CALLBACK_MINUTE_DECREASE))
    else:
        rows[2].append(utils.create_inline_callback_button(' ', CALLBACK_WRONG_CHOICE))

    rows[1].extend([
        utils.create_inline_callback_button(curr_time.hour, CALLBACK_WRONG_CHOICE),
        utils.create_inline_callback_button(curr_time.minute, CALLBACK_WRONG_CHOICE)
    ])
    rows[-1].append(utils.create_inline_callback_button('OK', CALLBACK_SUCCESS))

    for row in rows:
        kb.row(*row)

    return kb


def is_inline_timepicker_callbackquery(query):
    return _check_callback(query.data)


def handle_callback(chat_id, callback):
    if not is_inited(chat_id):
        raise NotInitedException('inline_timepicker is not inited properly')

    if not _check_callback(callback):
        raise WrongCallbackException('Wrong callback is given for handling')

    if callback == CALLBACK_WRONG_CHOICE:
        return None

    curr_time = _db_read(chat_id, _CURRENT_TIME)
    curr_date_time = datetime.datetime.now().replace(hour=curr_time.hour, minute=curr_time.minute)

    minute_step_date_time = datetime.timedelta(minutes=_db_read(chat_id, _MINUTE_STEP))
    an_hour_date_time = datetime.timedelta(hours=_db_read(chat_id, _HOUR_STEP))

    if callback == CALLBACK_MINUTE_DECREASE:
        curr_date_time = curr_date_time - minute_step_date_time
    if callback == CALLBACK_MINUTE_INCREASE:
        curr_date_time = curr_date_time + minute_step_date_time
    if callback == CALLBACK_HOUR_DECREASE:
        curr_date_time = curr_date_time - an_hour_date_time
    if callback == CALLBACK_HOUR_INCREASE:
        curr_date_time = curr_date_time + an_hour_date_time

    print(type(_db_read(chat_id, _MAX_TIME)))

    curr_time = datetime.time(curr_date_time.hour, curr_date_time.minute)
    if curr_time > _db_read(chat_id, _MAX_TIME) or curr_time < _db_read(chat_id, _MIN_TIME):
        return

    n_time = datetime.time(curr_date_time.hour, curr_date_time.minute)
    _db_write(chat_id, _CURRENT_TIME, n_time)

    if callback == CALLBACK_SUCCESS:
        return curr_time
