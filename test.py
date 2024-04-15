user_input='Hey'
bot_reply='Bro'
lang='en'
sql=f"INSERT INTO messages(user_message,bot_reply,lang) VALUES ('%s','%s','%s');" % (user_input,bot_reply,lang)
print(sql)
