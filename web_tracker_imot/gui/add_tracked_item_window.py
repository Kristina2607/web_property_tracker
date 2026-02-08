import uuid
import tkinter as tk
from tkinter import ttk, messagebox

from web_tracker_imot.models.tracked_imot import TrackedItem, CriterionType

PRESETS: dict[str, list[tuple[str, str]]] = {
    "imot.bg": [
        ("Preset: Price", "preset:price"),
        ("Preset: Location", "preset:location"),
        ("Preset: Area", "preset:area"),
        ("Preset: Price per m²", "preset:psm"),
        ("Custom (manual)", ""),
    ],
    "bazar.bg": [
        ("Preset: Price (or est.)", "preset:price"),
        ("Preset: Location", "preset:location"),
        ("Preset: Area", "preset:area"),
        ("Preset: Price per m²", "preset:psm"),
        ("Custom (manual)", ""),
    ],
}


class AddTrackedItem(tk.Toplevel):
    def __init__(self, master: tk.Tk, on_submit) -> None:
        super().__init__(master)
        self.title("Add tracked item")
        self.resizable(False, False)

        self._on_submit = on_submit

        self.var_site = tk.StringVar(value="imot.bg")
        self.var_url = tk.StringVar()

        self.var_preset = tk.StringVar(value="Custom (manual)")

        self.var_crit_type = tk.StringVar(value=CriterionType.CSS.value)
        self.var_crit_value = tk.StringVar()

        self.var_interval = tk.StringVar(value="60")
        self.var_email = tk.BooleanVar(value=False)

        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Site").grid(row=0, column=0, sticky="w")
        self._site_box = ttk.Combobox(
            frm,
            textvariable=self.var_site,
            values=["imot.bg", "bazar.bg"],
            width=30,
            state="readonly",
        )
        self._site_box.grid(row=0, column=1, sticky="ew")
        self._site_box.bind("<<ComboboxSelected>>", self._on_site_changed)

        ttk.Label(frm, text="URL").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_url, width=55).grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Preset").grid(row=2, column=0, sticky="w")
        self._preset_box = ttk.Combobox(frm, textvariable=self.var_preset, width=30, state="readonly")
        self._preset_box.grid(row=2, column=1, sticky="w")
        self._preset_box.bind("<<ComboboxSelected>>", self._on_preset_selected)

        ttk.Label(frm, text="Criterion type").grid(row=3, column=0, sticky="w")
        ttk.Combobox(
            frm,
            textvariable=self.var_crit_type,
            values=[CriterionType.CSS.value, CriterionType.KEYWORD.value],
            width=30,
            state="readonly",
        ).grid(row=3, column=1, sticky="w")

        ttk.Label(frm, text="Criterion value").grid(row=4, column=0, sticky="w")
        self._crit_entry = ttk.Entry(frm, textvariable=self.var_crit_value, width=55)
        self._crit_entry.grid(row=4, column=1, sticky="ew")

        ttk.Label(frm, text="Interval (sec)").grid(row=5, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_interval, width=10).grid(row=5, column=1, sticky="w")

        ttk.Checkbutton(frm, text="Email notify", variable=self.var_email).grid(row=6, column=1, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=7, column=0, columnspan=2, sticky="e", pady=(10, 0))

        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Add", command=self._submit).grid(row=0, column=1)

        self._refresh_presets()

        self.grab_set()
        self.transient(master)

    def _on_site_changed(self, _event) -> None:
        self._refresh_presets()

    def _refresh_presets(self) -> None:
        site = self.var_site.get().strip()
        opts = PRESETS.get(site, [])
        names = [name for name, _ in opts]
        self._preset_box["values"] = names
        self.var_preset.set("Custom (manual)")
        self._apply_preset_value("")

    def _on_preset_selected(self, _event) -> None:
        site = self.var_site.get().strip()
        mapping = dict(PRESETS.get(site, []))
        value = mapping.get(self.var_preset.get(), "")
        self._apply_preset_value(value)

    def _apply_preset_value(self, value: str) -> None:
        if not value:
            self._crit_entry.config(state="normal")
            return
        self.var_crit_value.set(value)
        self._crit_entry.config(state="disabled")
        self.var_crit_type.set(CriterionType.CSS.value)

    def _build_item(self, *, use_existing_id: bool) -> TrackedItem | None:
        url = self.var_url.get().strip()
        if not url:
            messagebox.showerror("Validation", "URL is required.")
            return None
        if not (url.startswith("http://") or url.startswith("https://")):
            messagebox.showerror("Validation", "URL must start with http:// or https://")
            return None

        crit_value = self.var_crit_value.get().strip()
        if not crit_value:
            messagebox.showerror("Validation", "Criterion value is required (preset or custom).")
            return None

        try:
            interval = int(self.var_interval.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation", "Interval must be a positive integer.")
            return None

        item_id: str | None = None
        if use_existing_id:
            item_id = getattr(self, "_existing_id", None)
        if not item_id:
            item_id = str(uuid.uuid4())

        return TrackedItem(
            id=item_id,
            site=self.var_site.get().strip(),
            url=url,
            criterion_type=CriterionType(self.var_crit_type.get().strip()),
            criterion_value=crit_value,
            check_interval_sec=interval,
            email_notify=bool(self.var_email.get()),
        )

    def _submit(self) -> None:
        if str(self._crit_entry.cget("state")) == "disabled":
            self._crit_entry.config(state="normal")

        item = self._build_item(use_existing_id=False)
        if item is None:
            return
        self._on_submit(item)
        self.destroy()

        