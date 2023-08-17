import logging
from logging.config import fileConfig


from datetime import datetime
from os import walk, remove

from auth import authenticate
from mail import ScheduleManager

import sys
from PyQt6.QtWidgets import QApplication
from app.MainWindow import MainWindow


# ----------
# logging
# ----------


"""
----------
USAGE
----------
display output for ordinary cli:
    print()

report events (status monitoring, fault investigation):
    logger.info() or
    logger.debug() for detailed output

issue warnings (particular runtime events):
    issue is avoidable and the code should be modified:
        warnings.warn()
    the event should be noticed, but there is nothing you can do about it:
        logger.warning()

report errors (particular runtime events):
    catch Error/
    raise MostSpecificError()

report suppressed errors without raising exceptions:
    logger.error() or
    logger.exception() or
    logger.critical()
----------
"""

logging.config.fileConfig(
            './logger.ini',
            encoding='utf-8',
            defaults={
                'logfilename':
                    f'./logs/{datetime.now().strftime("%Y-%m-%d_-_%H-%M-%S")}.log'
            }
        )
logger = logging.getLogger(__name__)

# only keep up to 5 log files
logfiles = list(filter(
    lambda file: file.endswith('.log') or file.split('.')[-1].isdigit(),
    next(walk('./logs/'), (None, None, []))[2]
))
if len(logfiles) > 5:
    for logfile in logfiles[0:len(logfiles) - 5]:
        remove(f'./logs/{logfile}')
del logfiles


# ----------
# run configurations
# ----------


def send_and_reschedule_scheduled_mails(iserv_username, iserv_password):
    mail_schedule_manager = ScheduleManager(iserv_username, iserv_password)
    mail_schedule_manager.send_and_reschedule_scheduled_mails()
    mail_schedule_manager.shutdown()


def launch_app(iserv_username: str, iserv_password: str) -> None:
    q_application = QApplication(sys.argv)
    q_application.setApplicationName('IScrA')

    q_application_main_window = MainWindow(iserv_username, iserv_password)
    q_application_main_window.show()

    q_application.exec()


# ----------
# run
# ----------


def main():
    iserv_username, iserv_password = authenticate()

    # handle scheduled mails
    send_and_reschedule_scheduled_mails(iserv_username, iserv_password)

    # start the app
    launch_app(iserv_username, iserv_password)


if __name__ == '__main__':
    main()
