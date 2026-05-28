import re
from typing import Any

APPLICATION_RE = re.compile(
    r"ЗАЯВКА СОЗДАНА:\s*"
    r"Имя:\s*(?P<name>.+?),\s*"
    r"Телефон:\s*(?P<phone>.+?),\s*"
    r"Авто:\s*(?P<vehicle>.+?),\s*"
    r"Услуга:\s*(?P<service>.+?),\s*"
    r"Время:\s*(?P<visit_time>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_application_line(text: str) -> dict[str, Any] | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("ЗАЯВКА СОЗДАНА:"):
            continue
        match = APPLICATION_RE.search(line)
        if not match:
            return {"application_line": line}
        return {
            "application_line": line,
            "client_name": match.group("name").strip(),
            "client_phone": match.group("phone").strip(),
            "vehicle": match.group("vehicle").strip(),
            "service_type": match.group("service").strip(),
            "visit_time": match.group("visit_time").strip(),
        }
    return None
