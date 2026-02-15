import csv
from pathlib import Path
from web_tracker_imot.models.tracked_imot import TrackedItem, CriterionType

class CsvStorage:
    def __init__(self, filepath:str) ->None:
        self._path=Path(filepath)

    def export_items(self, items: list[TrackedItem]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        with self._path.open("w", newline="", encoding="utf-8") as f:
            writer=csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "site",
                    "url",
                    "criterion_type",
                    "criterion_value",
                    "check_interval_sec",
                    "email_notify"
                ]
            )
            writer.writeheader()
            for i, it in enumerate(items, start=1):
                writer.writerow({
                    "row_num": i,
                    "id": it.id,
                    "site": it.site,
                    "url": it.url,
                    "criterion_type": it.criterion_type.value,
                    "criterion_value": it.criterion_value,
                    "check_interval_sec": it.check_interval_sec,
                    "email_notify": int(it.email_notify),
                })
    
    def import_items(self)->list[TrackedItem]:
        if not self._path.exists():
            return []
        
        out: list[TrackedItem]=[]
        with self._path.open("r", newline="", encoding="utf-8") as f:
            reader=csv.DictReader(f)
            for row in reader:
                out.append(
                    TrackedItem(
                        id=row["id"],
                        site=row["site"],
                        url=row["url"],
                        criterion_type=CriterionType(row["criterion_type"]),
                        criterion_value=row["criterion_value"],
                        check_interval_sec=int(row["check_interval_sec"]),
                        email_notify=bool(int(row["email_notify"]))
                    )
                )
        return out