import logging
from logging.config import fileConfig

from dateutil import tz
from datetime import datetime, timedelta
from os import walk, remove, replace

from plyer import notification

from auth import authenticate
import mail

import sys
from PyQt6.QtCore import Qt
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


def send_and_reschedule_scheduled_mails(iserv_username: str, iserv_password: str) -> None:
    """sEndS aNd ResChEduLEs schEdUleD mAiLs"""
    my_transmitter = mail.Transmitter(iserv_username=iserv_username, iserv_password=iserv_password)

    mail_schedule_file = open('./data/mail/schedule/schedule.txt', mode='r', encoding='utf-8')
    new_mail_schedule_file = open('./data/mail/schedule/new_schedule.txt', mode='w', encoding='utf-8')

    # read the mail schedule line by line (and therefore mail by mail)
    while scheduled_mail := mail_schedule_file.readline().strip():
        now = datetime.now(tz=tz.tzlocal())  # get the exact time for every mail; very likely unnecessary

        if ((scheduled_for := datetime.strptime(scheduled_mail.split(' | ')[1], '%d-%m-%Y_-_%H-%M-%S')
                .replace(tzinfo=tz.gettz(scheduled_mail.split(' | ')[0]))) - now).total_seconds() > 0:
            # the mail is to be sent in the future
            new_mail_schedule_file.write(f'{scheduled_mail}\n')
            continue

        # the difference the time for which the mail has been scheduled and now (timedelta) is negative or equal to zero
        # send the mail
        scheduled_mail = scheduled_mail.split(' | ')
        mail_template_content_type, mail_template = scheduled_mail[4].split('/')

        if mail_template_content_type not in ['plaintext', 'html']:
            # dump the failed scheduled mails into a text file
            failed_mails_file = open('./data/mail/schedule/failed.txt', mode='a', encoding='utf-8')
            failed_mails_file.write(f'{scheduled_mail}\n')
            failed_mails_file.close()
            # do not raise an exception, mark the wrongly scheduled mail as failed and continue with the next one
            logger.exception('There is an invalid template type defined for a mail in the schedule.txt. '
                             'The bad mail definition has been dumped into a "failed.txt" file in the same directory.')
            continue

        # send the scheduled mail
        my_transmitter.send_mail_template(
            to_user=scheduled_mail[2],
            subject=scheduled_mail[3],
            template=mail_template,
            formatted_template=True if mail_template_content_type == 'html' else False,
            attachments=scheduled_mail[6:len(scheduled_mail)]
        )
        # inform the user that a mail has been sent
        logger.info(f'A mail has been sent to "{scheduled_mail[2]}". Subject of the mail: "{scheduled_mail[3]}"')
        notification.notify(
            title='IServ Mails',
            message=f'A mail has been sent to "{scheduled_mail[2]}". \nSubject of the mail: "{scheduled_mail[3]}"',
            app_name='IScrA',
            app_icon='./assets/icon/send.ico',
            timeout=3,
        )

        if scheduled_mail[5].split(' ')[0] == 'repeat':
            # if the mail is to be repeated, calculate when it is to be sent next and append it to the new schedule
            repeat_in_timedelta = scheduled_mail[5].split(' ')[1].split('-')
            scheduled_mail[1] = (scheduled_for + timedelta(
                weeks=int(repeat_in_timedelta[0]),
                days=int(repeat_in_timedelta[1]),
                hours=int(repeat_in_timedelta[2]),
                minutes=int(repeat_in_timedelta[3]),
                seconds=int(repeat_in_timedelta[4])
            )).strftime('%d-%m-%Y_-_%H-%M-%S')
            new_mail_schedule_file.write(f'{" | ".join(scheduled_mail)}\n')

    new_mail_schedule_file.close()
    mail_schedule_file.close()

    # replace the old schedule file with the new one
    replace(src='./data/mail/schedule/new_schedule.txt', dst='./data/mail/schedule/schedule.txt')

    my_transmitter.shutdown()
    del my_transmitter


def launch_app(iserv_username: str, iserv_password: str) -> None:
    q_application = QApplication(sys.argv)
    q_application.setStyleSheet('file:///./app/stylesheet/stylesheet.css')

    q_application_main_window = MainWindow(iserv_username, iserv_password)
    q_application_main_window.show()

    q_application.aboutToQuit.connect(q_application_main_window.shutdown)

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
