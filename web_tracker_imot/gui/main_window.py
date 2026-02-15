import tkinter as tk
from queue import Queue, Empty
from tkinter import ttk, messagebox

from web_tracker_imot.models.tracked_imot import TrackedItem
from web_tracker_imot.gui.add_tracked_item_window import AddTrackedItem
from web_tracker_imot.gui.edit_tracked_item_window import EditTrackedItem

from web_tracker_imot.strorage.storage_json import JsonStorage
from web_tracker_imot.strorage.storage_csv import CsvStorage

from web_tracker_imot.services.tracker_service import TrackResult, TrackerService
from web_tracker_imot.services.notifier_service import EmailNotifier, EmailConfig
from web_tracker_imot.services.extractor import extract_value

import matplotlib.pyplot as plt
import re
import os

class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Web Tracker")
        self.geometry("980x520")

        cfg = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="",
        password="",
        from_addr="",
        to_addr="",
        dry_run=True)
        self._notifier = EmailNotifier(cfg)

        self._queue: Queue[TrackResult]=Queue()
        self._tracker=TrackerService(self._queue, extractor=extract_value, notifier=self._notifier)

        self._storage=JsonStorage("data/tracked_items.json")
        self._csv = CsvStorage("data/tracked_items.csv")

        self._items:list[TrackedItem]=self._storage.load_items()
        self._item_by_id: dict[str, TrackedItem]={it.id: it for it in self._items}

        self._history: dict[str, list[tuple[float, str]]] = {}
        self._last_error: dict[str, str] = {}

        self._build_ui()
        self._populate_table()

        self._tracker.set_items(self._items)
        self._tracker.start()

        self.after(300, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)


    def _build_ui(self) -> None:
        top=ttk.Frame(self, padding=10)
        top.pack(fill="both", expand=True)

        toolbar=ttk.Frame(top)
        toolbar.pack(fill="x", pady=(0,8))

        ttk.Button(toolbar, text="Add", command=self._on_add).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Edit", command=self._on_edit).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Delete", command=self._on_delete).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Refresh", command=self._on_refresh).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Save", command=self._on_save).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Export CSV", command=self._on_export_csv).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Import CSV", command=self._on_import_csv).pack(side="left", padx=4)

        columns=("site", "url", "criterion", "interval", "last_value", "status", "error")
        self.tree=ttk.Treeview(top, columns=columns, show="headings", height=18)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_row_double_click)

        self.tree.heading("site", text="Site")
        self.tree.heading("url", text="URL")
        self.tree.heading("criterion", text="Criterion")
        self.tree.heading("interval", text="Interval")
        self.tree.heading("last_value", text="Last value")
        self.tree.heading("status", text="Status")
        self.tree.heading("error", text="Error")

        self.tree.column("site", width=90, anchor="w")
        self.tree.column("url", width=380, anchor="w")
        self.tree.column("criterion", width=160, anchor="w")
        self.tree.column("interval", width=80, anchor="center")
        self.tree.column("last_value", width=160, anchor="w")
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("error", width=220, anchor="w")

    def _populate_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for it in self._items:
            self.tree.insert(
                "",
                "end",
                iid=it.id,
                values=(
                    it.site,
                    it.url,
                    f"{it.criterion_type.value}:{it.criterion_value}",
                    it.check_interval_sec,
                    " ",
                    " ",
                    " "
                ),
            )

    def _upsert_item(self, item:TrackedItem) -> None:
        is_edit=item.id in self._item_by_id
        old_item = self._item_by_id.get(item.id)

        self._item_by_id[item.id]=item
        self._items=list(self._item_by_id.values())

        if is_edit and old_item is not None:
            changed_identity = (
                old_item.url != item.url
                or old_item.site != item.site
                or old_item.criterion_type != item.criterion_type
                or old_item.criterion_value != item.criterion_value
            )
            if changed_identity:
                self._history.pop(item.id, None)
                self._last_error.pop(item.id, None)
        
        if is_edit:
            current=list(self.tree.item(item.id, "values"))
            current[0]=item.site
            current[1]=item.url
            current[2]=f"{item.criterion_type.value}:{item.criterion_value}"
            current[3]=item.check_interval_sec
            self.tree.item(item.id, values=tuple(current))
        else:
            self.tree.insert(
                "",
                "end",
                iid=item.id,
                values=(
                    item.site,
                    item.url,
                    f"{item.criterion_type.value}:{item.criterion_value}",
                    item.check_interval_sec,
                    " ",
                    " ",
                    " "
                ),
            )
        self._tracker.set_items(self._items)
        self._tracker.refresh_now()



    def _on_add(self) -> None:
        AddTrackedItem(self, on_submit=self._upsert_item)

    def _on_edit(self) -> None:
        selected=self.tree.selection()
        if not selected:
            messagebox.showinfo("Edit","Select a row to edit.")
            return
        
        item_id=selected[0]
        existing=self._item_by_id.get(item_id)
        if not existing:
            return

        EditTrackedItem(self, on_submit=self._upsert_item, existing_item=existing)

    def _on_delete(self) -> None:
        selected=self.tree.selection()
        if not selected:
            messagebox.showinfo("Delete","Select a row to delete.")
            return
        
        for lid in selected:
            self.tree.delete(lid)
            self._item_by_id.pop(lid, None)

        self._items=list(self._item_by_id.values())
        self._tracker.set_items(self._items)

    def _on_refresh(self) -> None:
        self._tracker.refresh_now()

    def _on_save(self) -> None:
        self._storage.save_items(self._items)
        messagebox.showinfo("Save", "Saved to data/tracked_items.json")

    def _on_export_csv(self) -> None:
        self._csv.export_items(self._items)
        messagebox.showinfo("Export CSV", "Exported to data/tracked_items.csv")

    def _on_import_csv(self) -> None:
        imported=self._csv.import_items()
        if not imported:
            messagebox.showinfo("Import CSV", "No items found in data/tracked_items.csv")
            return
        
        for it in imported:
            self._item_by_id[it.id]=it

        self._items=list(self._item_by_id.values())

        self._populate_table()
        self._tracker.set_items(self._items)
        self._tracker.refresh_now()

        messagebox.showinfo("Import CSV", f"Imported {len(imported)} items from CSV.")


    def _on_row_double_click(self, event) -> None:
        selected=self.tree.selection()
        if not selected:
            return
        item_id=selected[0]
        self._show_details(item_id)

    def _show_details(self, item_id:str) -> None:
        item = self._item_by_id.get(item_id)
        if not item:
            return

        win = tk.Toplevel(self)
        win.title("Details")
        win.geometry("720x420")

        header = ttk.Frame(win, padding=10)
        header.pack(fill="x")

        ttk.Label(header, text=f"Site: {item.site}").pack(anchor="w")
        ttk.Label(header, text=f"URL: {item.url}").pack(anchor="w")
        ttk.Label(
            header,
            text=f"Criterion: {item.criterion_type.value}:{item.criterion_value}",
        ).pack(anchor="w")

        err = self._last_error.get(item_id)
        if err:
            ttk.Label(header, text=f"Last error: {err}").pack(anchor="w")

        body = ttk.Frame(win, padding=10)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="History (latest last):").pack(anchor="w")

        listbox = tk.Listbox(body, height=14)
        listbox.pack(fill="both", expand=True)

        hist = self._history.get(item_id, [])
        for ts, val in hist[-200:]:
            listbox.insert("end", f"{ts:.0f}  |  {val}")

        btns = ttk.Frame(win, padding=10)
        btns.pack(fill="x")

        ttk.Button(btns, text="Close", command=win.destroy).pack(side="right")

        ttk.Button(btns, text="Plot (if available)", command=lambda: self._plot_history(item_id)).pack(
            side="right", padx=6
        )


    def _poll_queue(self) -> None:
        try:
            while True:
                msg=self._queue.get_nowait()
                print("UI GOT RESULT:", msg)
                self._apply_result(msg)
        except Empty:
            pass
        self.after(300, self._poll_queue)
    

    def _plot_history(self, item_id:str) -> None:
        hist=self._history.get(item_id, [])
        if len(hist)<2:
            messagebox.showinfo("Plot", "Not enough history to plot.")
            return
        
        xs=[ts for ts, _ in hist]
        ys:list[float]=[]
        for _, val in hist:
            num=_first_number(val)
            if num is None:
                messagebox.showinfo("Plot", "Values are not numeric (they cannnot plot).")
                return
            ys.append(num)

        plt.figure()
        plt.plot(xs,ys)
        plt.title("History")
        plt.xlabel("timestamp")
        plt.ylabel("value")
        plt.show()
            

    def _apply_result(self, result: TrackResult) -> None:
        if result.item_id not in self._item_by_id:
            return
        
        item = self._item_by_id[result.item_id]
        current = list(self.tree.item(result.item_id, "values"))

        if result.is_valid:
            old_value = str(current[4]).strip()
            if result.changed and item.email_notify:
                try:
                    title = f"{item.site}"
                    self._notifier.notify_changed(
                    title=title,
                    url=item.url,
                    old_value=old_value if old_value else "(empty)",
                    new_value=str(result.value),
                    )
                except Exception as e:
                    print("[EmailNotifier] ERROR:", e)

            current[4] = result.value
            current[5] = "Changed" if result.changed else "OK"
            current[6] = ""  
            self._history.setdefault(result.item_id, []).append((result.timestamp, result.value))
            self._last_error.pop(result.item_id, None)
        else:
            current[5] = "error"
            current[6] = result.error or "Unknown error"
            self._last_error[result.item_id] = current[6]

        self.tree.item(result.item_id, values=tuple(current))

    def _on_close(self) -> None:
        self._tracker.stop()
        self.destroy()


def _first_number(text: str) -> float|None:
        m = re.search(r"(\d+([.,]\d+)?)", text.replace(" ", ""))
        if not m:
            return None
        return float(m.group(1).replace(",", "."))

