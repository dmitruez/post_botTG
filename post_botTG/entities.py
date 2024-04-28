from dataclasses import dataclass, field

unit_translate = {
	"seconds": "секунд",
	"minutes": "минут",
	"hours": "часа",
	"days": "дня",
	"weeks": "недели"
	}

@dataclass
class Post:
	post_id: int
	title: str
	text: str
	media: str or None
	media_type: str
	interval: int
	unit: str
	groups: field(default=list)
	
	
	def pretty_print(self):
		text_groups = ""
		for group in self.groups:
			if group.username:
				text_groups += f'@{group.username}, '
			else:
				text_groups += f'{group.title}, '
		
		text_groups = text_groups[:-2]
		unit = unit_translate[self.unit] or None
		text = f'{self.text}\n' + "\n<b><i>Параметры:</i></b>" +  f"\n<b>Название поста</b>: {self.title}\n<b>Чаты</b>: {text_groups}\n<b>Интервал</b>: каждые {self.interval} {unit}\n\n"
		return text
	
	
	
class Container:
	
	def __init__(self):
		self.title = None
		self.text = None
		self.media = None
		self.media_type = None
		self.interval = None
		self.unit = None
		self.groups = []
		
		
	def clear(self):
		self.title = None
		self.text = None
		self.media = None
		self.media_type = None
		self.interval = None
		self.unit = None
		self.groups: list[Group] = []
	
	
	def pretty_print(self):
		text_groups = ""
		if len(self.groups) > 0:
			for group in self.groups:
				if group.username:
					text_groups += f'@{group.username}, '
				else:
					text_groups += f'{group.title}, '
					
			text_groups = text_groups[:-2]
		if self.text:
			text = f'{self.text}\n' + "\n<b><i>Параметры:</i></b>" +  f"\n<b>Название поста</b>: {self.title}"
			if len(text_groups) > 0:
				text = f'{self.text}\n' + "\n<b><i>Параметры:</i></b>" +  f"\n<b>Название поста</b>: {self.title}\n<b>Чаты</b>: {text_groups}"
				if self.interval and self.unit:
					unit = unit_translate[self.unit.lower()]
					text = f'{self.text}\n' + "\n<b><i>Параметры:</i></b>" +  f"\n<b>Название поста</b>: {self.title}\n<b>Чаты</b>: {text_groups}\n<b>Интервал</b>: каждые {self.interval} {unit}"
		else:
			text = 'Ваш текст будет <i>тут</i>\n' + "\n<b><i>Параметры:</i></b>" +  f"\n<b>Название поста</b>: {self.title}"
			
		return text
	
	
	
	
	

@dataclass
class Group:
	group_id: int
	tg_id: int
	title: str
	group_type: str
	username: str
	
	
	
	def pretty_print(self):
		if self.group_type == 'channel':
			if self.username:
				text = f"<b>Канал</b>\n\n<b>Название:</b> {self.title}\n<b>Быстрая ссылка:</b> @{self.username}"
			else:
				text = f"<b>Канал</b>\n\n<b>Название:</b> {self.title}"
		else:
			if self.username:
				text = f"<b>Группа</b>\n\n<b>Название:</b> {self.title}\n<b>Быстрая ссылка:</b> @{self.username}"
			else:
				text = f"<b>Группа</b>\n\n<b>Название:</b> {self.title}"
		return text
	
	

@dataclass
class Admin:
	admin_id: int
	tg_id: int
	first_name: str
	username: str