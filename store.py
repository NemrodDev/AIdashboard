"""Saved copies of everything the AI Capex dashboard downloads, in ai-capex\\data.

Each dataset is downloaded once and kept on disk. It is downloaded again only after the next
end-of-day cutoff (5 pm Eastern on a weekday, when the day's closes are in and FRED has posted the
morning's updates), so opening the dashboard normally just reads files. If a download fails, the last
saved copy is used and the page says so.

    fresh(name)        True if the saved copy is newer than the last cutoff
    get(name, fetch)   saved copy if fresh, else fetch() -> save -> return (falls back to the old copy).
                       fetch() can read the old copy (load) and download only what's new: a top-up.
    refresh_all()      used by the evening scheduled task (see daily_refresh.bat)
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
ET = ZoneInfo("America/New_York")
CUTOFF = time(17, 0)          # 5 pm Eastern: after the close and FRED's daily ICE BofA update


def now_et() -> datetime:
    return datetime.now(ET)


def last_cutoff(now: datetime | None = None) -> datetime:
    """The most recent weekday 5 pm Eastern at or before `now`."""
    now = now or now_et()
    d = now.date()
    while True:
        c = datetime.combine(d, CUTOFF, ET)
        if d.weekday() < 5 and c <= now:
            return c
        d -= timedelta(days=1)


def next_cutoff(now: datetime | None = None) -> datetime:
    now = now or now_et()
    d = now.date()
    while True:
        c = datetime.combine(d, CUTOFF, ET)
        if d.weekday() < 5 and c > now:
            return c
        d += timedelta(days=1)


def key(*parts) -> str:
    """Short stable file name for a dataset defined by its parts (e.g. a tuple of series IDs)."""
    return hashlib.sha1(repr(parts).encode()).hexdigest()[:12]


def _paths(name: str) -> tuple[Path, Path]:
    return DATA / f"{name}.pkl", DATA / f"{name}.json"


def meta(name: str) -> dict:
    try:
        return json.loads(_paths(name)[1].read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def fresh(name: str, now: datetime | None = None) -> bool:
    m = meta(name)
    if not m.get("fetched_at") or not _paths(name)[0].exists():
        return False
    try:
        return datetime.fromisoformat(m["fetched_at"]) >= last_cutoff(now)
    except ValueError:
        return False


def load(name: str):
    with open(_paths(name)[0], "rb") as f:
        return pickle.load(f)


class WithMeta:
    """Returned by a fetch function to save extra facts in the dataset's meta (e.g. when the full history
    was last downloaded)."""
    def __init__(self, value, **extra):
        self.value, self.extra = value, extra


def exists(name: str) -> bool:
    return _paths(name)[0].exists()


def save(name: str, value, label: str = "", extra: dict | None = None) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    pkl, js = _paths(name)
    tmp = pkl.with_name(pkl.name + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(value, f)
    os.replace(tmp, pkl)                     # atomic: the page and the evening task can overlap
    m = {**meta(name), **(extra or {}), "fetched_at": now_et().isoformat(timespec="seconds"), "label": label}
    js.write_text(json.dumps(m), encoding="utf-8")


STATUS: dict[str, str] = {}   # name -> "saved" / "downloaded" / "old copy: <error>" for this run


def get(name: str, fetch, label: str = "", force: bool = False):
    """Saved copy if it is newer than the last 5 pm ET cutoff; otherwise download, save and return it.
    If the download fails and an older copy exists, return that instead of failing."""
    if not force and fresh(name):
        STATUS[name] = "saved"
        return load(name)
    try:
        value = fetch()
    except Exception as e:  # noqa: BLE001
        if _paths(name)[0].exists():
            STATUS[name] = f"old copy ({str(e)[:120]})"
            return load(name)
        raise
    extra = {}
    if isinstance(value, WithMeta):
        value, extra = value.value, value.extra
    save(name, value, label, extra)
    STATUS[name] = "downloaded"
    return value


def forget_all() -> None:
    """Make every saved dataset stale, so the next view downloads it again (the Refresh Data button)."""
    for js in DATA.glob("*.json"):
        try:
            m = json.loads(js.read_text(encoding="utf-8"))
            m["fetched_at"] = "2000-01-01T00:00:00-05:00"
            js.write_text(json.dumps(m), encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue


def last_refresh() -> datetime | None:
    """When the newest saved dataset was downloaded."""
    times = []
    for js in DATA.glob("*.json"):
        try:
            t = datetime.fromisoformat(json.loads(js.read_text(encoding="utf-8"))["fetched_at"])
            if t.year > 2000:
                times.append(t)
        except Exception:  # noqa: BLE001
            continue
    return max(times) if times else None
