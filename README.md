![badge: python](https://img.shields.io/badge/Lang-Python-informational?style=for-the-badge&logo=Python&logoColor=white&color=fcd132)

Why is there a webdriver, a webscraper, and extra e-mail client??


# webscraping automations for IServ
<b>Add the missing dotenv and config files before running.<br/>
_CREDGEN.PY_ does most of the work.</b>

- ./IScrA/.env
  - username
- ./IScrA/config.ini
  - base domain
  - ports (imap, smtp)
- ./IScrA/subject.ini
  - subject keywords for guessing the subjects of exercises
- ./app/config/MainWindow.ini
  - initial window size and position

## Features
- <b>webdriver</b>
  - tasks
  - texts
  - files
  - messenger rooms
- <b>mailer</b>
  - sending (scheduled) mails using SMTP
  - received mails using IMAP4
- <b>scraper</b>
  - retrieving the users csrf token
  - fetching pending exercises
  - checking if new exercises have been assigned

## \_\_main__.py
- processes mail schedule 
- launches ui
