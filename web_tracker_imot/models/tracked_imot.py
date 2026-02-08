from dataclasses import dataclass
from enum import Enum

class CriterionType(str, Enum):
    CSS="css"
    KEYWORD="keyword"

@dataclass
class TrackedItem:
    id:str
    site:str
    url:str
    criterion_type: CriterionType
    criterion_value: str
    check_interval_sec: int
    email_notify: bool = False