import os
from dotenv import load_dotenv
load_dotenv()
TOKEN_TL = os.getenv('TOKEN_TL')

hostDB = os.getenv('hostDB')
userDB = os.getenv('userDB')
passDB = os.getenv('passDB')
dataDB = os.getenv('dataDB')
