from web_tracker_imot.services.notifier_service import EmailConfig, EmailNotifier


class DummySMTP:
    def __init__(self, host: str, port: int, timeout: int = 15) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = False
        self.sent_messages = []

    def __enter__(self) -> "DummySMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.logged_in = True

    def send_message(self, msg) -> None:
        self.sent_messages.append(msg)


def test_email_notifier_dry_run_does_not_send(monkeypatch) -> None:
    # ако е dry_run, SMTP не трябва да се вика
    def fail_smtp(*args, **kwargs):
        raise AssertionError("SMTP should not be called in dry_run mode")

    monkeypatch.setattr("web_tracker_imot.services.notifier_service.smtplib.SMTP", fail_smtp)

    cfg = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="u",
        password="p",
        from_addr="from@example.com",
        to_addr="to@example.com",
        dry_run=True,
    )

    n = EmailNotifier(cfg)
    n.notify_changed(title="Test", url="https://example.com", old_value="1", new_value="2")


def test_email_notifier_sends_when_enabled(monkeypatch) -> None:
    dummy = DummySMTP("smtp.example.com", 587)

    def smtp_factory(host: str, port: int, timeout: int = 15):
        # връщаме същия dummy обект за да проверим какво е пратено
        return dummy

    monkeypatch.setattr("web_tracker_imot.services.notifier_service.smtplib.SMTP", smtp_factory)

    cfg = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="u",
        password="p",
        from_addr="from@example.com",
        to_addr="to@example.com",
        dry_run=False,
        use_tls=True,
    )

    n = EmailNotifier(cfg)
    n.notify_changed(title="Title", url="https://example.com/x", old_value="OLD", new_value="NEW")

    assert dummy.started_tls is True
    assert dummy.logged_in is True
    assert len(dummy.sent_messages) == 1
    msg = dummy.sent_messages[0]
    assert "Changed" in msg["Subject"]