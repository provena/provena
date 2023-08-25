import abc
from dataclasses import dataclass
from config import Config
from typing import List, Tuple


@dataclass
class EmailContent():
    subject: str
    body: str


class EmailClient(abc.ABC):
    @abc.abstractmethod
    async def send_email(self, reason: str, email_to: str, email_content: EmailContent) -> None:
        pass

    @abc.abstractmethod
    async def send_emails(self, reason: str, emails: List[Tuple[str, EmailContent]]) -> None:
        pass


