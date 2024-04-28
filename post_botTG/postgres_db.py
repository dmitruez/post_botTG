import psycopg2
from entities import Container, Group, Admin


class PostgresDB:
	dbname = 'postgres'
	db_password = 'postgres'
	db_user = 'postgres'
	db_host = 'localhost'
	db_port = '5432'
	
	
	def __init__(self):
		self.connection = psycopg2.connect(
			dbname=self.dbname,
			user=self.db_user,
			password=self.db_password,
			host=self.db_host,
			port=self.db_port,
			)
		self.cursor = self.connection.cursor()
		self.create_tables()
	
	def create_tables(self):
		# Создаем основную таблицу с именами групп или каналов
		self.cursor.execute(
			"""
				CREATE TABLE IF NOT EXISTS groups
				(
					id serial PRIMARY KEY,
					tg_id bigint,
					title text,
					type text,
					username text
				)
			"""
			)
		self.connection.commit()
		
		
		
		# Создаем таблицу со всеми постами
		self.cursor.execute(
			"""
				CREATE TABLE IF NOT EXISTS posts
				(
					id serial PRIMARY KEY,
					title text,
					text text,
					media text,
					media_type text,
					interval int,
					unit text
				)
			"""
			)
		self.connection.commit()
		
		
		# Создаем таблицу, которая связывает посты с группами или каналами
		self.cursor.execute(
			"""
				CREATE TABLE IF NOT EXISTS groups_posts_connect
				(
					id serial PRIMARY KEY,
					group_id int,
					post_id int
				)
				"""
			)
		self.connection.commit()
		
		# Создаем таблицу со всеми админами
		self.cursor.execute(
			"""
				CREATE TABLE IF NOT EXISTS admins
				(
					id serial PRIMARY KEY,
					tg_id bigint,
					first_name text,
					username text
				)
			"""
			)
		self.connection.commit()
		
	
	def select_all_posts(self):
		# Достаем все посты из таблицы
		self.cursor.execute(
			"""
				SELECT * FROM posts
					"""
			)
		data = self.cursor.fetchall()
		return data
		
		
	def select_one_post(self, post_id):
		self.cursor.execute(
			"""
			SELECT title, text, media, media_type, interval, unit FROM posts
			WHERE id = %s""", (post_id, )
			)
		data = self.cursor.fetchone()
		return data
	
	
	def select_all_groups(self):
		self.cursor.execute(
			"""
			SELECT * FROM groups"""
			)
		
		data = self.cursor.fetchall()
		return data
	
	
	def select_one_group(self, group_id):
		self.cursor.execute(
			"""
			SELECT tg_id, title, type, username
			FROM groups
			WHERE id = %s""", (group_id,)
			)
		data = self.cursor.fetchone()
		return data
	
	
	def select_one_group_by_tg_id(self, tg_id):
		self.cursor.execute(
			"""
			SELECT *
			FROM groups
			WHERE tg_id = %s""", (tg_id,)
			)
		data = self.cursor.fetchone()
		return data
	
	
	# Заготовка для получения поста его параметров, в каких группах он находится и тд
	def get_groups_post(self, post_id: int):
		groups: list[Group] = []
		self.cursor.execute(
			"""
			SELECT groups.id, groups.tg_id, groups.title, groups.type, groups.username from groups
			inner join groups_posts_connect
			on groups.id = groups_posts_connect.group_id
			inner join posts
			on posts.id = groups_posts_connect.post_id
			WHERE posts.id = %s
			""", (post_id, )
			)
		
		data = self.cursor.fetchall()
		for group_id, tg_id, title, group_type, username in data:
			groups.append(Group(group_id, tg_id, title, group_type, username))
		return groups
	
	

	def select_first_post_id(self):
		self.cursor.execute(
			"""
			SELECT id FROM posts"""
			)
		
		post_id = self.cursor.fetchall()[-1][0]
		return post_id
	
	
	def insert_into_groups_posts_connect(self, post_id: int, groups: list):
		for group in groups:
			self.cursor.execute(
				"""
				INSERT INTO groups_posts_connect (group_id, post_id)
				VALUES (%s, %s)""", (group.group_id, post_id)
				)
			self.connection.commit()
			
			
	def insert_into_posts(self, container: Container):
		title = container.title
		text = container.text
		media = container.media
		media_type = container.media_type
		interval = container.interval
		unit = container.unit
		self.cursor.execute(
			"""
			INSERT INTO posts (title, text, media, media_type, interval, unit)
				VALUES (%s, %s, %s, %s, %s, %s)""", (title, text, media, media_type, interval, unit)
			)
		self.connection.commit()
		
		post_id = self.select_first_post_id()
		self.insert_into_groups_posts_connect(post_id, container.groups)
		
	
	def delete_from_posts(self, post_id: int):
		self.cursor.execute(
			"""
			DELETE FROM posts
			WHERE id = %s""", (post_id, )
			)
		self.connection.commit()
	
	
	def delete_from_groups_posts_connect(self, _id, _type):
		if _type == "group":
			self.cursor.execute(
				"""
			DELETE FROM groups_posts_connect
			WHERE group_id = %s""", (_id, )
				)
		else:
			self.cursor.execute(
				"""
			DELETE FROM groups_posts_connect
			WHERE post_id = %s""", (_id,)
				)
			
		self.connection.commit()
		
		
	def insert_into_groups(self, tg_id, title, group_type, username):
		self.cursor.execute(
			"""
			INSERT INTO groups (tg_id, title, type, username)
				VALUES (%s, %s, %s, %s)
				""", (tg_id, title, group_type, username)
				)
		
		self.connection.commit()
		
		
	def delete_from_groups(self, group_tg_id):
		self.cursor.execute(
			"""
			DELETE FROM groups
			WHERE tg_id = %s
			""", (group_tg_id, )
			)
		
		self.connection.commit()
		
	
	
	def insert_into_admins(self, tg_id, first_name, username):
		self.cursor.execute(
			"""
			INSERT INTO admins (tg_id, first_name, username)
				VALUES (%s, %s, %s)
				""", (tg_id, first_name, username)
			)
		
		self.connection.commit()
		
		
		
	def select_admin(self, tg_id):
		self.cursor.execute(
			"""
			SELECT * FROM admins
			WHERE tg_id = %s
				""", (tg_id, )
			)
		
		admin_id, tg_id, first_name, username = self.cursor.fetchone()
		return Admin(admin_id, tg_id, first_name, username)
	
	
	
	def select_admins(self):
		self.cursor.execute(
			"""
			SELECT * FROM admins
				"""
			)
		
		data = self.cursor.fetchall()
		return data
	
	
	def select_admins_ids(self):
		self.cursor.execute(
			"""
			SELECT tg_id FROM admins
				"""
			)
		
		tg_ids = self.cursor.fetchall()
		return tg_ids
	
	def delete_from_admins(self, tg_id):
		self.cursor.execute(
			"""
			DELETE FROM admins
			WHERE tg_id = %s
				""", (tg_id,)
			)
		
		self.connection.commit()
		