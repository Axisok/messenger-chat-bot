# Messenger Chat Bot
This simple script made in [Python](https://www.python.org/) will allow anyone to easily make a simple (or robust, I didn't try though) bot for Messenger, without any need to deal with the mess that is the Messenger HTML structure.

Heavily inspired by, incredibly, [a Shrek bot](https://github.com/HenryAlbu/FB-Messenger-Whatsapp-Discord-message-spammer).

### Little warning
This bot can be considered against Facebook's terms and using it for spamming/similar doesn't help.
If you get banned it's your own fault.

## What this script is
 - It's a chat bot generalization for Messenger.
 - It's an easy to understand layer when dealing with Messenger interface.
 - It's made to make auto replies/annoucing events/utility (like telling a joke whenever someone asks for one) very simple tasks.

## What it isn't
 - It's not a bot by itself, just makes making one ridiculously easy.
 - It's not designed to be a spam bot, multiple instances will run slowly (and open a browser for each) and the bot itself is pretty slow at most things.
 - It's not made to be annoying, please use it for something people will enjoy or don't at all.
 - It's not perfect and won't last forever, any change at all on the structure of the website and it stops working properly.

## Features
 - [x] Log in and out freely.
 - [x] Send messages on any conversation.
 - [x] Read messages, optionally only reading the text for a faster scan.
 - [x] List all conversations available, including it's name and link (used for changing conversations).
 - [x] List people in a conversation.
 - [x] Optionally get only new messages.
 - [x] Command system (I mean, it kind of works).
 - [ ] Detect and send mentions on messages (you can send mentions, but it's hacky).
 - [ ] Faster typing.
 - [ ] Cooler example (current one doesn't print something made for human eyes, unfortunately).
 - [ ] Deal with emojis (probably won't actually do it).

## Requirements
You need to download a [chrome driver](https://chromedriver.chromium.org/) and put into the folder, as the one here might be outdated.

Requirements are very few and are listed in [the requirements file](requirements.txt).

You can quickly install everything if you have pip and use:
`pip install -r requirements.txt`

## Setup
 - Clone the repository.
 - Install requirements, including an updated chromedriver.exe
 - Import MessengerBot on your Python script.
 - That's all the setup needed, really.

## How to contribute
You don't, fork it if you want to add anything, tell me if you find a bug.

Why can't you?
Well, it's not something worth putting time into, both for you and for me.
I put this project here, but I have no time to manage it properly, only development.

## Example
The [example file](example.py) contains a very simple example showcasing some very basic features.
You can easily insert your credentials there and see the magic happening.

Will be improved on later, probably.

## How to not be banned on Facebook/Messenger
 - Don't use this bot at all if you're worried, I don't guarantee anything.
 - Read their [Terms of Service](https://www.facebook.com/terms.php) very, very, carefully. Don't just trust me, it's a very grey area in the terms.
 - Don't use this bot for spam, Facebook really hates this and Messenger won't be different.
 - Don't use this bot for commercial purposes, Facebook also hates this.
 - Don't create an account for your bot, Facebook only allows one account for person (though I don't think they can find out).

## Some general recommendations
 - Don't save your credentials in plain text, find a way to obfuscate it at least a little so people can't just look at a script and get your account.
 - This works best as a fun and games bot, don't rely on it. It'll break at some point and I may not be able to fix it.
 - Brush your teeth.
 - If you really want a cool bot, use Discord or another bot-friendly chat service.

## License
This software uses the [MIT license](LICENSE), you can use it for whatever purpose you want but I also won't offer any guarantee and you are solely responsible for everything you use it for. This includes breaking [Terms of Service](https://www.facebook.com/terms.php), which might get your account banned temporarily or permanently.
