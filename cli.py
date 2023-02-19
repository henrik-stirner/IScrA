import argparse

import core


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


parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {".".join(core.VERSION)}')


# ----------
# version command as subparser
# ----------


def version(arguments: argparse.Namespace) -> str:
    """returns the current IScrA version"""
    return f'{parser.prog} {".".join(core.VERSION)}'


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


def mail(arguments: argparse.Namespace) -> str:
    if arguments.action == 'unread':
        i = 0

        for unread_mail in core.fetch_unread_mails():
            # print(f'\n{unread_mail}\n')
            # the logger in core.py already does the job; however, we still need the for loop to trigger the generator

            # print the number of the mail
            i += 1
            print(f'\n\n({i})\n')

        return f'\nThere is a total of {i} unread mails in your inbox.'


mail_command = subparsers.add_parser('mail', help='tools for the IServ mail module')
mail_command.set_defaults(function=mail)

mail_command_arguments = mail_command.add_argument_group('arguments')
mail_command_arguments.add_argument('action', choices=['unread'], help='action to be performed by the client')

# mail_command_options = mail_command.add_argument_group('options')
# mail_command_options.add_argument('-o', '--option', type=int, default=0)


# ----------
# exercise command
# ----------


def exercise(arguments: argparse.Namespace) -> str:
    if arguments.action == 'new':
        if path_to_new_exercise_file := core.check_for_new_exercises():
            return f'Opening updated exercise table at "{path_to_new_exercise_file}"... '
        else:
            return 'Your pending exercises have not changed.'


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
