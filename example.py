from bot import MessengerBot

# If there's a default email and password it'll log in immediately, no need to call login() yourself.
# It'll also keep the credentials and use them if you don't pass anything on future login() calls.
# If your internet connection is on the slow side use a bigger ajax_time.
bot = MessengerBot(safe_mode=True, default_email="YOUR_EMAIL", default_password="YOUR_PASSWORD", ajax_time=1.5)

# We're getting the list of conversations here.
conversations = bot.get_conversations()
print(f"Conversations available for this account: {conversations}")

# Log out them back in just for fun.
bot.logout()
bot.login()

# Let's go through some conversations, 5 at most.
for i in range(0, min(5, len(conversations))):
	# Get the conversation.
	conversation = conversations[i]

	# Go to that conversation.
	bot.set_conversation(conversation.link)

	# Run some fun commands.
	print(f"People on conversation {conversation}: {bot.get_participants()}")
	print(f"Messages on conversation {conversation}: {bot.messages_detailed()}")

	# Unless you disable safe mode, this won't actually send anything.
	# Also notice how you can pass a conversation argument, this is very useful as it makes sure you're there before doing anything.
	# If, for whatever reason, this conversation link doesn't exist it'll just not send anything.
	bot.send_message(f"Hey {conversation.name}! This is a test.", conversation.link)

# Always call this method so the application actually stops.
bot.quit()