import re
from typing import Tuple, Set

_SELECT_ONLY = re.compile(r"^\s*select\b", re.IGNORECASE | re.DOTALL)

def is_select_only(sql: str) -> bool:
    if not sql:
        return False
    if not _SELECT_ONLY.search(sql):
        return False
    lowered = sql.lower()
    banned = [" insert ", " update ", " delete ", " merge ", " create ", " alter ", " drop ", " truncate ", " replace "]
    return not any(b in lowered or lowered.startswith(b.strip()) for b in banned)

def tables_within_allowlist(sql: str, allowlist: Set[str]) -> Tuple[bool, Set[str]]:
    if not sql:
        return False, set()
    parts = re.findall(r"`?([a-z0-9\-_]+)\.([a-z0-9\-_]+)\.([a-z0-9\-_]+)`?", sql, re.IGNORECASE)
    refs = {".".join(p) for p in parts}
    if not refs:
        return True, set()
    allowed_lower = {a.lower() for a in allowlist}
    illegal = {r for r in refs if r.lower() not in allowed_lower}
    return len(illegal) == 0, illegal
