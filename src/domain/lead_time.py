from datetime import datetime, timezone

TARGET_STATUSES = [
    "IN PROGRESS",
    "REWORK",
    "ON HOLD"
]

END_STATUSES = [
    "DONE",
    "REJECTED"
]


def _parse_jira_datetime(value):
    """
    Parse Jira datetime safely.
    Accepts formats like:
    - 2026-06-02T09:30:00.000+0000
    - 2026-06-02T09:30:00+0000
    - 2026-06-02T09:30:00.000Z
    """
    if not value:
        return None

    value = value.strip()

    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(value)

        # Handle Jira format +0000 -> +00:00
        if len(value) >= 5 and (value[-5] in ["+", "-"]) and value[-3] != ":":
            value = value[:-2] + ":" + value[-2:]

        return datetime.fromisoformat(value)

    except Exception:
        return None


def compute_time_in_status_details(issue):
    """
    Returns:
    {
        "time_spent": {
            "IN PROGRESS": float,
            "REWORK": float,
            "ON HOLD": float
        },
        "data_quality_issue": bool,
        "data_quality_notes": [str]
    }

    Logic:
    - Reconstruct durations between status transitions from changelog
    - Add ongoing duration for current status
    - If the entry date into current status cannot be found in changelog,
      fallback to statuscategorychangedate / updated / created
    """

    time_spent = {status: 0.0 for status in TARGET_STATUSES}
    data_quality_issue = False
    notes = []

    fields = issue.get("fields", {})
    changelog = issue.get("changelog", {})
    histories = changelog.get("histories", [])

    # -------------------------
    # 1) Extract status events
    # -------------------------
    events = []

    for history in histories:
        created_raw = history.get("created")
        created_dt = _parse_jira_datetime(created_raw)

        if not created_dt:
            continue

        for item in history.get("items", []):
            if item.get("field") == "status":
                to_status = item.get("toString")
                if to_status:
                    events.append({
                        "status": to_status.upper().strip(),
                        "date": created_dt
                    })

    events.sort(key=lambda x: x["date"])

    # -------------------------------------
    # 2) Compute durations between events
    # -------------------------------------
    for i in range(len(events) - 1):
        current = events[i]
        next_event = events[i + 1]

        current_status = current["status"]

        if current_status in TARGET_STATUSES:
            duration_days = (next_event["date"] - current["date"]).total_seconds() / 86400
            if duration_days > 0:
                time_spent[current_status] += duration_days

    # -------------------------------------
    # 3) Handle current active status
    # -------------------------------------
    current_status_name = (
        fields.get("status", {})
        .get("name", "")
        .upper()
        .strip()
    )

    now = datetime.now(timezone.utc)

    if current_status_name in TARGET_STATUSES:
        # Try to find the last transition INTO current status
        last_entry_date = None

        for event in reversed(events):
            if event["status"] == current_status_name:
                last_entry_date = event["date"]
                break

        # Fallbacks if changelog is incomplete
        if not last_entry_date:
            data_quality_issue = True
            notes.append(
                f"Missing transition into current status '{current_status_name}' in changelog."
            )

            fallback_candidates = [
                fields.get("statuscategorychangedate"),
                fields.get("updated"),
                fields.get("created"),
            ]

            for candidate in fallback_candidates:
                dt = _parse_jira_datetime(candidate)
                if dt:
                    last_entry_date = dt
                    notes.append(
                        f"Fallback date used for '{current_status_name}': {candidate}"
                    )
                    break

        if last_entry_date:
            duration_days = (now - last_entry_date).total_seconds() / 86400
            if duration_days > 0:
                time_spent[current_status_name] += duration_days
        else:
            data_quality_issue = True
            notes.append(
                f"Unable to estimate ongoing duration for current status '{current_status_name}'."
            )

    # -------------------------------------
    # 4) Detect obvious data quality issues
    # -------------------------------------
    if not events:
        data_quality_issue = True
        notes.append("No status transition found in changelog.")

    # Round
    rounded = {k: round(v, 2) for k, v in time_spent.items()}

    return {
        "time_spent": rounded,
        "data_quality_issue": data_quality_issue,
        "data_quality_notes": notes
    }


def compute_time_in_status(issue):
    """
    Backward-compatible helper:
    returns only the dictionary of durations.
    """
    result = compute_time_in_status_details(issue)
    return result["time_spent"]