from threading import Thread

import telebot
from telebot.types import Message, CallbackQuery

import commands
from postgres_db import PostgresDB
from repository import Repo
from utils import check_status


bot_token = "6161335069:AAFlJOQsPXblOj7H87HlPx69MKviBVOHdy8"
bot = telebot.TeleBot(bot_token, parse_mode="html")
group_list: list[int] = []
pg = PostgresDB()
repo = Repo()


@bot.message_handler(commands=["info"])
def show_info(message: Message):
	if check_status(message):
		commands.info(bot, message)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["start"])
def startsend(message: Message):
	if check_status(message):
		commands.starting_message(bot, message)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["admins"])
def admins(message: Message):
	if check_status(message):
		commands.show_admins(bot, message)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["add_admin"])
def admins(message: Message):
	if check_status(message):
		commands.add_admin(bot, message)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["stop_all"])
def stopall(message: Message):
	if check_status(message):
		commands.stop_all(bot, message)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["start_all"])
def startall(message: Message):
	if check_status(message):
		commands.start_all(bot, message)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["new_post"])
def posts_settings(message: Message):
	if check_status(message):
		commands.get_creation_instruction(message, bot)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["posts"])
def get_posts(message: Message, page=1):
	if check_status(message):
		commands.pagination_posts(bot, message, page)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["chats"])
def chats_settings(message: Message, page=1):
	if check_status(message):
		commands.show_groups(bot, message, page)
	else:
		bot.send_message(message.chat.id, f"У вас нет прав администратора")


@bot.message_handler(commands=["new_chat"])
def new_chat(message: Message):
	if check_status(message):
		commands.add_new_chat(bot, message)
	else:
		bot.send_message(message.from_user.id, f"У вас нет прав администратора")


@bot.message_handler(func=lambda message: message.forward_from_chat is not None)
def add_new_channel(message: Message):
	if message.forward_from_chat.type == "channel":
		commands.add_channel(message, bot)


@bot.message_handler(content_types=["new_chat_members"])
def add_new_chat(message: Message):
	if check_status(message, forward_chat=True):
		commands.add_group(message, bot)
	else:
		pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("deladmin"))
def admin_callback(call: CallbackQuery):
	func, user_id = call.data.split("_")
	commands.del_admin(bot, call.message, int(user_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin"))
def admin_callback(call: CallbackQuery):
	func, user_id = call.data.split("_")
	commands.one_admin(bot, call.message, int(user_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith("clear"))
def clear(call: CallbackQuery):
	func, m1, m2 = call.data.split("_")
	m3 = [m1, m2]
	commands.clearing(bot, call.message, m3)


@bot.callback_query_handler(func=lambda call: call.data.startswith("startsend"))
def startsend(call: CallbackQuery):
	func, post_id = call.data.split("_")
	commands.start_sending_post(bot, call.message, int(post_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith("stopsend"))
def stopsend(call: CallbackQuery):
	func, post_id = call.data.split("_")
	commands.stop_sending_post(bot, call.message, int(post_id))


@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def adding_channel(call: CallbackQuery):
	commands.channel_request(bot, call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("unit"))
def get_unit(call: CallbackQuery):
	func, unit, message_id, message_info_id = call.data.split("_")
	commands.interval_handler(call.message, bot, unit, int(message_id), int(message_info_id))


@bot.callback_query_handler(func=lambda call: "stop" in call.data)
def stop_group_adding(call: CallbackQuery):
	group, func, message_id, message_info_id = call.data.split("_")
	if group_list == 0:
		bot.send_message(call.message.chat.id, "Нужна минимум одна группа для отправки")
	else:
		for mess in group_list:
			bot.delete_message(call.message.chat.id, mess)
		group_list.clear()
		commands.unit_handler(bot, call.message, int(message_id), int(message_info_id))


@bot.callback_query_handler(func=lambda call: "hide" in call.data)
def hide_post(call: CallbackQuery):
	bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: "delete" in call.data)
def delete_posts(call: CallbackQuery):
	func, tt, _id = call.data.split('_')
	if tt == "post":
		commands.delete_post(bot, call.message, int(_id))
	else:
		commands.delete_group(bot, call.message, int(_id))


@bot.callback_query_handler(func=lambda call: "_group" in call.data or "_post" in call.data)
def get_one_post(call: CallbackQuery):
	if "_group-get" in call.data:
		group_id, func = call.data.split("_")
		group = repo.get_group(int(group_id))
		commands.send_group(bot, call.message, group)
	elif "_group" in call.data:
		group_id, func = call.data.split("_")
		title = commands.add_group_to_np(int(group_id))
		if title:
			messag = bot.send_message(chat_id=call.message.chat.id, text=f"Добавлена группа: {title}")
			group_list.append(messag.message_id)
	else:
		post_id, func = call.data.split("_")
		post = repo.get_post(int(post_id))
		commands.send_post(bot, call.message, post)


@bot.callback_query_handler(func=lambda call: "to" in call.data)
def paginate_posts(call: CallbackQuery):
	func, to, page = call.data.split('_')
	if func == "post":
		commands.pagination_posts(bot, call.message, int(page))
	elif func == "group-get":
		commands.show_groups(bot, call.message, int(page), call.message.message_id)
	else:
		func, message_id, message_info_id = call.data.split(" ")[:-1]
		commands.paginate_groups(bot, call.message, int(message_id), int(message_info_id), int(page))


@bot.callback_query_handler(func=lambda call: "media" in call.data)
def media_posts(call: CallbackQuery):
	media, boolean, message_id, message_info_id = call.data.split('_')
	commands.media_call_data(call.message, bot, bool(int(boolean)), int(message_id), int(message_info_id))


if __name__ == "__main__":
	run_pend = Thread(target=commands.run_pending)
	bot_poll = Thread(target=bot.infinity_polling)
	run_pend.start()
	bot_poll.start()
	run_pend.join()
	bot_poll.join()