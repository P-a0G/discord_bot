import json
from pathlib import Path


def migrate_json_storage(
        path: str,
        *,
        backup: bool = True,
        aggregation: str = "max",  # "max" | "min" | "first"
):
    """
    Migrate JSON storage from:
      RiotAccount.latest_match_seen_date
    to:
      DiscordUser.latest_match_seen_date

    aggregation:
        - "max": use the most recent match date (recommended)
        - "min": use the oldest match date
        - "first": use the first encountered value
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    raw = json.loads(path.read_text())

    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_text(json.dumps(raw, indent=2))
        print(f"Backup written to {backup_path}")

    for uid, user_data in raw.items():
        riot_accounts = user_data.get("riot_accounts", [])

        dates = []
        for acc in riot_accounts:
            if "latest_match_seen_date" in acc:
                dates.append(acc.pop("latest_match_seen_date"))

        # Skip if already migrated
        if "latest_match_seen_date" in user_data:
            continue

        if dates:
            if aggregation == "max":
                user_data["latest_match_seen_date"] = max(dates)
            elif aggregation == "min":
                user_data["latest_match_seen_date"] = min(dates)
            elif aggregation == "first":
                user_data["latest_match_seen_date"] = dates[0]
            else:
                raise ValueError(f"Unknown aggregation mode: {aggregation}")
        else:
            user_data["latest_match_seen_date"] = 0

    path.write_text(json.dumps(raw, indent=2))
    print("Migration completed successfully.")


if __name__ == "__main__":
    migrate_json_storage("files/discord_users.json", backup=True, aggregation="max")
