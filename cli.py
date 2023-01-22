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
# version command
# ----------


def version(arguments: argparse.Namespace) -> str:
    """returns the current IScrA version"""
    return '.'.join(core.VERSION)


version_command = subparsers.add_parser('version', help='returns the current IScrA version')
version_command.set_defaults(function=version)


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


# ----------
# run
# ----------


def main():
    arguments = parser.parse_args()
    result = arguments.function(arguments)

    print(result)


if __name__ == '__main__':
    main()
