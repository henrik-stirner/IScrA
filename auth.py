from dotenv import load_dotenv
from os import getenv
from getpass import getpass
import keyring


# retrieve the users IServ login credentials
def authenticate() -> tuple[str, str]:
    load_dotenv()

    iserv_username = getenv('ISERV_USERNAME')
    if not iserv_username:
        # aks the user for his username if it is not saved in the dotenv file
        print('\n\nPlease enter your IServ username below.\n----------')
        iserv_username = getpass('user.name: ')
        print('\n\n')

    iserv_password = keyring.get_password('IServ', iserv_username)
    if not iserv_password:
        # aks the user for his password if it is not saved in the keyring
        print('\n\nPlease enter your IServ password below.\n----------')
        iserv_password = getpass('password: ')
        print('\n\n')

    return iserv_username, iserv_password
