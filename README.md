BookieBot
=========

A plugin for the [Err chatbot](https://github.com/gbin/err) that tracks world cup football matches, takes scores and awards points. Tested and developed for HipChat, but should work with any protocol (XMPP/Jabber/IRC).

# Installing

After setting up _Err_ , you'll need to ensure the following config variables are set in `config.py`:

* `BOT_IDENTITY`: Use "HipChat mode" and set the username, password and token (this needs to be a valid APIv2 token).
* `BOT_ADMINS`: Hipchat ID for your account (`123456_123456@chat.hipchat.com`)
* `CHATROOM_PRESENCE`: Hipchat ID for your announcement room (`12345_room_name@conf.hipchat.com`)
* `CHATROOM_NAME`: Actual Hipchat name of the announcement room ("Room Name")
* `CHATROOM_FN`: Actual Hipchat name of your bot user ("Super Bot")

Start _Err_, then install with:

`!repos install git@github.com:foxxyz/bookiebot.git`

Bookiebot should now be ready to go.

# Notes

BookieBot automatically polls FIFA's website every so often to check for new matches, as well as final scores for ongoing matches. Right now this can't be turned off.

BookieBot can only track football (don't use the "s" word) scores, but the Score class could easily be modified or extended to handle any sports' scores.
