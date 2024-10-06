## About `/bot/` and `mwbot`

### Authorship and attribution
The original `mwbot.py` was provided to me by the author, another contributor to the RuneScape Wikis. Permission was 
given to me to use, modify, and redistribute it, with the request that 
their name not be shared. I've included this notice in order to be clear that
I am not its original author, though the version of the file included in this or other
repositories may or may not be one I modified from the original I was provided.

### Using `mwbot`

Use of `mwbot` requires the inclusion of some supplemental files in the `/bot/` directory:

- `creds.file` should contain the credentials of the wiki account to be associated with the bot's actions. Username 
should be on one line, and password on the next. *Some actions available in `mwbot` may require more advanced account 
permissions on the target wiki.*

- `agent.txt` should contain the string to be used as the user agent for any requests made by the bot. I recommend using
the name of the bot account being used and a way to contact the operator in case of any issues, such as an email address.  