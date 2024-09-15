import bot_secrets
# bot_secrets.BOT_TOKEN
import telebot
from telebot import types

API_TOKEN = bot_secrets.BOT_TOKEN

bot = telebot.TeleBot(API_TOKEN)

user_data = {}

currency_rates = {
    'ILS': 1.0,
    'EUR': 3.91,
    'USD': 3.57,
    'HUF': 0.011,
    'RON': 0.8,
    'GBP': 4.69,
    'AED': 0.97,
    'ARS': 0.01,
    'CAD': 2.67,
    'CHF': 4.21,
    'CNY': 0.49,
    'CZK': 0.16,
    'INR': 0.043,
    'JPY': 0.026,
    'KRW': 0.0027,
    'PEN': 1.05,
    'THB': 0.1
}

currency_names_flags = {
    'ILS': 'Israeli Shekel 🇮🇱',
    'EUR': 'Euro 🇪🇺',
    'USD': 'US Dollar 🇺🇸',
    'HUF': 'Hungarian Forint 🇭🇺',
    'RON': 'Romanian Leu 🇷🇴',
    'GBP': 'British Pound 🇬🇧',
    'AED': 'UAE Dirham 🇦🇪',
    'ARS': 'Argentine Peso 🇦🇷',
    'CAD': 'Canadian Dollar 🇨🇦',
    'CHF': 'Swiss Franc 🇨🇭',
    'CNY': 'Chinese Yuan 🇨🇳',
    'CZK': 'Czech Koruna 🇨🇿',
    'INR': 'Indian Rupee 🇮🇳',
    'JPY': 'Japanese Yen 🇯🇵',
    'KRW': 'South Korean Won 🇰🇷',
    'PEN': 'Peruvian Sol 🇵🇪',
    'THB': 'Thai Baht 🇹🇭'
}

sorted_currencies = ['ILS', 'EUR', 'USD', 'HUF', 'RON', 'GBP'] + sorted(
    [k for k in currency_rates if k not in ['ILS', 'EUR', 'USD', 'HUF', 'RON', 'GBP']])


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data.clear()
    user_data['messages'] = []
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for currency in sorted_currencies[:6]:
        markup.add(types.KeyboardButton(f"{currency_names_flags[currency]}"))
    btn_more = types.KeyboardButton('More')
    markup.add(btn_more)
    msg = bot.send_message(message.chat.id, "Select the currency you want to convert from:", reply_markup=markup)
    user_data['messages'].append(msg.message_id)
    user_data['messages'].append(message.message_id)


@bot.message_handler(func=lambda message: 'More' in message.text)
def show_more_currencies(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for currency in sorted_currencies[6:]:
        markup.add(types.KeyboardButton(f"{currency_names_flags[currency]}"))
    msg = bot.send_message(message.chat.id, "Select the currency you want to convert from:", reply_markup=markup)
    user_data['messages'].append(msg.message_id)
    user_data['messages'].append(message.message_id)


@bot.message_handler(func=lambda message: 'from_currency' not in user_data and any(
    currency in message.text for currency in currency_names_flags.values()))
def process_from_currency(message):
    selected_currency = next(key for key, value in currency_names_flags.items() if value in message.text)
    user_data['from_currency'] = selected_currency
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for currency in sorted_currencies[:6]:
        markup.add(types.KeyboardButton(f"{currency_names_flags[currency]}"))
    btn_more = types.KeyboardButton('More')
    markup.add(btn_more)
    msg = bot.send_message(message.chat.id,
                           f"Select the currency you want to convert to from {currency_names_flags[selected_currency]}:",
                           reply_markup=markup)
    user_data['messages'].append(msg.message_id)
    user_data['messages'].append(message.message_id)


@bot.message_handler(func=lambda message: 'from_currency' in user_data and 'to_currency' not in user_data and any(
    currency in message.text for currency in currency_names_flags.values()))
def process_to_currency(message):
    selected_currency = next(key for key, value in currency_names_flags.items() if value in message.text)
    user_data['to_currency'] = selected_currency
    delete_previous_messages(message)
    markup = types.ForceReply()
    msg = bot.send_message(message.chat.id,
                           f"Please enter the amount to convert from {currency_names_flags[user_data['from_currency']]} to {currency_names_flags[selected_currency]}:",
                           reply_markup=markup)
    user_data['messages'].append(msg.message_id)


@bot.message_handler(
    func=lambda message: 'from_currency' in user_data and 'to_currency' in user_data and message.text.replace('.', '',
                                                                                                              1).isdigit())
def process_amount(message):
    user_data['messages'].append(message.message_id)
    amount = float(message.text)
    from_currency = user_data['from_currency']
    to_currency = user_data['to_currency']

    converted_amount = amount * (currency_rates[from_currency] / currency_rates[to_currency])

    bot.send_message(message.chat.id,
                     f"{amount} {currency_names_flags[from_currency]} is {converted_amount:.2f} {currency_names_flags[to_currency]}")
    user_data['messages'].append(message.message_id)  # Add the user's message to delete list
    delete_previous_messages(message)  # Delete messages after showing the result


def delete_previous_messages(message):
    for msg_id in user_data.get('messages', []):
        try:
            bot.delete_message(message.chat.id, msg_id)
        except Exception as e:
            print(f"Failed to delete message {msg_id}: {e}")
    user_data['messages'] = []


bot.polling()
