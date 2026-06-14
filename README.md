BookieBot
=========

A plugin for the [Err chatbot](https://github.com/gbin/err) that tracks world cup football matches, takes scores and awards points. Originally developed for HipChat, it's currently set up for Mattermost but should work with any protocol (XMPP/Jabber/IRC).

Requirements
------------

Python 3.12 (later versions seem to cause issues, for now)

Installing
----------

[`uv`](https://docs.astral.sh/uv/) is recommended as it makes packaging pretty easy. Run the following steps in a dedicated directory.

### Installing errbot

```
uv init
uv add errbot
uv run errbot --init
```

The last command adds a basic `config.py` configuration file that we'll fill out next.

### Add backend

Add [backend of your choice](https://errbot.readthedocs.io/en/latest/user_guide/setup.html#id1). For example, to add Mattermost:

```
git clone git@github.com:errbotio/err-backend-mattermost.git backend-plugins/err-backend-mattermost
uv add mattermostdriver
```

> [!WARNING]
> [`mattermostdriver`](https://github.com/Vaelor/python-mattermost-driver) has a [bug that hasn't been fixed in a while](https://github.com/Vaelor/python-mattermost-driver/issues/115):
>
> ```
> nano .venv/lib/python3.xx/site-packages/mattermostdriver/websocket.py
> ```
>
> Modify L29 to read:
>
> ```
> context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
> ```

### Add the Bookiebot plugin

```
git clone git@github.com:foxxyz/bookiebot.git plugins/bookiebot
```

### Configuring

Ensure the following config variables are set in `config.py`:

* `BACKEND`: `Mattermost` (or backend of your choice)
* `BOT_ADMINS`: ID for your account (E.G. `123456_123456@chat.hipchat.com` or `@username`)
* `BOT_IDENTITY`: Set `team`, `server` and `token` for MatterMost, or check your specific backend for appropriate keys.

Ensure the following settings are set in `plugins/bookiebot/lib/settings.py`:

* `API_KEY`: football-data.org API key (free)
* `MAIN_ROOM`: Target room to make announcements in (E.G. `~town-square` or `@username`)

Bookiebot should now be ready to go:

```
uv run errbot
```

Notes
=====

BookieBot automatically polls football-data.org every so often to check for new matches, as well as final scores for ongoing matches. Right now this can't be turned off.

BookieBot can only track football (don't use the "s" word) scores, but the Score class could easily be modified or extended to handle any sports' scores.

Last words
==========

Fuck FIFA. The world cup is a great tournament that deserves better.
