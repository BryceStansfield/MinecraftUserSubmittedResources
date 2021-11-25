NOTE: This was a quick project done at night on a weekend. I can't guarentee that it functions perfectly under all situations, if you encounter anything though feel free to raise an issue or fork.

A web-gui that lets users (with a password) automatically upload texture varients to a servers resource pack

Required config vars (in instance/config.py):
SECRET_KEY = {Your secret key}
RESOURCE_PACK_NAME = {Name of resource pack}
RESOURCE_PACK_DIR = { Folder where resource pack is hosted }
SERVER_PROPERTIES_LOCATION = {Location of server.properties file (for auto-updating hash)}
WEB_ADDRESS = {Resource pack web directory (e.g. www.google.com/minecraft/ if the resource pack lives in www.google.com/minecraft/pack.zip)}
SUBMISSION_PASSWORD = {A submission password of your choice}
ENV='production'

Put your existing resource pack in instance/pack
