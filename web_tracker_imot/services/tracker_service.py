import threading
import time
from dataclasses import dataclass
from queue import Queue
from typing import Callable
from web_tracker_imot.models.tracked_imot import TrackedItem

@dataclass
class TrackResult:
    item_id:str
    is_valid:bool
    value:int
    timestamp:float
    error:str|None=None
    changed: bool=False

Extractor=Callable[[TrackedItem], str]

class TrackerService:
    def __init__(self, out_queue: Queue[TrackResult], extractor:Extractor):
        self._out_queue=out_queue
        self._extractor=extractor

        self._stop_event=threading.Event()
        self._force_refresh=threading.Event()

        self._thread:threading.Thread|None=None

        self._items_lock=threading.Lock()
        self._items_by_id: dict[str, TrackedItem]=[]

        self._last_values: dict[str,str]={}
        self._next_run_time: dict[str, float]={}

    def set_items(self, items:list[TrackedItem]) -> None:
        now=time.time()
        with self._items_lock:
            new_by_id={it.id: it for it in items}
            self._items_by_id=new_by_id

            for removed_id in list(self._next_run_time.keys()):
                if removed_id not in new_by_id:
                    self._next_run_time.pop(removed_id, None)
                    self._last_values.pop(removed_id, None)
            
            for it_id, it in new_by_id.items():
                if it_id not in self._next_run_time:
                    self._next_run_time[it_id]=now

            self._force_refresh.set()


    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread=threading.Thread(target=self._run_loop, name="tracker-thread", daemon=True)
        self._thread.start()

    def stop(self)->None:
        self._stop_event.set()
        self._force_refresh.set()
        if self._thread:
            self._thread.join(timeout=2)

    def refresh_now(self) -> None:
        with self._items_lock:
            now=time.time()
            for it_id in self._items_by_id.keys():
                self._next_run_time[it_id]=now
        self._force_refresh.set()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            due_items=self._collect_due_items()

            for item in due_items:
                if self._stop_event.is_set():
                    break
                self._check_one(item)

                with self._items_lock:
                    if item.id in self._items_by_id:
                        self._next_run_time[item.id]=time.time() + float(item.check_interval_sec)

            sleep_for=self._compute_sleep_time(default=0.3, max_sleep=0.8)
            self._force_refresh.wait(timeout=sleep_for)
            self._force_refresh.clear()

    def _collect_due_items(self) -> list[TrackedItem]:
        now=time.time()
        with self._items_lock:
            due: list[TrackedItem]= []
            for it_id, item in self._items_by_id.items():
                next_t=self._next_run_time.get(it_id, now)
                if next_t <= now:
                    due.append(item)
            return due
        
    def _compute_sleep_time(self, *, default: float, max_sleep: float) -> float:
        now=time.time()
        with self._items_lock:
            if not self._next_run_time:
                return default
            
            next_due=min(self._next_run_time.values())
            delta=next_due-now
            if delta<=0:
                return 0.05
            return min(delta, max_sleep)
        
    def _check_one(self, item:TrackedItem) -> None:
        try:
            value=self._extractor(item)
            print("EXTRACTED VALUE:", value)
            old=self._last_values.get(item.id)
            changed=(old is not None) and (old!=value)
            self._last_values[item.id] = value

            self._out_queue.put(
                TrackResult(item_id=item.id, is_valid=True, 
                value=value, timestamp=time.time(), error=None, changed=changed)
            )
        except Exception as exc:
            self._out_queue.put(
                TrackResult(item_id=item.id, is_valid=False, 
                value="", timestamp=time.time(), error=str(exc), changed=False)
            )


