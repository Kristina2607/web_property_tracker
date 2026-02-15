from dataclasses import dataclass
from email.message import EmailMessage
import smtplib


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_addr: str
    to_addr: str
    use_tls: bool = True
    dry_run: bool = True  # по default да НЕ праща реални имейли


class EmailNotifier:
    def __init__(self, config: EmailConfig) -> None:
        self._cfg = config

    def notify_changed(self, title: str, url: str, old_value: str, new_value: str) -> None:
        subject = f"[WebTracker] Changed: {title}"
        body = (
            f"Tracked page changed:\n\n"
            f"Title: {title}\n"
            f"URL: {url}\n\n"
            f"Old value: {old_value}\n"
            f"New value: {new_value}\n"
        )
        self._send_email(subject=subject, body=body)

    def _send_email(self, subject: str, body: str) -> None:
        if self._cfg.dry_run:
            print("[EmailNotifier] DRY RUN - would send email:")
            print("Subject:", subject)
            print(body)
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._cfg.from_addr
        msg["To"] = self._cfg.to_addr
        msg.set_content(body)

        with smtplib.SMTP(self._cfg.smtp_host, self._cfg.smtp_port, timeout=15) as server:
            if self._cfg.use_tls:
                server.starttls()
            server.login(self._cfg.username, self._cfg.password)
            server.send_message(msg)