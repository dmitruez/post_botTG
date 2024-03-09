import psycopg2



class PostgresDB:
	db_password = 'postgres'
	db_user = 'postgres'
	db_host = 'localhost'
	db_port = '5432'
	
	def __init__(self):
		self.connection = psycopg2.connect(
			user=self.db_user,
			password=self.db_password,
			host=self.db_host,
			port=self.db_port,
			)
		self.cursor = self.connection.cursor()
		self._create_tables()
	
	def _create_tables(self):
		# Создаем основную таблицу с именами групп или каналов
		self.cursor.execute(
			f"""
				CREATE TABLE IF NOT EXISTS groups
				(
					id serial PRIMARY KEY,
					group_name text,
					type varchar(10)
				)
			"""
			)
		self.connection.commit()
		
		# Создаем таблицу со всеми постами
		self.cursor.execute(
			f"""
				CREATE TABLE IF NOT EXISTS posts
				(
					id serial PRIMARY KEY,
					title text,
					text text,
					media text
				)
			"""
			)
		
		# Создаем таблицу связующую посты с группами или каналами
		self.cursor.execute(
			f"""
				CREATE TABLE IF NOT EXISTS groups_posts_connect
				(
					id serial PRIMARY KEY,
					group_id int,
					post_id int
				)
				"""
			)