import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from entities import Post, Group, Admin
from postgres_db import PostgresDB

class Repo:
	pg = PostgresDB()
	
	
	@staticmethod
	def get_text(config, name):
		with open("config.json", "r", encoding="utf-8") as file:
			data = json.load(file)[config]["sentences"]
			res = data[name]
			return res
	
	
	
	
	@staticmethod
	def get_keyboard(config, category, call_data=None, url=False):
		with open("config.json", "r", encoding="utf-8") as read_file:
			data = json.load(read_file)[config]
			keyboard_settings = data["keyboards"][category]
			keyboard = InlineKeyboardMarkup()
			buttns = []
			for key, button in keyboard_settings.items():
				if url:
					if button.get("call_data"):
						buttns.append(InlineKeyboardButton(button["text"], callback_data=button["call_data"]))
					else:
						buttns.append(InlineKeyboardButton(button["text"], url=button["url"]))
				else:
					if call_data:
						buttns.append(InlineKeyboardButton(button["text"], callback_data=button["call_data"] + str(call_data)))
					else:
						buttns.append(
							InlineKeyboardButton(button["text"], callback_data=button["call_data"])
							)
			keyboard.add(*buttns)
			return keyboard
	
	
	
	def get_admin_keyboard(self):
		keyboard = InlineKeyboardMarkup()
		with open("config.json", "r", encoding="utf-8") as read_file:
			data = json.load(read_file)["admins"]
			super_admin = data["super_admin"]
			common_admins = [Admin(admin_id, tg_id, first_name, username) for admin_id, tg_id, first_name,
			username in self.pg.select_admins()]
			if len(common_admins) == 0:
				return super_admin
			else:
				for admin in common_admins:
					if admin.username:
						button = InlineKeyboardButton(admin.username, callback_data=f"admin_{admin.tg_id}")
					else:
						button = InlineKeyboardButton(admin.first_name, callback_data=f"admin_{admin.tg_id}")
					keyboard.add(button)
			
			return keyboard
			
			
	def get_admin_ids(self):
		ids = self.pg.select_admins_ids()
		ids = [id[0] for id in ids]
		with open("config.json", "r", encoding="utf-8") as read_file:
			data = json.load(read_file)["admins"]
			super_admin = data["super_admin"]
			me = data["me"]
			ids.append(super_admin[1])
			ids.append(me)
		return ids
	
		
		
	
	def get_posts(self):
		data = self.pg.select_all_posts()
		posts = []
		for post_id, title, text, media, media_type, interval, unit in data:
			groups = self.pg.get_groups_post(post_id)
			posts.append(Post(post_id, title, text, media, media_type, interval, unit, groups))
		return posts
	
	
	
	def get_post(self, post_id):
		title, text, media, media_type, interval, unit = self.pg.select_one_post(post_id)
		groups = self.pg.get_groups_post(post_id)
		post = Post(post_id, title, text, media, media_type, interval, unit, groups)
		return post
	
	
	def get_groups(self):
		data = self.pg.select_all_groups()
		groups = []
		for group_id, tg_id, title, group_type, username in data:
			groups.append(Group(group_id, tg_id, title, group_type, username))
		return groups
	
	
	def get_group(self, group_id):
		tg_id, title, group_type, username = self.pg.select_one_group(group_id)
		return Group(group_id, tg_id, title, group_type, username)
	
	
	def get_group_by_tg_id(self, tg_id):
		group_id, tg_id, title, group_type, username = self.pg.select_one_group_by_tg_id(tg_id)
		return Group(group_id, tg_id, title, group_type, username)