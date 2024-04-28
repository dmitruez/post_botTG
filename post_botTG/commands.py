from time import sleep

import schedule
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import utils
from entities import Post, Container, Group
from postgres_db import PostgresDB
from repository import Repo


repo = Repo()
pg = PostgresDB()
np = Container()
started = False

schedule_works = {}


# ОТПРАВКА В ЧАТЫ СООБЩЕНИЙ =======================================================================
def info(bot: TeleBot, message: Message):
	bot.send_message(message.chat.id, repo.get_text("start_bot", "info"))


def starting_message(bot: TeleBot, message: Message):
	bot.send_message(message.chat.id, repo.get_text("start_bot", "start").format(message.from_user.first_name),
	                 disable_web_page_preview=True)


def run_pending():
	global started
	if started:
		pass
	else:
		started = True
		while True:
			schedule.run_pending()
			sleep(1)


def start_all(bot, message):
	posts = repo.get_posts()
	schedules = 0
	for post in posts:
		create_schedule_for_post(bot, message, post)
		schedules += 1
	if schedules > 0:
		bot.send_message(message.chat.id, repo.get_text("sending_config", "start_send"))
	else:
		bot.send_message(message.chat.id, repo.get_text("sending_config", "nothing_to_start"))


def stop_all(bot, message):
	posts = repo.get_posts()
	schedules = 0
	for post in posts:
		delete_schedule_for_post(post)
		schedules += 1
	if schedules > 0:
		bot.send_message(message.chat.id, repo.get_text("sending_config", "end_send"))
	else:
		bot.send_message(message.chat.id, repo.get_text("sending_config", "nothing_to_end"))


def start_sending(bot: TeleBot, message_chat_id, group: Group, text, media, media_type):
	try:
		if media:
			with open(media, "rb") as media:
				if media_type == "photo":
					bot.send_photo(group.tg_id, media, caption=text)
				else:
					bot.send_video(group.tg_id, media, caption=text)
		else:
			bot.send_message(group.tg_id, text)
	except ApiTelegramException:
		if group.username:
			form = f"@{group.username}"
		else:
			form = f"{group.title}"
		bot.send_message(message_chat_id, repo.get_text("sending_config", "admin_error").format(form))


def create_schedule_for_post(bot, message: Message, post: Post):
	groups: list[Group] = post.groups
	if not schedule_works.get(post.post_id):
		schedule_works[post.post_id] = []
	if len(schedule_works[post.post_id]) > 0:
		pass
	else:
		for group in groups:
			start_sending(bot, message.chat.id, group, post.text, post.media, post.media_type)
			if post.unit == 'minutes':
				a = schedule.every(post.interval).minutes.do(start_sending, bot, message.chat.id, group, post.text,
				                                             post.media, post.media_type)
				schedule_works[post.post_id].append(a)
			elif post.unit == 'hours':
				a = schedule.every(post.interval).hours.do(start_sending, bot, message.chat.id, group, post.text,
				                                           post.media, post.media_type)
				schedule_works[post.post_id].append(a)
			else:
				a = schedule.every(post.interval).seconds.do(start_sending, bot, message.chat.id, group, post.text,
				                                             post.media, post.media_type)
				schedule_works[post.post_id].append(a)


def delete_schedule_for_post(post: Post):
	if schedule_works.get(post.post_id):
		if len(schedule_works[post.post_id]) > 0:
			for job in schedule_works[post.post_id]:
				schedule.cancel_job(job)
			schedule_works.pop(post.post_id)


# БЛОК ДЛЯ РАБОТЫ С ПОСТАМИ ============================================================================
def save_new_post(message: Message, bot: TeleBot, message_id, message_info_id):
	if message.text == '/clear':
		bot.send_message(message.chat.id, text=repo.get_text("create_config", "clear_command"))
		np.clear()
		bot.delete_message(message.chat.id, message_id)
		bot.delete_message(message.chat.id, message_info_id)
	else:
		np.interval = int(message.text)
		if np.media:
			bot.edit_message_caption(np.pretty_print(), message.chat.id, message_id)
		else:
			bot.edit_message_text(np.pretty_print(), message.chat.id, message_id)
		bot.edit_message_text(repo.get_text("create_config", "saving"), message.chat.id, message_info_id)
		pg.insert_into_posts(np)
		np.clear()
		post_id = pg.select_first_post_id()
		post = repo.get_post(post_id)
		create_schedule_for_post(bot, message, post)
		bot.edit_message_text(repo.get_text("create_config", "save_clear"), message.chat.id, message_info_id)


def interval_handler(message: Message, bot: TeleBot, unit, message_id, message_info_id):
	np.unit = unit
	bot.edit_message_text(repo.get_text("create_config", "input_interval"), message.chat.id, message_info_id)
	bot.register_next_step_handler(message, save_new_post, bot, message_id, message_info_id)


def unit_handler(bot: TeleBot, message: Message, message_id, message_info_id):
	if np.media:
		bot.edit_message_caption(np.pretty_print(), message.chat.id, message_id)
	else:
		bot.edit_message_text(np.pretty_print(), message.chat.id, message_id)
	keyboard = repo.get_keyboard("create_config", "unit_keyboard", call_data=f"{message_id}_{message_info_id}")
	button_clear = InlineKeyboardButton(text="Остановить создание поста", callback_data=f"clear_{message_id}"
	                                                                                    f"_{message_info_id}")
	keyboard.add(button_clear)
	bot.edit_message_text(repo.get_text("create_config", "input_unit"), message.chat.id, message_info_id,
	                      reply_markup=keyboard)


def add_group_to_np(group_id):
	group = repo.get_group(group_id)
	if group not in np.groups:
		np.groups.append(group)
		return group.title
	return None


def show_groups(bot: TeleBot, message: Message, page=1, message_id=None):
	try:
		groups = repo.get_groups()
		group_pages = utils.get_pages(groups, group_func="get")
		group_count = len(group_pages)
		keyboard = utils.paginate(page, group_count, group_pages, "group-get")
		utils.add_hide_button(keyboard)
		if message_id:
			bot.edit_message_reply_markup(message.chat.id, message_id=message_id, reply_markup=keyboard)
		else:
			bot.send_message(message.chat.id, text="<b>Доступные чаты</b>", reply_markup=keyboard)
	except IndexError:
		bot.send_message(message.chat.id,
		                 "<b>Доступные чаты</b>\n\nУ вас пока нет чатов для отправки\nЧто бы добавить чат для постинга напишите /new_chat")


def paginate_groups(bot: TeleBot, message: Message, message_id=None, message_info_id=None, page=1):
	groups = repo.get_groups()
	group_pages = utils.get_pages(groups)
	group_count = len(group_pages)
	if len(groups) == 0:
		bot.send_message(message.chat.id,
		                 "<b>Доступные чаты</b>\n\nУ вас пока нет чатов для отправки\nЧто бы добавить чат для постинга напишите /new_chat\n\nПосле, заного напишите /new_post")
	keyboard = utils.paginate(page, group_count, group_pages, f"group {message_id} {message_info_id} ")
	button_end = InlineKeyboardButton(text="Завершить добавление чатов",
	                                  callback_data=f"group_stop_{message_id}_{message_info_id}")
	button_clear = InlineKeyboardButton(text="Остановить создание поста",
	                                    callback_data=f"clear_{message_id}_{message_info_id}")
	keyboard.add(button_end, button_clear)
	try:
		bot.edit_message_reply_markup(message.chat.id, message_id=message_info_id, reply_markup=keyboard)
	except ApiTelegramException:
		bot.send_message(message.chat.id, text="<b>Доступные чаты</b>", reply_markup=keyboard)


# 5. Принимает фото или видео
def media_handler(message: Message, bot: TeleBot, message_id, message_info_id):
	bot.delete_message(message.chat.id, message.message_id)
	bot.delete_message(message.chat.id, message_info_id)
	if message.content_type == "photo":
		np.media_type = 'photo'
		media = bot.get_file(message.photo[len(message.photo) - 1].file_id)
		np.media = "media/" + media.file_path
		data = bot.download_file(media.file_path)
		utils.save_to_media(np.media, data)
		text = np.pretty_print()
		with open(np.media, "rb") as photo:
			bot.delete_message(message.chat.id, message_id)
			messag = bot.send_photo(message.chat.id, photo=photo, caption=text)
		message_id = messag.message_id
	elif message.content_type == "video":
		np.media_type = 'video'
		media = bot.get_file(message.video.file_id)
		np.media = "media/" + media.file_path
		data = bot.download_file(media.file_path)
		utils.save_to_media(np.media, data)
		text = np.pretty_print()
		with open(np.media, "rb") as video:
			bot.delete_message(message.chat.id, message_id)
			messag = bot.send_video(message.chat.id, video=video, caption=text)
		message_id = messag.message_id
	else:
		bot.send_message(
			message.chat.id, text=f"Не верный тип данных: {message.content_type} | Отправьте медиа "
			                      f"еще раз"
			)
		bot.register_next_step_handler(message, media_handler, bot, message_id, message_info_id)
	messagi = bot.send_message(message.chat.id, repo.get_text("create_config", "select_groups"))
	message_id_info = messagi.message_id
	paginate_groups(bot, message, message_id, message_id_info)


# 4. Проверяет нужно ли медиа для поста или нет
def media_call_data(message: Message, bot: TeleBot, boolean, message_id, message_info_id):
	if boolean:
		bot.edit_message_text(repo.get_text("create_config", "send_media"), message.chat.id, message_info_id)
		bot.register_next_step_handler(message, media_handler, bot, message_id, message_info_id)
	else:
		bot.edit_message_text(repo.get_text("create_config", "select_groups"), message.chat.id, message_info_id)
		paginate_groups(bot, message, message_id, message_info_id)


# 3. Принимает любой текст с тегами для поста
def text_handler(message: Message, bot: TeleBot, message_id, message_info_id):
	if message.text == '/clear':
		bot.send_message(message.chat.id, text=repo.get_text("create_config", "clear_command"))
		np.clear()
		bot.delete_message(message.chat.id, message_id)
		bot.delete_message(message.chat.id, message_info_id)
	else:
		np.text = message.text
		bot.delete_message(message.chat.id, message.message_id)
		text = np.pretty_print()
		bot.edit_message_text(text, message.chat.id, message_id)
		keyboard = repo.get_keyboard("create_config", "media_keyboard", call_data=f"{message_id}_{message_info_id}")
		button_clear = InlineKeyboardButton(text="Остановить создание поста",
		                                    callback_data=f"clear_{message_id}_{message_info_id}")
		keyboard.add(button_clear)
		bot.edit_message_text(repo.get_text("create_config", "input_media"), message.chat.id, message_info_id,
		                      reply_markup=keyboard)


# 2. Даёт посту название, для ориентира
def title_handler(message: Message, bot: TeleBot, message_id, message_info_id):
	if message.text == '/clear':
		bot.send_message(message.chat.id, text=repo.get_text("create_config", "clear_command"))
		bot.delete_message(message.chat.id, message_id)
		bot.delete_message(message.chat.id, message_info_id)
	else:
		bot.delete_message(message.chat.id, message.message_id)
		np.title = message.text
		messag = bot.edit_message_text(np.pretty_print(), message.chat.id, message_id)
		bot.edit_message_text(repo.get_text("create_config", "input_text"), message.chat.id, message_info_id,
		                      disable_web_page_preview=True)
		message_id = messag.message_id
		bot.register_next_step_handler(message, text_handler, bot, message_id, message_info_id)


# 1. Принимает команду /new_post
def get_creation_instruction(message: Message, bot: TeleBot):
	messag = bot.send_message(message.chat.id, text=repo.get_text("create_config", "start"))
	message_info = bot.send_message(message.chat.id, text=repo.get_text("create_config", "input_title"))
	bot.register_next_step_handler(message, title_handler, bot, messag.message_id, message_info.message_id)


# ПАГИНАЦИЯ ПОСТОВ
def pagination_posts(bot: TeleBot, message: Message, page):
	posts = repo.get_posts()
	try:
		post_pages: dict[Post] = utils.get_pages(posts)
		pages_count = len(post_pages)
		keyboard = utils.paginate(page, pages_count, post_pages, "post")
		utils.add_hide_button(keyboard)
		try:
			bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id, reply_markup=keyboard)
		except ApiTelegramException:
			bot.send_message(message.chat.id, text="<b>Доступные посты</b>", reply_markup=keyboard)
	except IndexError:
		bot.send_message(message.chat.id,
		                 text="<b>Доступные посты</b>\n\n У вас пока нет постов\nНажмите /new_post что бы создать новый пост")


# Отправка одиночного поста
def send_post(bot: TeleBot, message: Message, post: Post):
	button_delete = InlineKeyboardButton("Удалить пост", callback_data=f"delete_post_{post.post_id}")
	if schedule_works.get(post.post_id):
		button_3 = InlineKeyboardButton("Остановить рассылку", callback_data=f"stopsend_{post.post_id}")
	else:
		button_3 = InlineKeyboardButton("Начать рассылку", callback_data=f"startsend_{post.post_id}")
	reply_markup = InlineKeyboardMarkup().add(button_delete).add(button_3)
	utils.add_hide_button(reply_markup)
	text = post.pretty_print()
	if post.media:
		with open(post.media, "rb") as f:
			if post.media_type == "photo":
				bot.send_photo(message.chat.id, photo=f, caption=text, reply_markup=reply_markup)
			else:
				bot.send_video(message.chat.id, video=f, caption=text, reply_markup=reply_markup)
	else:
		bot.send_message(message.chat.id, text=text, reply_markup=reply_markup)


def delete_post(bot: TeleBot, message: Message, post_id):
	post = repo.get_post(post_id)
	title = post.title
	pg.delete_from_posts(post_id)
	pg.delete_from_groups_posts_connect(post_id, "post")
	bot.delete_message(message.chat.id, message.message_id)
	bot.send_message(message.chat.id, text=f"Пост: {title} | Удалён")
	for job in schedule_works[post_id]:
		schedule.cancel_job(job)
	schedule_works.pop(post_id)


def stop_sending_post(bot: TeleBot, message: Message, post_id):
	post = repo.get_post(post_id)
	keyboard = utils.edit_keyboard_post(post, "stop")
	bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=keyboard)
	delete_schedule_for_post(post)
	bot.send_message(message.chat.id, repo.get_text("sending_config", "stop_send").format(post.title))


def start_sending_post(bot: TeleBot, message: Message, post_id):
	post = repo.get_post(post_id)
	keyboard = utils.edit_keyboard_post(post, "start")
	bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=keyboard)
	create_schedule_for_post(bot, message, post)
	bot.send_message(message.chat.id, repo.get_text("sending_config", "start_send_post").format(post.title))


def clearing(bot: TeleBot, message: Message, m3):
	for m in [int(m) for m in m3]:
		bot.delete_message(message.chat.id, m)
	bot.send_message(message.chat.id, text=repo.get_text("create_config", "clear_command"))
	np.clear()


# БЛОК ДЛЯ РАБОТЫ С ЧАТАМИ ============================================================================
def send_group(bot: TeleBot, message: Message, group: Group):
	button_delete = InlineKeyboardButton("Удалить", callback_data=f"delete_group_{group.tg_id}")
	text = group.pretty_print()
	reply_markup = InlineKeyboardMarkup().add(button_delete)
	utils.add_hide_button(reply_markup)
	bot.send_message(message.chat.id, text=text, reply_markup=reply_markup)


def add_channel(message: Message, bot: TeleBot):
	groups = repo.get_groups()
	if message.forward_from_chat.id in list(map(lambda np: np.tg_id, groups)):
		pass
	else:
		pg.insert_into_groups(message.forward_from_chat.id, message.forward_from_chat.title,
		                      message.forward_from_chat.type, message.forward_from_chat.username)
		bot.send_message(message.chat.id,
		                 repo.get_text("add_chat_config", "second").format(message.forward_from_chat.title))


def add_group(message: Message, bot: TeleBot):
	if 6161335069 in list(map(lambda np: np.id, message.new_chat_members)):
		groups = repo.get_groups()
		if message.chat.id in list(map(lambda np: np.tg_id, groups)):
			pass
		else:
			pg.insert_into_groups(message.chat.id, message.chat.title, message.chat.type, message.chat.username)
			bot.send_message(
				message.from_user.id, f"<b>Добавление нового чата</b>\n\nДобавлена новая группа:"
				                 f" {message.chat.title}"
				)
	else:
		pass


def channel_request(bot: TeleBot, message: Message):
	keyboard = repo.get_keyboard("add_chat_config", "add_to_channel", url=True)
	bot.send_message(message.chat.id, text=repo.get_text("add_chat_config", "channel"), reply_markup=keyboard)


def add_new_chat(bot: TeleBot, message: Message):
	keyboard = repo.get_keyboard("add_chat_config", "add_to_group", url=True)
	bot.send_message(message.chat.id, text=repo.get_text("add_chat_config", "first"), reply_markup=keyboard)


def delete_group(bot: TeleBot, message: Message, group_tg_id):
	group = repo.get_group_by_tg_id(group_tg_id)
	title = group.title
	pg.delete_from_groups(group_tg_id)
	pg.delete_from_groups_posts_connect(group.group_id, "group")
	try:
		bot.leave_chat(group_tg_id)
	except ApiTelegramException:
		pass
	bot.send_message(message.chat.id, repo.get_text("add_chat_config", "delete_group").format(title))


# РАБОТА С АДМИНАМИ БОТА
def show_admins(bot: TeleBot, message: Message):
	keyboard = repo.get_admin_keyboard()
	if isinstance(keyboard, InlineKeyboardMarkup):
		bot.send_message(message.chat.id, text=repo.get_text("admins", "admins"), reply_markup=keyboard)
	else:
		bot.send_message(message.chat.id, text=repo.get_text("admins", "no_admins").format(keyboard[0]))


def one_admin(bot: TeleBot, message: Message, tg_id):
	try:
		admin = pg.select_admin(tg_id)
		keyboard = InlineKeyboardMarkup()
		button_delete = InlineKeyboardButton(text="Удалить админа", callback_data=f"deladmin_{tg_id}")
		keyboard.add(button_delete)
		utils.add_hide_button(keyboard)
		bot.send_message(message.chat.id, text=f"<b>Админ</b>\n\nИмя пользователя: {admin.first_name}\nНикнейм: @"
		                                       f"{admin.username}", reply_markup=keyboard)
	except TypeError:
		bot.send_message(
			message.chat.id, text="Такого админа больше не существует :/")


def del_admin(bot: TeleBot, message: Message, tg_id):
	admin = pg.select_admin(tg_id)
	pg.delete_from_admins(tg_id)
	bot.delete_message(message.chat.id, message.message_id)
	if admin.username:
		bot.send_message(message.chat.id, text=repo.get_text("admins", "delete_admin").format(f"@{admin.username}"))
	else:
		bot.send_message(message.chat.id, text=repo.get_text("admins", "delete_admin").format(admin.first_name))


def admin_handler(message: Message, bot: TeleBot):
	if message.contact:
		pg.insert_into_admins(message.contact.user_id, message.contact.first_name, None)
		bot.send_message(
			message.chat.id,
			text=repo.get_text("admins", "success_admin").format(message.contact.first_name)
			)
	elif message.forward_from:
		pg.insert_into_admins(message.forward_from.id, message.forward_from.first_name, message.forward_from.username)
		if message.forward_from.username:
			bot.send_message(
				message.chat.id,
				text=repo.get_text("admins", "success_admin").format(f"@{message.forward_from.username}")
				)
		else:
			bot.send_message(
				message.chat.id,
				text=repo.get_text("admins", "success_admin").format(message.forward_from.first_name)
				)


def add_admin(bot: TeleBot, message: Message):
	bot.send_message(message.chat.id, text=repo.get_text("admins", "add_admin"))
	bot.register_next_step_handler(message, admin_handler, bot)