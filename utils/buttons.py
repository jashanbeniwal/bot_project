from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def mk_buttons(rows):
    """
    rows: list of list of tuples (text, callback_data)
    """
    keyboard = []
    for row in rows:
        r = [InlineKeyboardButton(text, callback_data=data) for text, data in row]
        keyboard.append(r)
    return InlineKeyboardMarkup(keyboard)
