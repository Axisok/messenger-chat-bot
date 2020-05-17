from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import platform

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
	def __init__(self, text, quote_text):
		self.text = text
		self.quote_text = quote_text
		
	def __repr__(self):
		if (self.quote_text != ""):
			return f"> {self.quote_text} | {self.text}"
		else:
			return f"{self.text}"

class MessengerBot:
	''' Class to control a Chrome driver and read/write information on Messenger conversations.

	'''

	def __init__(self, safe_mode=False, default_email="", default_password="", ajax_time=1.5):
		print("Starting bot...")
		self.driver = webdriver.Chrome("chromedriver.exe")
		self.safe_mode = safe_mode
			
		self.ajax_time = ajax_time

		self.default_email = default_email
		self.default_password = default_password
		if (self.default_email != "" and self.default_password != ""):
			self.login()

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
			print(f"Currently logged in, logging out.")
			self.logout()

		print("Going to Messenger.com...")
		self.driver.get("https://www.messenger.com/login/")

		# We could definitely do something fancier, but this does the job and can be adjusted so I'm fine with it.
		time.sleep(self.ajax_time)

		print("Logging in...")
		# Write email and password, then log in.
		email_in = self.driver.find_element_by_xpath("//*[@id=\"email\"]")
		email_in.clear()
		email_in.send_keys(email)
		pass_in = self.driver.find_element_by_xpath("//*[@id=\"pass\"]")
		pass_in.clear()
		pass_in.send_keys(password)
		self.driver.find_element_by_xpath("//*[@id=\"loginbutton\"]").click()

	def logout(self):
		''' Tries to log out of the current account.

		'''

		# Sometimes it can't log out if you don't do this, I don't get it either.
		time.sleep(self.ajax_time)

		# Find settings button, then the Exit button.
		self.driver.find_element_by_xpath("//*[@id=\"settings\"]").find_element_by_xpath("..").click()
		self.driver.find_elements_by_class_name("_54nh")[-1].click()

		return True

	def set_conversation(self, link):
		''' This method tries to set the conversation to whatever is requested, works with the part of the link after /t/.
			It was designed to be called every time you want to make sure you're at a certain conversation.

			Some methods will call this if you pass a conversation argument.

			Returns True if it was successful and False if it fails.

		'''

		if (link == "" or self.driver.current_url == f"https://www.messenger.com/t/{link}"):
			return True
		
		print(f"Trying to go to conversation {link}...")
		self.driver.get(f"https://www.messenger.com/t/{link}")

		# Waits for messages to load.
		time.sleep(self.ajax_time)

		if (self.driver.current_url == f"https://www.messenger.com/t/{link}"):
			print(f"Sucessfully got into a conversation with {link}.")
			return True
		else:
			print("Couldn't go to the desired conversation.")
			return False

	def send_message(self, message, conversation=""):
		''' Sends a message to a certain conversation.
			If no conversation is given, it'll send the message on whatever conversation it is in at the moment.

			It's heavily recommended to give a conversation so the bot makes sure it's sent there.

		'''

		# If it can't get to the desired conversation, it returns False and doesn't send anything.
		if (not self.set_conversation(conversation)):
			return False

		conversation = self.driver.current_url.split("/")[-1]

		# If safe mode is enabled, don't actually send anything.
		if (self.safe_mode):
			print(f"[SAFE MODE] To {conversation}: {message}")
			return True

		# Writes the message, sends it, and logs it on the console.
		self.driver.find_element_by_css_selector("._kmc._7kpg").click()

		actions = ActionChains(self.driver)
		actions.send_keys(message, Keys.ENTER)
		actions.perform()
		print(f"To {conversation}: {message}")
		
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

		if (len(self.driver.find_elements_by_class_name("_2v6o")) == 0):
			el = self.driver.find_elements_by_class_name("_8slc")
			r = []
			for e in el:
				r.append(e.text)

			return r
		else:
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

	def _message_list(self, ml):
		''' Internal method to get messages from a given list of message elements in HTML.

			Shouldn't ever be used outside of the class.
			Only exists because it's used in two different situations and the code is the same.

		'''

		r = []

		for m in ml:
			# If there's no text on the message, we ignore it completely.
			if (len(m.find_elements_by_css_selector("._3oh-._58nk")) == 0):
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
		
			r.append(Message(m.find_element_by_css_selector("._3oh-._58nk").text, quote_text))

		return r




	def _fetch_messages_detail(self):
		''' Internal method to read messages in the chat.

			DON'T use this method, it doesn't guarantee it'll return the same thing every time.
			Any update might break it completely.

			For reading messages, use messages_detail().

		'''

		print("Fetching details from messages...")
		mgl = self.driver.find_elements_by_css_selector(".__i_._7i2k #js_1 > div")

		r = []
		for mg in mgl:

			author = ""
			ml = []

			# Finds list of messages in message group made by the bot himself (on the right of the screen).
			bml = mg.find_elements_by_css_selector(".clearfix._o46._3erg._3i_m._nd_.direction_ltr.text_align_ltr")

			if (len(bml) > 0):
				# If this list has any element at all, the bot was the author.
				author = "_Bot"
				ml = self._message_list(bml)

			else:
				# If the message group is not from the bot.
				author = mg.find_element_by_css_selector("._4ldz._1t_r._p").get_attribute("data-tooltip-content")
				ml = self._message_list(mg.find_elements_by_css_selector(".clearfix._o46._3erg._29_7.direction_ltr.text_align_ltr"))

			# If the message group seems fine, we create it.
			if (len(ml) > 0 and author != ""):
				r.append(MessageGroup(author, ml))

		return r
		

	def _fetch_messages_text(self):
		''' Internal method to read messages in the chat.

			DON'T use this method, it doesn't guarantee it'll return the same thing every time.
			Any update might break it completely.

			For reading text from messages, use messages_text().

		'''

		print("Fetching text from messages...")
		ml = self.driver.find_elements_by_css_selector("._3oh-._58nk")

		r = []
		for m in ml:
			r.append(m.text)

		return r

	def messages_detailed(self, conversation=""):
		''' Returns a list of messages in string form, containing their text content.

			Runs faster than other methods, made for situations where the text is the only important thing.

			If it can't get to the desired conversation, returns an empty list.

		'''
		if (not self.set_conversation(conversation)):
			return []

		return self._fetch_messages_detail()

	def messages_text(self, conversation=""):
		''' Returns a list of messages in string form, containing their text content.

			Runs faster than other methods, made for situations where the text is the only important thing.

			If it can't get to the desired conversation, returns an empty list.

		'''
		if (not self.set_conversation(conversation)):
			return []

		return self._fetch_messages_text()

	def quit(self):
		''' Quits the browser.

			Call this to close the window and allow the program to end.

		'''
		self.driver.quit()
		