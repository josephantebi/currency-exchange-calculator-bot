# import bot_secrets
import telebot
from telebot import types
import schedule
import threading
import time
import requests
import json
import os

# API_TOKEN = bot_secrets.BOT_TOKEN
# API_KEY_EXCHANGE_RATES = bot_secrets.EXCHANGE_RATES
API_TOKEN = os.getenv('BOT_TOKEN')
API_KEY_EXCHANGE_RATES = os.getenv('EXCHANGE_RATES')

bot = telebot.TeleBot(API_TOKEN)
CURRENCY_FILE = "currency_rates.json"
API_URL = f"https://openexchangerates.org/api/latest.json?app_id={API_KEY_EXCHANGE_RATES}"

user_data = {}


def load_currency_rates():
    if os.path.exists(CURRENCY_FILE):
        with open(CURRENCY_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
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


def save_currency_rates():
    with open(CURRENCY_FILE, 'w') as f:
        json.dump(currency_rates, f)

currency_rates = load_currency_rates()


def update_currency_rates():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()

            ils_to_usd = data['rates']['ILS']
            currency_rates.update({
                'ILS': 1.0,
                'EUR': data['rates']['EUR'] / ils_to_usd,
                'USD': data['rates']['USD'] / ils_to_usd,
                'HUF': data['rates']['HUF'] / ils_to_usd,
                'RON': data['rates']['RON'] / ils_to_usd,
                'GBP': data['rates']['GBP'] / ils_to_usd,
                'AED': data['rates']['AED'] / ils_to_usd,
                'ARS': data['rates']['ARS'] / ils_to_usd,
                'CAD': data['rates']['CAD'] / ils_to_usd,
                'CHF': data['rates']['CHF'] / ils_to_usd,
                'CNY': data['rates']['CNY'] / ils_to_usd,
                'CZK': data['rates']['CZK'] / ils_to_usd,
                'INR': data['rates']['INR'] / ils_to_usd,
                'JPY': data['rates']['JPY'] / ils_to_usd,
                'KRW': data['rates']['KRW'] / ils_to_usd,
                'PEN': data['rates']['PEN'] / ils_to_usd,
                'THB': data['rates']['THB'] / ils_to_usd
            })

            save_currency_rates()
    except Exception as e:
        print(f"Error fetching currency rates: {e}")

schedule.every().day.at("08:00").do(update_currency_rates)


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule).start()

currency_names_flags = {
    'ILS': 'ILS 🇮🇱',
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


def delete_duplicate_messages(chat_id):
    unique_messages = []
    for msg_id in user_data.get('messages', []):
        if msg_id not in unique_messages:
            unique_messages.append(msg_id)
        else:
            try:
                print(f"Deleting duplicate message {msg_id}")
                bot.delete_message(chat_id, msg_id)
            except telebot.apihelper.ApiTelegramException as e:
                if e.result_json['description'] == 'Bad Request: message to delete not found':
                    print(f"Message {msg_id} not found. Skipping deletion.")
                else:
                    print(f"Failed to delete message {msg_id}: {e}")

    user_data['messages'] = unique_messages


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data.clear()
    user_data['messages'] = []
    user_message_id = message.message_id

    delete_invalid_and_user_messages(message)

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for currency in sorted_currencies[:6]:
        markup.add(types.KeyboardButton(f"{currency_names_flags[currency]}"))

    btn_more = types.KeyboardButton('More')
    markup.add(btn_more)

    msg = bot.send_message(message.chat.id, "Select the currency you want to convert from:", reply_markup=markup)
    user_data['messages'].append(msg.message_id)

    try:
        if user_message_id:
            bot.delete_message(message.chat.id, user_message_id)
    except Exception as e:
        print(f"Failed to delete message {user_message_id}: {e}")

    delete_duplicate_messages(message.chat.id)


def delete_previous_messages(message):
    user_data.setdefault('messages', [])
    for msg_id in user_data.get('messages', []):
        try:
            print(f"Trying to delete message {msg_id}")
            bot.delete_message(message.chat.id, msg_id)
        except telebot.apihelper.ApiTelegramException as e:
            if e.result_json['description'] == 'Bad Request: message to delete not found':
                print(f"Message {msg_id} not found. Skipping deletion.")
            else:
                print(f"Failed to delete message {msg_id}: {e}")
    user_data['messages'] = []


@bot.message_handler(func=lambda message: 'More' in message.text)
def show_more_currencies(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for currency in sorted_currencies:
        markup.add(types.KeyboardButton(f"{currency_names_flags[currency]}"))
    msg = bot.send_message(message.chat.id, "Select the currency you want to convert from:", reply_markup=markup)
    user_data['messages'].append(msg.message_id)
    user_data['messages'].append(message.message_id)


@bot.message_handler(func=lambda message: 'from_currency' not in user_data and any(
    currency in message.text for currency in currency_names_flags.values()))
def process_from_currency(message):
    user_data.setdefault('messages', [])
    selected_currency = next(key for key, value in currency_names_flags.items() if value in message.text)
    user_data['from_currency'] = selected_currency
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for currency in sorted_currencies:
        markup.add(types.KeyboardButton(f"{currency_names_flags[currency]}"))
    msg = bot.send_message(message.chat.id,
                           f"Select the currency you want to convert to from {currency_names_flags[selected_currency]}:",
                           reply_markup=markup)
    user_data['messages'].append(msg.message_id)
    user_data['messages'].append(message.message_id)


@bot.message_handler(func=lambda message: 'from_currency' in user_data and 'to_currency' not in user_data and any(
    currency in message.text for currency in currency_names_flags.values()))
def process_to_currency(message):
    user_data.setdefault('messages', [])
    selected_currency = next(key for key, value in currency_names_flags.items() if value in message.text)
    user_data['to_currency'] = selected_currency
    user_data['messages'].append(message.message_id)
    delete_previous_messages(message)
    bot.send_message(message.chat.id,
                     f"-------------------------------- \n {currency_names_flags[user_data['from_currency']]} => {currency_names_flags[user_data['to_currency']]}")
    markup = types.ReplyKeyboardRemove()
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
    converted_amount = amount * (currency_rates[to_currency] / currency_rates[from_currency])
    formatted_converted_amount = f"{converted_amount:,.2f}"
    bot.send_message(message.chat.id,
                     f"{amount:,.2f} {currency_names_flags[from_currency]} is {formatted_converted_amount} {currency_names_flags[to_currency]}")
    delete_previous_messages(message)


@bot.message_handler(
    func=lambda message: 'from_currency' in user_data and 'to_currency' in user_data and not message.text.replace('.',
                                                                                                                  '',
                                                                                                                  1).isdigit() and '/switch' not in message.text)
def handle_invalid_input(message):
    user_data.setdefault('messages', [])
    msg = bot.send_message(message.chat.id, "Invalid input, please enter a valid number.")
    user_data['invalid_message'] = msg.message_id
    user_data['messages'].append(message.message_id)
    user_data['messages'].append(msg.message_id)


def delete_invalid_and_user_messages(message):
    user_data.setdefault('messages', [])
    if 'invalid_message' in user_data:
        try:
            bot.delete_message(message.chat.id, user_data['invalid_message'])
        except Exception as e:
            print(f"Failed to delete invalid input message: {e}")
        del user_data['invalid_message']
    delete_previous_messages(message)


@bot.message_handler(commands=['switch'])
def switch_currencies(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Failed to delete /switch message: {e}")

    user_data.setdefault('messages', [])
    if 'from_currency' in user_data and 'to_currency' in user_data:
        user_data['from_currency'], user_data['to_currency'] = user_data['to_currency'], user_data['from_currency']

        bot.send_message(message.chat.id,
                         f"-------------------------------- \n {currency_names_flags[user_data['from_currency']]} => {currency_names_flags[user_data['to_currency']]}")

        markup = types.ReplyKeyboardRemove()
        msg = bot.send_message(message.chat.id,
                               f"Please enter the amount to convert from {currency_names_flags[user_data['from_currency']]} to {currency_names_flags[user_data['to_currency']]}:",
                               reply_markup=markup)
        user_data['messages'].append(msg.message_id)
    else:
        error_msg = bot.send_message(message.chat.id, "No currencies selected to switch.")
        user_data['messages'].append(error_msg.message_id)
        send_welcome(message)
        try:
            bot.delete_message(message.chat.id, error_msg.message_id)
        except Exception as e:
            print(f"Failed to delete No currencies selected to switch message: {e}")


@bot.message_handler(func=lambda message: message.text.replace('.', '', 1).isdigit())
def handle_valid_input(message):
    if 'invalid_message' in user_data:
        try:
            bot.delete_message(message.chat.id, user_data['invalid_message'])
            del user_data['invalid_message']
        except Exception as e:
            print(f"Failed to delete invalid input message: {e}")

    if 'error_message_id' in user_data and 'switch_message_id' in user_data:
        try:
            bot.delete_message(message.chat.id, user_data['error_message_id'])
            bot.delete_message(message.chat.id, user_data['switch_message_id'])
            del user_data['error_message_id']
            del user_data['switch_message_id']
        except Exception as e:
            print(f"Failed to delete error or switch message: {e}")

    process_amount(message)


@bot.message_handler(func=lambda message: message.text.replace('.', '', 1).isdigit())
def handle_valid_input(message):
    if 'invalid_message' in user_data:
        try:
            bot.delete_message(message.chat.id, user_data['invalid_message'])
            del user_data['invalid_message']
        except Exception as e:
            print(f"Failed to delete invalid input message: {e}")
    process_amount(message)

bot.polling()
