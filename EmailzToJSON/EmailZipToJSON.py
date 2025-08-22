from alive_progress import alive_bar, alive_it
from zipfile import BadZipFile, LargeZipFile
from datetime import datetime
from zipfile import ZipFile as Z
import json
import os
import re



email_path = 'email_logs.zip'
logs_json = {"exported": {}}
content = ''
log_path = 'LOG.txt'
email_fltr = r"(?s)(Subject:.+?)(?=Subject:|$)"
content_fltr = r"(?s)Subject: ?(?P<subject>.+?)\nSender: ?(?P<sender>.+?)\nRecipient: ?(?P<recipient>.+?)\nDate: ?(?P<date>.+?)\nBody:\n?(?P<body>.+?)(?=\n(?:Subject:|Sender:|Recipient:|Date:|Body:|$))(?:\n\(Attachments: ?(?P<attachments>.+?)\)\n)?"


def pretty_time():
    return datetime.now().strftime("%m/%d/%y %H:%M")


def LOGGER(t):
    print(t)
    with open(log_path, 'a+') as LOG:
        LOG.write(f'[{pretty_time()}]\n{t}\n---\n')
        LOG.flush()


def loadEmailZip(path):
    global content

    try:
        with Z(path, 'r') as email_zip:
            filenames = email_zip.namelist()
            bar1 = alive_it(filenames)
            for f in bar1:
                if f.endswith('.txt'):
                    LOGGER(f'- loading "{f}"..\n|')
                    with email_zip.open(f) as txt:
                        t = txt.read().decode('utf-8')
                        LOGGER(f'-- "{t[:60]}..."\n|')
                        content += t + '\n'
                        LOGGER('- done\n|')

                else:
                    LOGGER(f'- skipping {f}..\n')
                    continue

        LOGGER('- content loaded\n')

    except BadZipFile:
        LOGGER('- error: check archive integrity\n')

    except LargeZipFile:
        LOGGER('- warning: large archive\n')
        # handle

    except Exception as e:
        LOGGER(e)

    finally:
        return content


def parse_email(content):
    """
    This function assumes we has seen the structure of our email text logs.
    Knowing the structure of the logs is not a necessarily a requirement.
    This is a PoC that demonstrates one potential method.
    """

    global logs_json

    if not content:
        LOGGER('- no content loaded\n')

    else:
        LOGGER('- extracting from content..\n|')
        emails = re.findall(email_fltr, content)

        for mail in emails:
            LOGGER('-- parsing..\n|')
            parts = re.finditer(content_fltr, mail)
            try:
                for p in parts:
                    subject = p.group("subject")
                    LOGGER(f'--- {subject}\n|')
                    sender = p.group("sender")
                    LOGGER(f'--- {sender}\n|')
                    recipient = p.group("recipient")
                    LOGGER(f'--- {recipient}\n|')
                    date = p.group("date")
                    LOGGER(f'--- {date}\n|')
                    body = p.group("body").strip()
                    LOGGER(f'--- "{body[:60]}.."\n|')
                    attachments = p.group("attachments")
                    LOGGER(f'--- {attachments or "No Attachments"}\n|')

                    if sender:
                        sender = sender.lower()
                        logs_json['exported'].setdefault(sender, [])

                        data = {
                            "date": date,
                            "recipients": [r.lower().strip() for r in recipient.split(',')],
                            "subject": subject,
                            "body": body,
                            "attachments": attachments or 'No Attachments'
                        }

                        logs_json['exported'][sender].append(data)

                LOGGER('-- done\n|')

            except TypeError as e:
                LOGGER(e)
                continue

    LOGGER('-- extraction complete\n|')
    return logs_json


def exportLogs(logs_json):
    LOGGER('-- exporting..\n|')
    with open('email_log.json', 'w+') as log:
        json.dump(logs_json, log)

    LOGGER('\n- EXPORT COMPLETE -\n')

if __name__ == '__main__':
    print(f"""\n\nTasks:\n
    -Extract email logs from a .zip archive.\n
    -Parse the file contents and each email.\n
    -Export email threads to json file
    -Log extraction/export process\n
    ------------------------------------------\n\n""")

    content = loadEmailZip(email_path)
    parsed = parse_email(content)

    print('\nUnique Emails:')
    print(list(parsed['exported'].keys()))

    exportLogs(parsed)

print('END')
