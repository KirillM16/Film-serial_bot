import config
import random
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from logic import MovieDatabase


bot = telebot.TeleBot(config.API_TOKEN)
db = MovieDatabase("movie_database.db")

favorites_dict = {}


def send_info(message, row, show_favorite_button=True):
    info = f"""
📍Название фильма: {row[2]}
📍Год: {row[3]}
📍Жанр: {row[4]}
📍Рейтинг IMDB: {row[5]}

🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻
{row[6]}
"""
    if row[1]:
        bot.send_photo(message.chat.id, row[1])

    markup = add_to_favorite(row[0]) if show_favorite_button else None
    bot.send_message(message.chat.id, info, reply_markup=markup)


def add_to_favorite(movie_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(
            "Добавить фильм в избранное 🌟",
            callback_data=f"favorite_{movie_id}"
        )
    )
    return markup


def remove_from_favorite(movie_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(
            "Удалить из избранного ❌",
            callback_data=f"unfavorite_{movie_id}"
        )
    )
    return markup


def main_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("/random"),
        KeyboardButton("/top"),
        KeyboardButton("/favorites")
    )
    markup.add(
        KeyboardButton("/random_favorite"),
        KeyboardButton("/clear_favorites")
    )
    return markup


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("favorite_")
    or call.data.startswith("unfavorite_")
)
def favorite_callback(call):
    action, movie_id = call.data.split("_", 1)
    movie_id = int(movie_id)
    user_id = call.from_user.id

    favorites_dict.setdefault(user_id, [])

    if action == "favorite":
        if movie_id not in favorites_dict[user_id]:
            favorites_dict[user_id].append(movie_id)
            bot.answer_callback_query(call.id, "Фильм добавлен в избранное! ⭐")
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=remove_from_favorite(movie_id)
            )
        else:
            bot.answer_callback_query(
                call.id,
                "Уже в избранном! ⭐",
                show_alert=True
            )

    elif action == "unfavorite":
        if movie_id in favorites_dict[user_id]:
            favorites_dict[user_id].remove(movie_id)
            bot.answer_callback_query(call.id, "Удалено из избранного! ❌")
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=add_to_favorite(movie_id)
            )


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        """Привет! Добро пожаловать в чат-бот для фильмов! 🎥

Команды:
/random — случайный фильм
/top — топ фильмов по рейтингу
/favorites — мои избранные фильмы
/random_favorite — случайный фильм из избранного
/clear_favorites — очистить избранное

Или напишите название фильма для поиска! 🎬""",
        reply_markup=main_markup()
    )


@bot.message_handler(commands=["random"])
def random_movie(message):
    row = db.get_random_movie()

    if row:
        send_info(message, row)
    else:
        bot.send_message(message.chat.id, "База данных пуста 😔")


@bot.message_handler(commands=["top"])
def top_movies(message):
    rows = db.get_top_movies(10)

    if not rows:
        bot.send_message(message.chat.id, "База данных пуста 😔")
        return

    text = "🏆 <b>Топ-10 фильмов по рейтингу:</b>\n\n"

    for i, row in enumerate(rows, start=1):
        text += f"{i}. <b>{row[2]}</b> ({row[3]}) — ⭐ {row[5]}\n"

    bot.send_message(message.chat.id, text, parse_mode="HTML")


@bot.message_handler(commands=["favorites"])
def show_favorites(message):
    user_id = message.from_user.id
    movie_ids = favorites_dict.get(user_id, [])

    if not movie_ids:
        bot.send_message(
            message.chat.id,
            "У вас пока нет избранных фильмов. Добавьте фильмы через кнопку ⭐"
        )
        return

    rows = db.get_movies_by_ids(movie_ids)

    if not rows:
        bot.send_message(message.chat.id, "Фильмы не найдены 😕")
        return

    bot.send_message(
        message.chat.id,
        f"Ваши избранные фильмы ({len(rows)}): 🌟"
    )

    for row in rows:
        send_info(message, row, show_favorite_button=False)


@bot.message_handler(commands=["random_favorite"])
def random_favorite(message):
    user_id = message.from_user.id
    movie_ids = favorites_dict.get(user_id, [])

    if not movie_ids:
        bot.send_message(
            message.chat.id,
            "У вас нет избранных фильмов! Добавьте фильмы через кнопку ⭐"
        )
        return

    movie_id = random.choice(movie_ids)
    row = db.get_movie_by_id(movie_id)

    if row:
        bot.send_message(
            message.chat.id,
            "🎲 Случайный фильм из вашего избранного:"
        )
        send_info(message, row, show_favorite_button=False)
    else:
        bot.send_message(message.chat.id, "Фильм не найден 😕")


@bot.message_handler(commands=["clear_favorites"])
def clear_favorites(message):
    user_id = message.from_user.id

    if favorites_dict.get(user_id):
        favorites_dict[user_id].clear()
        bot.send_message(message.chat.id, "Избранное очищено 🧹")
    else:
        bot.send_message(message.chat.id, "У вас уже нет избранных фильмов.")


@bot.message_handler(func=lambda message: not message.text.startswith("/"))
def search_movie(message):
    row = db.search_movie(message.text)

    if row:
        bot.send_message(message.chat.id, "Конечно. Я знаю этот фильм. 😌")
        send_info(message, row)
    else:
        bot.send_message(message.chat.id, "Я не знаю этот фильм. 😕")


bot.set_my_commands([
    telebot.types.BotCommand("start", "Запустить бота"),
    telebot.types.BotCommand("random", "Случайный фильм"),
    telebot.types.BotCommand("top", "Топ фильмов по рейтингу"),
    telebot.types.BotCommand("favorites", "Мои избранные фильмы"),
    telebot.types.BotCommand("random_favorite", "Случайный фильм из избранного"),
    telebot.types.BotCommand("clear_favorites", "Очистить избранное"),
])


bot.infinity_polling()