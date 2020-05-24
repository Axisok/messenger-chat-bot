from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time
import inspect

class Conversation:
	''' Represents a conversation on the left side bar.

	'''
	def __init__(self, name, link):
		self.name = name
		self.link = link
		
	def __repr__(self):
		return f"{self.name} [{self.link}]"

class MessageGroup:
	''' Represents a group of messages, contains consecutive messages sent by the same person in a relatively short period of time.

	'''
	def __init__(self, author, messages):
		self.author = author
		self.messages = messages
		
	def __repr__(self):
		return f"From {self.author}: {self.messages}"

class Message:
	''' Represents a single message, may or may not include a quote.

	'''
	def __init__(self, text, quote_text, author=None):
		self.author = author
		self.text = text
		self.quote_text = quote_text
		
	def __repr__(self):
		if (self.quote_text != ""):
			return f"> {self.quote_text} | {self.text}"
		else:
			return f"{self.text}"

class Command:
	''' A class representing a command sent to the bot.

		This is passed to BotCommands.

	'''
	def __init__(self, message, command_text):
		self.message = message
		self.command_text = command_text
		self.args = []

class BotCommand:
	''' A class representing a command the bot can receive.

		Names must have no spaces, otherwise they won't work.

	'''
	def __init__(self, function, names):
		self._call = function
		self.names = list(names)

def command(*names):
	''' A decorator returning a BotCommand.
		I'm actually surprised it works in the first place.

		Usage is command(name1, name2, name3 etc).
		Names will be put into the names parameter as a list.

	'''
	def wrapper(function):
		r = BotCommand(function, names)
		return r
	return wrapper

class MessengerBot:
	''' Class to control a Chrome driver and read/write information on Messenger conversations.

		You can easily inherit from the class and replace things so they work exactly how you want.
		That's part of the idea, even if this bot should provide everything most people need.

		Create methods and decorate them with @command(command_name1, command_name2, etc..) to easily create commands.

		Call handle_commands to read messages, find commands and execute matching ones.

	'''

	def __init__(self, default_email="", default_password="", safe_mode=False, headless=True):
		# Messages won't be sent, the browser window appears. Useful to find problems and test the bot before sending anything.
		self.safe_mode = safe_mode

		self.debug_log("Starting bot...")

		# Boot up the driver and saves it so we can do cool stuff later.
		options = Options()
		if (headless):
			options.add_argument('--headless')

		# You should add a chromedriver.exe somewhere.
		self.driver = webdriver.Chrome("chromedriver.exe", options=options)

		# If true, marks all seen messages so they aren't read twice.
		self.mark_seen_messages = True

		# If not zero, deletes message groups if there's that amount of them or more after reading messages. Performance was not measured, but should be better.
		# Recommended value is 30, anything below 20 has a decent chance of crashing and offer little to no performance advantage over 30.
		# Try disabling if having issues.
		self.auto_delete_messages = 30
	
		# Represents maximum time allowed for most ajax calls.
		self.ajax_time = 5

		# If true, the bot can trigger commands with it's own messages.
		# Very dangerous.
		self.self_commands = False

		# Commands are recognized as such if the message starts/ends with these.
		# {bot} refers to the name of the bot, hence why the bot should try to find it out.
		# Case sensitivity will be ignored, it shouldn't be considered when making variants.
		# By default, the bot reacts to being mentioned.
		# When not in a group this check doesn't happen and all messages go through.
		self.command_prefixes = ["@{bot}"]
		self.command_suffixes = ["@{bot}"]

		# List of commands.
		self.commands = []

		# Finds commands on the object and adds them.
		self._find_commands()

		# Set default credentials, if not empty also tries to log in immediately.
		self.default_email = default_email
		self.default_password = default_password
		if (self.default_email != "" and self.default_password != ""):
			self.login()

		# The name of the bot, as it knows it. Will be "_Bot" if it can't find it out.
		# If using your own account for example, it's your name.
		self.bot_name = "_Bot"
		self.get_bot_name()

	def get_bot_name(self):
		''' Goes through the conversations to try to find out who it is.
			If not called, the bot name will be considered "_Bot" unless manually changed.

			Returns the name the bot thinks it has, which won't change if it can't find it out.
		
		'''

		cl = self.get_conversations()

		pl = []
		for c in cl:
			pl2 = self.get_participants(c.link)

			if (pl != []):

				pl3 = []
				for p in pl2:
					if (p in pl):
						pl3.append(p)
				pl = pl3
			else:
				pl = pl2

			if (len(pl) == 1):
				self.bot_name = pl[0]
				self.debug_log(f"Bot name: {self.bot_name}")
				break
		
		return self.bot_name

	def is_logged_in(self):
		''' Returns True if an account is logged in.

		'''

		# I've never seen this failing, but I can imagine it happening.
		return "https://www.messenger.com/t/" in self.driver.current_url

	def login(self, email="", password=""):
		''' Tries to log in, if already in an account, logs out first.

			If no credentials are given, default ones are used.
			If default credentials are also blank, that's the user's fault, for calling this method without arguments.

		'''

		if (email == ""):
			email = self.default_email
		if (password == ""):
			password = self.default_password

		# If already logged in, log out.
		if (self.is_logged_in()):
			self.debug_log(f"Currently logged in, logging out.")
			self.logout()

		self.debug_log("Going to Messenger.com...")
		self.driver.get("https://www.messenger.com/login/")

		WebDriverWait(self.driver, self.ajax_time).until(expected_conditions.element_to_be_clickable((By.ID, "email")))

		self.debug_log("Logging in...")

		# Write email and password, then log in.
		email_in = self.driver.find_element_by_id("email")
		email_in.clear()
		email_in.send_keys(email)
		pass_in = self.driver.find_element_by_id("pass")
		pass_in.clear()
		pass_in.send_keys(password)
		self.driver.find_element_by_id("loginbutton").click()

		self._wait_messages()
		self._mark_messages_as_seen()

	def logout(self):
		''' Tries to log out of the current account.

		'''

		# Sometimes it can't log out if you don't do this, I don't get it either.
		WebDriverWait(self.driver, self.ajax_time).until(expected_conditions.presence_of_element_located((By.ID, "settings")))

		# Find settings button, then the Exit button.
		self.driver.find_element_by_id("settings").find_element_by_xpath("..").click()
		self.driver.find_elements_by_class_name("_54nh")[-1].click()

		return True

	def get_conversations(self):
		''' Returns a list of conversations on the side bar, in the form of Conversation objects.

			They contain a name and a link, the link is used in set_conversation() or other methods taking conversations as arguments.

		'''

		el = self.driver.find_elements_by_css_selector("._5l-3._1ht1._6zk9")

		if (len(el) == 0):
			return []

		r = []
		for e in el:
			link = e.find_element_by_css_selector("a._1ht5._2il3._6zka._5l-3._3itx").get_attribute("data-href").split("/")[-1]
			name = e.find_element_by_css_selector("._1qt3._6-5k._5l-3").get_attribute("data-tooltip-content")
			r.append(Conversation(name, link))
		
		return r

	def get_participants(self, conversation=""):
		''' Returns a list of participants in the current/desired conversation, in the form of names (nicknames ignored).

			It might need to open the nickname menu, specifically if it's not a group conversation.
			Because of that, calling this method in a group is a little faster.

			If it can't get to the desired conversation, returns an empty list.

		'''

		if (not self.set_conversation(conversation)):
			return []

		if (self.is_group_conversation()):
			# Group conversation.

			# Read names on the side, easy.
			el = self.driver.find_elements_by_class_name("_8slc")
			r = []
			for e in el:
				r.append(e.text)

			return r
		else:
			# One on one conversation.

			# Open nicknames, then read names listed there.
			self.driver.find_element_by_id("pencil-underline").click()
			el = self.driver.find_elements_by_css_selector("._44kr._5l37")
			r = []
			for e in el:
				if (len(e.find_elements_by_class_name("_3q35")) == 1):
					r.append(e.find_element_by_class_name("_3q35").text)
				else:
					r.append(e.find_element_by_class_name("_8slc").text)

			self.driver.find_element_by_class_name("layerCancel").click()

			return r

	def set_conversation(self, link):
		''' This method tries to set the conversation to whatever is requested, works with the part of the link after /t/.
			It was designed to be called every time you want to make sure you're at a certain conversation.

			Some methods will call this if you pass a conversation argument.

			Returns True if it was successful and False if it fails.

		'''

		if (link == "" or self.driver.current_url == f"https://www.messenger.com/t/{link}"):
			return True
		
		self.debug_log(f"Trying to go to conversation {link}...")
		self.driver.get(f"https://www.messenger.com/t/{link}")

		self._wait_messages()
		self._mark_messages_as_seen()

		if (self.driver.current_url == f"https://www.messenger.com/t/{link}"):
			self.debug_log(f"Sucessfully got into a conversation with {link}.")
			return True
		else:
			self.debug_log("Couldn't go to the desired conversation.")
			return False

	def is_group_conversation(self):
		''' True if the conversation is a group conversation.
		
		'''
		return len(self.driver.find_elements_by_class_name("_2v6o")) == 0

	def refresh(self):
		''' ...Refreshes.
		
		'''

		self.driver.refresh()
		self._wait_messages()
		self._mark_messages_as_seen()

	def quit(self):
		''' Quits the browser.

			Call this to close the window and allow the program to end.

		'''
		self.driver.quit()

	def send_message(self, message, conversation=""):
		''' Sends a message to a certain conversation.
			If no conversation is given, it'll send the message on whatever conversation it is in at the moment.

			It's heavily recommended to give a conversation so the bot makes sure it's sent there.

		'''

		# If it can't get to the desired conversation, it returns False and doesn't send anything.
		if (not self.set_conversation(conversation)):
			return False

		conversation = self.driver.current_url.split("/")[-1]

		# Selects the text box, then clears it.
		self.driver.find_element_by_css_selector("._kmc._7kpg").click()
		actions = ActionChains(self.driver)
		actions.key_down(Keys.CONTROL)
		actions.send_keys("a")
		actions.key_up(Keys.CONTROL)
		actions.send_keys(Keys.BACKSPACE)
		actions.perform()

		# This is a hack to deal with mentions, hopefully won't be there for long.
		kl = message.split("\t")
		for i in range(len(kl) - 1):
			kl.insert(i*2 + 1, Keys.TAB)


		# If safe mode is enabled, don't actually send anything, but still write it.
		if (self.safe_mode):
			self.debug_log(f"[SAFE MODE] To {conversation}: {message}")
		else:
			self.debug_log(f"To {conversation}: {message}")
			kl.append(Keys.ENTER)

		# Store here just so it isn't called multiple times.
		group = self.is_group_conversation()

		for k in kl:
			# If not in a group, we should never press tab. Again, it's a hack, and it's terrible.
			if (k == Keys.TAB and not group):
				continue
			actions = ActionChains(self.driver)
			actions.send_keys(k)
			actions.perform()
			time.sleep(.05)
		
		return True

	def new_messages(self):
		''' The amount of unread messages, or the total amount if message marking is disabled.

			This is the recommended method of checking if there's new messages before reading them, as it's pretty fast.

			Read only.
		
		'''

		return len(self.driver.find_elements_by_css_selector(f"._3oh-._58nk:not([seen])"))

	def last_message(self):
		''' The last message sent in the current conversation.

			Way faster than listing all messages.

		'''
		ml = self._fetch_messages_detail(filters="", message_group_list=[self.driver.find_elements_by_css_selector(".__i_._7i2k > div[id^='js'] > div")[-1]])
		return ml[-1]

	def messages_detailed(self, conversation="", unseen_only=True, grouped=False):
		''' Returns a list of messages/message groups if grouped given is True.

			If it can't get to the desired conversation, returns an empty list.

			By default only shows unseen messages, if message marking is disabled it'll still return all messages.

		'''

		filters = ""
		if (unseen_only):
			filters += ":not([seen])"

		if (not self.set_conversation(conversation)):
			return []

		r = self._fetch_messages_detail(filters=filters, grouped=grouped)

		return r

	def messages_text(self, conversation="", unseen_only=True):
		''' Returns a list of messages in string form, containing their text content.

			Runs faster than messages_detailed, made for situations where the text is the only important thing.

			If it can't get to the desired conversation, returns an empty list.
			It can optionally only show unseen messages, if message marking is disabled it'll still return all messages.

		'''

		filters = ""
		if (unseen_only):
			filters += ":not([seen])"

		if (not self.set_conversation(conversation)):
			return []

		r = self._fetch_messages_text(filters=filters)
		return r

	def _message_list(self, ml, filters="", author=None):
		''' Internal method to get messages from a given list of message elements in HTML.

			Shouldn't ever be used outside of the class.
			Only exists because it's used in two different situations and the code is the same.

		'''

		r = []
		mrl = []

		for m in ml:

			# If there's no text on the message or it doesn't meet the attributes requirement, we ignore it completely.
			if (len(m.find_elements_by_css_selector(f"._3oh-._58nk{filters}")) == 0):
				continue

			# _pye is a quote, shown when responding to another message.
			# We use the same method as before to check if it exists.
			ql = m.find_elements_by_css_selector("._pye")

			quote_text = ""

			# I'm assuming this number will never be bigger than 1.
			if (len(ql) == 1):
				mel = m.find_elements_by_css_selector("._4k7e._4ik4._4ik5>span>*")
				for me in mel:
					if (me.tag_name == "br"):
						quote_text += "\n"
					elif (me.tag_name == "span"):
						quote_text += me.get_attribute("textContent")

			mt = m.find_element_by_css_selector(f"._3oh-._58nk{filters}")
			mrl.append(mt)

			r.append(Message(mt.text, quote_text, author))

		self._mark_messages_as_seen(mrl)

		return r

	def _fetch_messages_detail(self, filters="", message_group_list=None, grouped=False):
		''' Internal method to read messages in the chat.

			DON'T use this method, it doesn't guarantee it'll return the same thing every time.
			Any update might break it completely.

			For reading messages, use messages_detailed().

		'''

		self._wait_messages()

		if (message_group_list):
			mgl = message_group_list
		else:
			mgl = self.driver.find_elements_by_css_selector(".__i_._7i2k > div[id^='js'] > div")

		r = []
		for mg in mgl:

			author = ""
			ml = []

			# Finds list of messages in message group made by the bot himself (on the right of the screen).
			bml = mg.find_elements_by_css_selector(".clearfix._o46._3erg._3i_m._nd_.direction_ltr.text_align_ltr")

			if (len(bml) > 0):

				# If this list has any element at all, the bot was the author.
				author = self.bot_name
				if (grouped):
					ml = self._message_list(bml, filters)
				else:
					r.extend(self._message_list(bml, filters, author))

			else:

				# If the message group is not from the bot.
				author = mg.find_element_by_css_selector("._4ldz._1t_r._p").get_attribute("data-tooltip-content")
				oml = mg.find_elements_by_css_selector(".clearfix._o46._3erg._29_7.direction_ltr.text_align_ltr")
				
				if (grouped):
					ml = self._message_list(oml, filters)
				else:
					r.extend(self._message_list(oml, filters, author))

			# If the message group seems fine, we create it.
			if (grouped and len(ml) > 0 and author != ""):
				r.append(MessageGroup(author, ml))

		self._delete_messages()

		return r
		
	def _fetch_messages_text(self, filters=""):
		''' Internal method to read messages in the chat.

			DON'T use this method, it doesn't guarantee it'll return the same thing every time.
			Any update might break it completely.

			For reading plain text from messages, use messages_text().

		'''

		self._wait_messages()

		ml = self.driver.find_elements_by_css_selector(f"._3oh-._58nk{filters}")
		self._mark_messages_as_seen(ml)

		r = []
		for m in ml:
			r.append(m.text)

		self._delete_messages()

		return r

	def _mark_messages_as_seen(self, message_list=None):
		''' Internal method to put an attribute on messages given, marking them as seen by the bot.
			This method won't do anything if this functionality is disabled (it's enabled by default).

			Runs a javascript line of code, which may make the program run slower.
		
		'''
		if (self.mark_seen_messages):
			if (message_list is not None):
				self.driver.execute_script("arguments[0].forEach(e => e.setAttribute('seen', 'yes'));", message_list)
			else:
				self.driver.execute_script("document.querySelectorAll('._3oh-._58nk').forEach(e => e.setAttribute('seen', 'yes'));")

	def _wait_messages(self):
		''' Internal method to wait for messages to load.

		'''

		WebDriverWait(self.driver, self.ajax_time).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "._3oh-._58nk")))
		time.sleep(0.1)

	def _delete_messages(self):
		''' Internal method to delete messages if there's more than a certain amount of them.
		
		'''
		if (self.auto_delete_messages != 0):
			self.driver.execute_script("var l = document.querySelectorAll(\".__i_._7i2k > div[id^='js'] > div\"); if (l.length > arguments[0]) for (let i = 0; i < l.length - arguments[0]; i ++) l[i].remove()", self.auto_delete_messages)
	
	def _find_commands(self):
		''' Finds commands in the object.

			...Don't call this manually.
		
		'''
		for _, value in inspect.getmembers(self):
			if (isinstance(value, BotCommand)):
				self.commands.append(value)

	def handle_commands(self, unseen_only=True):
		''' Checks messages and find commands, then executes them.

			If, for whatever reason, more than one command fits, only the first will run.

			Returns a detailed message list, for convenience in case it's useful later in the code.
		
		'''

		# This is a complicated one, so I'll try to explain everything.
		# Yes, I realise it's trash and there's likely ways of making it more readable, it's how I managed to do it, ok?

		# First we read messages and make an empty command list.
		ml = self.messages_detailed(unseen_only=unseen_only)
		cl = []

		# If we aren't in a group conversation, the bot doesn't need to be called with prefixes or suffixes.
		# We assume all messages are a potential command.
		if (not self.is_group_conversation()):

			# Simply go through every message and add it as a command.
			for m in ml:

				# Check if the bot wasn't the one sending the message, we don't want it to call itself forever.
				if (m.author != self.bot_name or self.self_commands or len(self.get_participants()) == 1):
					self.debug_log("Command received: ", [m, m.text.strip(), m.text.split()])
					cl.append(Command(m, m.text.strip()))

		else:
			for m in ml:
				if (m.author != self.bot_name or self.self_commands):
					add = False

					# We make the message text lower case so it's case insensitive.
					# We also remove common punctuation and line break.
					# The line break here is actually a hack to deal with mentions.
					text = m.text.lower().translate(str.maketrans("", "", "\n.,!?'"))
					command_text = ""

					# Check if a prefix is found.
					for p in self.command_prefixes:
						if (text.startswith(p.format(bot=self.bot_name).lower())):
							add = True

							# This removes the prefix, then removes spaces around the resulting string.
							command_text = m.text[len(p.format(bot=self.bot_name)):].strip()
							break

					# Check if a suffix is found.
					if (not add):
						for s in self.command_suffixes:
							if (text.endswith(s.format(bot=self.bot_name).lower())):
								add = True

								# This removes the suffix, then removes spaces around the resulting string.
								command_text = m.text[:len(m.text) - len(s.format(bot=self.bot_name))].strip()
								break

					if (add):
						self.debug_log("Command received: ", [m, command_text, command_text.split()])
						cl.append(Command(m, command_text))
				
		# Now go through every potential command we found, check if it starts with the one of the names of a command, and call it if so.
		# Totally not overly complicated at all.
		for c in cl:
			done = False
			text = c.command_text.lower()
			for comm in self.commands:
				for n in comm.names:
					if (text.startswith(n.lower() + " ") or text == n.lower()):
						c.args = c.command_text[len(n):].split()

						try:
							comm._call(self, c)
						except Exception as e:
							self.debug_log(e)

						done = True
						break
				if (done):
					break
		
		return ml

	def debug_log(self, *args):
		''' Override this method if you desire the log messages to go somewhere else, or nowhere at all.
		
		'''
		print(*args)