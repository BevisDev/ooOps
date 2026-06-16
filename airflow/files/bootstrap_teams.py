from __future__ import annotations

import json
import sys

from airflow.configuration import conf
from airflow.models.team import Team
from airflow.utils.session import create_session

def main() -> int:
    raw = conf.get("dag_processor", "dag_bundle_config_list", fallback="[]")
    wanted = {
        b["team_name"]
        for b in json.loads(raw)
        if b.get("team_name")
    }
    if not wanted:
        print("No team_name in dag_bundle_config_list", file=sys.stderr)
        return 0

    with create_session() as session:
        existing = {t.name for t in session.query(Team).all()}
        for name in wanted:
            if not name in existing:
                session.add(Team(name=name))
        session.commit()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())