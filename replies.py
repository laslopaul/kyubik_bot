"""
Module replies
Contains templates of the bot replies to user messages
"""

# Reply to /info command (shows torrent info)
info = """{}
Status: {}
Size: {}
Downloaded: {} ({})
DL: {}
{}: {}

S/L: {}
Uploaded: {}
UL: {}"""

# Reply to /contents command (shows torrent contents)
contents = """File: {}
Size: {}
Progress: {}"""

# Reply to /stats command (shows traffic info of Qbittorrent)
stats = """Status: {}
DL: {} ({} downloaded this session)
UL: {} ({} uploaded this session)
DHT: {}"""
