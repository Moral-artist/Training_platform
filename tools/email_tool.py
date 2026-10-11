"""SMTP 587 默认 STARTTLS；465 使用 SMTP_USE_SSL=true。邮件包含三种语言说明。"""

import smtplib, ssl
from email.message import EmailMessage
from data_model.config import settings


def send_verify_email(to_email: str, code: str, tag: str = "register"):
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        raise RuntimeError("Email service is not configured")
    message = EmailMessage()
    message["Subject"] = "Training Platform — Verification code / 验证码 / รหัสยืนยัน"
    message["From"] = settings.SMTP_FROM or settings.SMTP_USER
    message["To"] = to_email
    purpose = (
        "Password reset / 重置密码 / รีเซ็ตรหัสผ่าน"
        if tag == "reset"
        else "Registration / 注册 / ลงทะเบียน"
    )
    message.set_content(
        f"{purpose}\n\n{code}\n\nValid for 5 minutes. Do not share this code.\n五分钟内有效，请勿分享验证码。\nรหัสมีอายุ 5 นาที โปรดอย่าเปิดเผยรหัส\n"
    )
    factory = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
    kwargs = {"context": ssl.create_default_context()} if settings.SMTP_USE_SSL else {}
    with factory(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15, **kwargs) as smtp:
        if not settings.SMTP_USE_SSL:
            smtp.starttls(context=ssl.create_default_context())
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)
