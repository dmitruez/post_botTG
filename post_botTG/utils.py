from entities import Post, Group
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from repository import Repo

repo = Repo()

def paginate(page, pages_count, array, func):
	keyboard = InlineKeyboardMarkup()
	if pages_count == 1:
		for item in array[page]:
			keyboard.add(item)
	else:
		left = page - 1 if page != 1 else pages_count
		right = page + 1 if page != pages_count else 1
		button_back = InlineKeyboardButton("←", callback_data=f"{func}_to_{left}")
		page_button = InlineKeyboardButton(f"{page}/{pages_count}", callback_data=f"current page")
		button_next = InlineKeyboardButton("→", callback_data=f"{func}_to_{right}")
		for item in array[page]:
			keyboard.add(item)
		keyboard.add(button_back, page_button, button_next)
	return keyboard


def get_pages(array: list[Post or Group], group_func=None):
	pages_dict = {}
	page = 1
	index = 0
	while True:
		pages_dict[page] = []
		if isinstance(array[0], Group):
			for group in array[index:index + 6]:
				if group_func == "get":
					pages_dict[page].append(InlineKeyboardButton(group.title, callback_data=f"{group.group_id}_group-get"))
				else:
					pages_dict[page].append(InlineKeyboardButton(group.title, callback_data=f"{group.group_id}_group"))
		else:
			for post in array[index:index + 6]:
				pages_dict[page].append(InlineKeyboardButton(post.title, callback_data=f"{post.post_id}_post"))
		if len(array[index + 6:]) == 0:
			break
		page += 1
		index += 6
	
	return pages_dict


def add_hide_button(keyboard: InlineKeyboardMarkup):
	button_hide = InlineKeyboardButton("Скрыть", callback_data="hide")
	keyboard.add(button_hide)


def edit_keyboard_post(post: Post, func) -> InlineKeyboardMarkup:
	keyboard = InlineKeyboardMarkup()
	button_delete = InlineKeyboardButton("Удалить пост", callback_data=f"delete_{post.post_id}")
	button_hide = InlineKeyboardButton("Скрыть", callback_data=f"hide")
	if func == "stop":
		button_3 = InlineKeyboardButton("Возобновить рассылку", callback_data=f"startsend_{post.post_id}")
	else:
		button_3 = InlineKeyboardButton("Остановить рассылку", callback_data=f"stopsend_{post.post_id}")
	
	keyboard.add(button_delete).add(button_3).add(button_hide)
	return keyboard


def save_to_media(filename, data):
	with open(filename, "wb+") as f:
		f.write(data)


def check_status(message: Message, forward_chat=False):
	ids = repo.get_admin_ids()
	if forward_chat:
		if message.from_user.id in ids:
			return True
		else:
			return False
	else:
		if message.from_user.id in ids and message.chat.type == 'private':
			return True
		else:
			return False