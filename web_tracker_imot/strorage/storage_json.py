import json
from dataclasses import asdict
from pathlib import Path
from web_tracker_imot.models.tracked_imot import CriterionType, TrackedItem

class JsonStorage:
    def __init__(self, path: str) -> None:
        self._path=Path(path)
    
    def load_items(self) -> list[TrackedItem]:
        if not self._path.exists():
            return []
        
        data=json.loads(self._path.read_text(encoding="utf-8"))
        items: list[TrackedItem]=[]
        for row in data:
            items.append(
                TrackedItem(
                    id=row["id"],
                    site=row["site"],
                    url=row["url"],
                    criterion_type=CriterionType(row["criterion_type"]),
                    criterion_value=row["criterion_value"],
                    check_interval_sec=int(row["check_interval_sec"]),
                    email_notify=bool(row.get("email_notify", False))
                )
            )
        return items
    
    def save_items(self, items: list[TrackedItem]) -> None:
        payload=[]
        for it in items:
            d=asdict(it)
            d["criterion_type"]=it.criteria_type.value
            payload.append(d)
        
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    