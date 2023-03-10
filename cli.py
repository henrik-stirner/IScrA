from version import __version__

import argparse

from plyer import notification
from os import startfile

from auth import authenticate
import mail
import scraper
import webdriver


# ----------
# main parsers
# ----------


parser = argparse.ArgumentParser(
    prog='IScrA',
    description='IServ scraping automations',
    epilog="Thank you for using %(prog)s"
)
subparsers = parser.add_subparsers(
    title='commands',
    help='IScrA subcommands',
    dest='command',
    required=True
)


# ----------
# version command for main parser
# ----------


parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {".".join(__version__)}')


# ----------
# version command as subparser
# ----------


def version(arguments: argparse.Namespace) -> str:
    """returns the current IScrA version"""
    return f'{parser.prog} {".".join(__version__)}'


version_command = subparsers.add_parser('version', help='returns the current IScrA version')
version_command.set_defaults(function=version)


"""
# ----------
# example command
# ----------


def example(arguments: argparse.Namespace) -> str:
    text = arguments.text
    for i in range(arguments.repeat_text):
        text = f'{text}\n{arguments.text}'

    return text


example_command = subparsers.add_parser('example', help='repeats a text')
example_command.set_defaults(function=example)

example_command_arguments = example_command.add_argument_group('arguments')
example_command_arguments.add_argument('text')

example_command_options = example_command.add_argument_group('options')
example_command_options.add_argument('-rt', '--repeat-text', type=int, default=0)
"""


# ----------
# mail command
# ----------


def mail_command_function(arguments: argparse.Namespace) -> str:

    # ----------
    # check for and lazily fetch unread mails
    # ----------

    if arguments.action == 'unread':
        my_receiver = mail.Receiver(*authenticate())

        # get the ids of all the unread mails in the inbox
        selection, mail_ids = my_receiver.get_ids_of_unread_mails()

        if not mail_ids:
            # job is done if there are no unseen mails
            return f'\nThere are no unread mails in your inbox.'

        # inform the user about unread mails
        number_of_unread_mails_info_string = f'There {"is" if len(mail_ids) == 1 else "are"} {len(mail_ids)} unread ' \
                                             f'{"mail" if len(mail_ids) == 1 else "mails"} in your inbox!'
        print(number_of_unread_mails_info_string)
        notification.notify(title='IServ Mails',
                            message=number_of_unread_mails_info_string,
                            app_name='IScrA',
                            app_icon='./assets/icon/mail.ico',
                            timeout=3,)

        i = 1
        for mail_id in mail_ids:
            date, subject, from_sender, to_receiver, body, attachment_data = my_receiver.fetch_mail_content_by_id(
                selection, mail_id)
            # "extract_text_by_mail_id()" is a generator
            # it is not a good idea to download all the unread mails at once and load the into memory

            # log unread mails because I do not want to save them anywhere
            data = f"""
====================
Date: {date}
----------
Subject: {subject}
From: {from_sender}
To: {to_receiver}
----------
{body[0]}
----------
Attachments: 
{', '.join([
    f'{attachment[0]} ({attachment[1]})' for attachment in attachment_data
]) if attachment_data else 'None'}
====================
"""

            print(f'\n\n({i})\n{data}')

            i += 1

        my_receiver.shutdown()
        del my_receiver

        return ''


mail_command = subparsers.add_parser('mail', help='tools for the IServ mail module')
mail_command.set_defaults(function=mail_command_function)

mail_command_arguments = mail_command.add_argument_group('arguments')
mail_command_arguments.add_argument('action', choices=['unread'], help='action to be performed by the client')

# mail_command_options = mail_command.add_argument_group('options')
# mail_command_options.add_argument('-o', '--option', type=int, default=0)


# ----------
# exercise command
# ----------


def exercise(arguments: argparse.Namespace) -> str:

    # ----------
    # checks if the users tasks have changed by comparing the currently pending tasks
    # to the ones that were saved in a textfile the last time the "pending_tasks_changed()" function was called
    #
    # if the tasks changed, the textfile they were saved in will be opened
    # ----------

    if arguments.action == 'new':
        my_scraper = scraper.Scraper(*authenticate())

        if path_to_new_exercise_file := my_scraper.pending_exercises_changed():
            # inform the user that their pending tasks have changed
            notification.notify(title='IServ Exercises',
                                message=f'Your pending IServ-exercises have changed!',
                                app_name='IScrA',
                                app_icon='./assets/icon/notification.ico',
                                timeout=3,)
            # open the new file with a list of the pending tasks
            startfile(path_to_new_exercise_file)

        my_scraper.shutdown()
        del my_scraper

        if path_to_new_exercise_file:
            return f'A new list of your pending exercises has been saved at:\n "{path_to_new_exercise_file}".'
        else:
            return f'Your pending exercises have not changed.'


exercise_command = subparsers.add_parser('exercise', help='tools for the IServ exercise module')
exercise_command.set_defaults(function=exercise)

exercise_command_arguments = exercise_command.add_argument_group('arguments')
exercise_command_arguments.add_argument('action', choices=['new'], help='action to be performed by the client')

# exercise_command_options = exercise_command.add_argument_group('options')
# exercise_command_options.add_argument('-o', '--option', type=int, default=0)


# ----------
# run
# ----------


def main():
    arguments = parser.parse_args()
    result = arguments.function(arguments)

    print(result)


if __name__ == '__main__':
    main()
