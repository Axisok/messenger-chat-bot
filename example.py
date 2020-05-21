from bot import MessengerBot, command
import time
import random
import sys

# An example bot.
# Uses most of the functionalities of the framework, to show how they work.

# Credentials the bot will use, it's heavily recommended not to put them in plain text like this, especially if you're planning to share your code.
email = "EMAIL"
password = "PASSWORD"

# The conversation link the bot will go to, use the part right after /t/.
conversation = "CONVERSATION"

# This shows how you can easily manage command names outside of the command decorator.
roulette_names = ["roulette", "roll", "random", "rand"]

class MyBot(MessengerBot):

	def __init__(self):

		# Giving a default email and password makes the bot automatically log in, so we don't need to call that.
		# safe_mode=True means messages will be written but not sent, headless=True means the browser is invisible.
		super().__init__(default_email=email, default_password=password, safe_mode=True, headless=True)
		# Start up might take a little while.

		# Because we're logged in, this'll log us out, then in again.
		# Because default credentials were set already, this will use those if not given any arguments.
		self.login()

		# Make it so the bot can be called with "hey @Name_of_the_Bot" in addition to existing prefixes.
		# {bot} in this case is replaced with the name.
		self.command_prefixes.append("hey @{bot}")

		# Try to go to the desired conversation. If we fail, quit the program.
		if (not self.set_conversation(conversation)):
			self.quit()
			sys.exit()

	@command("hi", "hey", "hello", "yo", "sup", "whats up")
	def hi(self, command):

		# The \t is for the mention to work, it's a hack and will hopefully be changed in the near future.
		# We use two y's so it doesn't trigger the command.
		self.send_message(f"Heyy, it's @{command.message.author}\t!")

	@command(*roulette_names)
	def roulette(self, command):

		# Simple random number generator command, it crashes with negative numbers but there's a try/except on every command so it's ok.
		if (command.args[1].isnumeric()):
			n = random.randint(0, int(float(command.args[1])))

			# You can pass a conversation argument, so it makes sure you're at that conversation before sending the message.
			# This is very useful if you want to go back and forth between multiple conversations, but isn't ideal for a command based bot.
			self.send_message(f"You got a {n}, @{command.message.author}\t.", conversation)

	@command("die", "go sleep", "time to sleep", "go away", "everyone hates you", "everybody hates you", "no one loves you")
	def die(self, command):
		self.send_message(f"Wow, ok then...")
		# Closes the window, then exits.
		self.quit()
		sys.exit()

bot = MyBot()

while (True):

	# Note that new messages are only detected after the bot enters a conversation, so commands sent before that will return nothing.

	# Check if there's new messages before doing anything else.
	# new_messages is about 100 times faster than calling handle_commands and possibly have it do nothing.
	if (bot.new_messages() > 0):

		# Handle any commands given.
		# The way commands are recognized is by using the prefix and suffix list, if any match with the message it's a command.
		# Then, it checks if each command is seen at the start of the message (ignoring prefix).
		# The first command matched is always the one executed.
		ml = bot.handle_commands()

		# handle_commands also returns the list of new messages it found, so we can print it or use for something interesting.
		# Here we print the amount because it's not made to be easy to read and it might take multiple lines.
		print(len(ml))

	# Reducing this value will make the bot a little more responsive, but also require more CPU.
	time.sleep(1)
