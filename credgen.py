from dotenv import load_dotenv
from os import getenv
from getpass import getpass
import keyring
from configparser import ConfigParser


def get_binary_choice(prompt: str) -> bool:
    while True:
        user_input = input(prompt)

        if user_input.lower() == 'y':
            return True
        if user_input.lower() == 'n':
            return False

        else:
            print('Invalid input. Your input should be "y" or "Y" for YES and "n" or "N" for NO. Please try again.')


# ----------
# MAIN WINDOW INITIAL SIZE AND POSITION
# ./IScrA/app/config/MainWindow.ini
# ----------


def create_main_window_ini() -> None:
    print('Creating ./IScrA/app/config/MainWindow.ini, which contains initial window sizes for the apps main window...')

    with open('./app/config/MainWindow.ini.example', 'r', encoding='utf-8') as main_window_ini_preset:

        with open('./app/config/MainWindow.ini', 'w', encoding='utf-8') as main_window_ini_file:
            main_window_ini_file.write(main_window_ini_preset.read())
            main_window_ini_file.close()

        main_window_ini_preset.close()

    print('Done.')


# ----------
# SUBJECT KEYWORDS
# ./IScrA/subject.ini
# ----------


def create_subject_ini() -> None:
    print('Creating ./IScrA/subject.ini, which contains German keywords to detect subjects of exercises...')

    with open('./subject.ini.example', 'r', encoding='utf-8') as subject_ini_preset:
        with open('./subject.ini', 'w', encoding='utf-8') as subject_ini_file:
            subject_ini_file.write(subject_ini_preset.read())
            subject_ini_file.close()

        subject_ini_preset.close()

    print('Done.')


# ----------
# SERVER DOMAIN; SMTP PORT; IMAP PORT
# ./IScrA/config.ini
# ----------


def create_config_ini() -> None:
    print('Creating ./IScrA/config.ini, which contains everything IServ...')

    config_ini = ConfigParser()
    config_ini.read('./config.ini.example', encoding='utf-8')

    config_ini['server']['domain'] = input(
        'Please enter the BASE domain name of the server which IServ is being run on \n'
        '(wrong: https://domain-name.extension/iserv; right: domain-name.extension): '
    )
    config_ini['port']['smtp'] = input(
        'Please enter the used port of the outgoing mail server (SMTP) \n'
        '(have a look at "https://domain-name.extension/iserv/mail/help/general#help-text"): '
    )
    config_ini['port']['imap'] = input(
        'Please enter the used port of the incoming mail server (IMAP) \n'
        '(have a look at "https://domain-name.extension/iserv/mail/help/general#help-text"): '
    )

    with open('./config.ini', 'w', encoding='utf-8') as config_ini_file:
        config_ini.write(config_ini_file)

    print('Done.')


# ----------
# USERNAME
# ./IScrA/.env
# ----------


def create_dotenv(iserv_username: str) -> None:
    print('Creating ./.env, which contains your IServ username...')

    with open('./.env', 'w', encoding='utf-8') as dotenv_file:
        dotenv_file.write(f"ISERV_USERNAME = 'f{iserv_username}'")

    print('Done.')


def get_store_iserv_username() -> None:
    # ask the user if they want to skip this step
    print(
        'You can skip this step of the setup. \n'
        'If you do so, you will be asked for your username everytime you try to run this app.\n'
        'Your username is needed to store your password in the keyring. '
        'If you do not enter your username, you will not be able to save your password using this script.'
        'However, you will be able to save your password manually. This could be helpful if you want to store multiple'
        'passwords for different usernames to be able to log into multiple IServ accounts.'
    )

    if get_binary_choice('Skip this part of the Setup (y/n)?: '):
        return

    # get username
    print('\n\nPlease enter your IServ username below.\n----------')
    iserv_username = getpass('user.name: ')
    print('\n\n')

    create_dotenv(iserv_username=iserv_username)


# ----------
# PASSWORD
# keyring
# ----------


def get_store_iserv_password() -> None:
    # ask the user if they want to skip this step
    print(
        'You can skip this step of the setup. \n'
        'If you do so, you will be asked for your password everytime you try to run this app.\n'
        'If you enter your password here, it will be stored in your operating system\'s core keyring. '
    )

    if get_binary_choice('Skip this part of the Setup (y/n)?: '):
        return

    # get password
    load_dotenv()
    iserv_username = getenv('ISERV_USERNAME')

    print('\n\nPlease enter your IServ password below.\n----------')
    iserv_password = getpass('password: ')
    print('\n\n')

    keyring.set_password('IServ', iserv_username, iserv_password)

    print(f'Your password is now stored in the keyring. \n(for service name: "IServ", username: "{iserv_username}"')


# ----------
# ICONS
# ./IScrA/assets/icon/missing.txt
# ----------


def inform_about_icons() -> None:
    print(
        '\nAlmost done!\n'
        'The icons that the app uses are missing.'
        'If you want this app to be able to send notifications, please add them in "./IScrA/assets/icon/".\n'
        'You can find a list of missing icons at "./IScrA/assets/icon/missing.txt".'
    )


# ----------
# run
# ----------

def main() -> None:
    create_main_window_ini()
    create_subject_ini()
    create_config_ini()
    get_store_iserv_username()
    get_store_iserv_password()
    inform_about_icons()


if __name__ == '__main__':
    main()
