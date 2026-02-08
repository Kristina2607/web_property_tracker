import tkinter as tk
from tkinter import ttk

from web_tracker_imot.gui.add_tracked_item_window import AddTrackedItem
from web_tracker_imot.models.tracked_imot import TrackedItem

class EditTrackedItem(AddTrackedItem):
    def __init__(self, master:tk.Tk, on_submit, existing_item: TrackedItem) -> None:
        super().__init__(master, on_submit=on_submit)
        self.title("Edit tracked item")

        self.var_site.set(existing_item.site)
        self.var_url.set(existing_item.url)
        self.var_crit_type.set(existing_item.criterion_type)
        self.var_crit_value.set(existing_item.criterion_value)
        self.var_interval.set(str(existing_item.check_interval_sec))
        self.var_email.set(bool(existing_item.email_notify))

        self._existing_id=existing_item.id
        self._primary_btn.config(text="Save")
        self._refresh_presets()

        if existing_item.criterion_value.lower().startswith("preset:"):
            self._crit_entry.config(state="disabled")
        else:
            self._crit_entry.config(state="normal")
                        
    def _submit(self) -> None:
        if str(self._crit_entry.cget("state")) == "disabled":
            self._crit_entry.config(state="normal")

        item = self._build_item(use_existing_id=True)
        
        if item is None:
            return
        self._on_submit(item)  
        self.destroy()
        
