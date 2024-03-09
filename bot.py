import telebot



bot_token = "7148185758:AAFK9hfn3IkbvLdjJM4CCdOaXnetrGvwwHo"
bot = telebot.TeleBot(bot_token, parse_mode="html")



@bot.message_handler(commands=["start"])
def bot_starting(message):
	pass



@bot.message_handler(commands=["post"])
def posts_settings(message):
	pass


@bot.message_handler(commands=["chats"])
def chats_settings(message):
	pass

