![badge: python](https://img.shields.io/badge/Lang-Python-informational?style=for-the-badge&logo=Python&logoColor=white&color=fcd132)

WORK IN PROGRESS

# IScrA - IServ Scraping Automations
Make sure to add the missing dotenv and config files.
- ./.env
- ./iserv_mailer/iserv_mailer.ini
- ./iserv_scraper/iserv_scraper.ini

## Currently supports...
- ...logging in and out of IServ.
- ...retrieving the users csrf token.
- ...checking if new tasks have been assigned.
- ...sending and scheduling mails.
  - using SMTP
  - Scheduled mails are sent only when the corresponding function is executed. <br/>The program does not run in the background.
- ...fetching received mails.
  - using IMAP4
