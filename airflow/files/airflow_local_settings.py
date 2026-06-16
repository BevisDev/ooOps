from __future__ import annotations

import logging
import re
import json
import unicodedata
import pendulum
from urllib import error, request

from airflow.configuration import conf
from airflow.sdk import (
    Variable, DAG
)
from airflow.models import DagModel
from airflow.exceptions import AirflowClusterPolicyViolation
from airflow.providers.smtp.notifications.smtp import SmtpNotifier
from airflow.sdk.bases.operator import BaseOperator

VN_TZ = pendulum.timezone("Asia/Ho_Chi_Minh")
log = logging.getLogger(__name__)

_SKIP_ALERT_TAGS = frozenset({"no_alert", "no_email"})
ALERT_URL = "ALERT_URL"
ALERT_EMAILS = "ALERT_EMAILS"

_MAX_DAG_ID_LEN = 250
_VALID = re.compile(r"^[a-z][a-z0-9_]*__[a-z0-9_]+$")

def _get_alert_emails() -> list[str]:
    emails = Variable.get(ALERT_EMAILS)
    return [e.strip() for e in emails.split(",") if e.strip()]

def _to_vn(dt):
    if not dt:
        return ""
    return pendulum.instance(dt).in_timezone(VN_TZ).to_datetime_string()

def _global_failure_callback(context) -> None:
    url = Variable.get(ALERT_URL, default="")
    if not url:
        log.warning("Variable %s missing, skip callback", ALERT_URL)
        return
    
    ti = context["ti"]
    payload = {
        "team": ti.dag_id.split("__", 1)[0] if "__" in ti.dag_id else "unknown",
        "dag_id": ti.dag_id,
        "task_id": ti.task_id,
        "run_id": context.get("run_id"),
        "status": ti.state.name,
        "try_number": ti.try_number,
        "logical_date": _to_vn(context.get("logical_date")),
        "start_date": _to_vn(getattr(ti, "start_date", None)),
        "log_url": getattr(ti, "log_url", None),
    }

    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = request.Request(
        url, 
        data=body, 
        headers=headers, 
        method="POST"
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            log.info(
                "Automation alert sent: status=%s dag_id=%s task_id=%s",
                resp.status, ti.dag_id, ti.task_id,
            )
    except error.HTTPError:
        log.exception("Automation alert HTTP error dag_id=%s task_id=%s", ti.dag_id, ti.task_id)
    except Exception:
        log.exception("Automation alert failed dag_id=%s task_id=%s", ti.dag_id, ti.task_id)

def _normalize(name: str) -> str:
    s = name.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

# get bundle from config -> dict[bundle_name, "team_name"]
def _bundle_team_map() -> dict[str, str]:
    raw = conf.get("dag_processor", "dag_bundle_config_list", fallback="[]")
    return {
        b["name"]: b["team_name"]
        for b in json.loads(raw)
        if b.get("team_name")
    }

# find team from bundle base on fileloc
def _team_from_bundle(dag: DAG) -> str | None:
    fileloc = dag.fileloc or ""
    for bundle_name, team in _bundle_team_map().items():
        if bundle_name in fileloc:
            return team
    return None

def _get_team(dag: DAG) -> str:
    team = _team_from_bundle(dag)

    # 2) Fallback: DB (lần parse sau / sau sync)
    if not team:
        db_team = DagModel.get_team_name(dag.dag_id)
        log.info("db fallback: dag_id=%s db_team=%s", dag.dag_id, db_team)
        if db_team:
            team = _normalize(db_team)

    if not team:
        raise AirflowClusterPolicyViolation(
            f"Không xác định được team cho DAG '{dag.dag_id}'. "
            f"fileloc={dag.fileloc!r}"
        )
    
    return team

def _build_new_dagid(team: str, raw: str) -> str:
    prefix = f"{team}__"
    name = _normalize(raw)

    if not name or name == prefix:
        raise AirflowClusterPolicyViolation(
            f"dag_id={raw} không hợp lệ"
        )
    
    dag_id = f"{prefix}{name}"

    if len(dag_id) > _MAX_DAG_ID_LEN:
        raise AirflowClusterPolicyViolation(
            f"dag_id quá dài ({len(dag_id)} > {_MAX_DAG_ID_LEN}): {dag_id!r}"
        )
    
    if not _VALID.match(dag_id):
        raise AirflowClusterPolicyViolation(
            f"dag_id không hợp lệ: {dag_id!r}"
        )
    
    return dag_id

def _ensure_team_tag(dag: DAG, team: str) -> None:
    tags = list(dag.tags or [])
    if team not in tags:
        tags.append(team)
    dag.tags = tags
  
def _ensure_team_owner(dag: DAG, team: str) -> None:
    for task in dag.tasks:
        task.owner = team

def dag_policy(dag : DAG):
    # find team
    team = _get_team(dag)
    
    # build new dag => prefix team__dag_id
    new_dagid = _build_new_dagid(team, dag.dag_id)
    dag.dag_id = new_dagid
    dag.dag_display_name = new_dagid

    # ensure has team tag
    _ensure_team_tag(dag, team)

    # ensure has team owner
    _ensure_team_owner(dag, team)

def task_policy(task: BaseOperator) -> None:
    if task.on_failure_callback:
        return
    
    if set(getattr(task.dag, "tags", None) or []) & _SKIP_ALERT_TAGS:
        return

    task.on_failure_callback = [_global_failure_callback]