import smtplib
import ssl
import os
import dotenv
from email.message import EmailMessage
dotenv.load_dotenv()


def send_verify_email(
        to_email:str,
        code:str,):
    with smtplib.SMTP_SSL(
        os.environ['SMTP_HOST'],
        int(os.environ['SMTP_PORT']),
        context=ssl.create_default_context(),
        timeout=5
    ) as smtp:
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.sendmail(
            os.environ['SMTP_USER'],
            to_email,
            f"""You are logining into the Training platform.
            The verify code is {code}.
            The limit time is 15 minutes.""",
        )