import datetime
import logging
import os
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select

from airflow.providers.fab.auth_manager.security_manager.override import (
    FabAirflowSecurityManagerOverride,
)
from flask_appbuilder.const import AUTH_OAUTH
from airflow.security import permissions
from airflow.models.team import Team
from airflow.providers.fab.auth_manager.models import (
    User, assoc_user_role
)
from airflow.utils.session import create_session

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

log = logging.getLogger(__name__)

AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
# AUTH_USER_REGISTRATION_ROLE = "Public"
AUTH_ROLES_SYNC_AT_LOGIN = True
AUTH_ROLES_MAPPING = {
    "airflow_admin": ["Admin"],
    "airflow_developer": ["User"],
    "airflow_view": ["Viewer"],
    "airflow_op": ["Op"],
}
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

AZ_TENANT_ID = os.environ["AZ_TENANT_ID"]
AZ_CLIENT_ID = os.environ["AZ_CLIENT_ID"]
AZ_CLIENT_SECRET = os.environ["AZ_CLIENT_SECRET"]

APP_NAME = "VietCredit Data Platform"

OAUTH_PROVIDERS = [
    {
        "name": "azure",
        "icon": "fa-windows",
        "token_key": "access_token",
        "remote_app": {
            "client_id": AZ_CLIENT_ID,
            "client_secret": AZ_CLIENT_SECRET,
            "api_base_url": "https://graph.microsoft.com/v1.0/",
            "client_kwargs": {
                "scope": "openid email profile",
            },
            "server_metadata_url": (
                f"https://login.microsoftonline.com/{AZ_TENANT_ID}/v2.0/.well-known/openid-configuration"
            ),
            "request_token_url": None,
            "access_token_url": (
                f"https://login.microsoftonline.com/{AZ_TENANT_ID}/oauth2/v2.0/token"
            ),
            "authorize_url": (
                f"https://login.microsoftonline.com/{AZ_TENANT_ID}/oauth2/v2.0/authorize"
            ),
        },
    }
]

class AzureSecurityManager(FabAirflowSecurityManagerOverride):
    AIRFLOW_ROLE_PREFIX = "airflow_"
    DEFAULT_ROLE_MAPPING = {
        "airflow_admin": "Admin",
        "airflow_developer": "User",
        "airflow_view": "Viewer",
        "airflow_op": "Op",
    }

    ONBOARDING_TEAM = [
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_DAG),
        # (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_CONNECTION),
        # (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_VARIABLE),
        # (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_POOL),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_IMPORT_ERROR),
    ]

    ONBOARDING_ROLE = [
        # ===========================================
        # =============== Menu Access ===============
        # ===========================================
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_DAG),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_DAG_DEPENDENCIES),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_DAG_RUN),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_DOCS),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_DOCS_MENU),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_TASK_INSTANCE),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_VARIABLE),
        (permissions.ACTION_CAN_ACCESS_MENU, permissions.RESOURCE_HITL_DETAIL),
        
        # ===========================================
        # ================ Can Read =================
        # ===========================================
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_DAG_DEPENDENCIES),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_DAG_CODE),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_DAG_RUN),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_DAG_WARNING),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_TASK_INSTANCE),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_TASK_LOG),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_VARIABLE),
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_HITL_DETAIL),

        # ===========================================
        # ================ Can Edit =================
        # ===========================================
        (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_DAG),
        (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_TASK_INSTANCE),
        (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_DAG_RUN),
        (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_CONNECTION),
        (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_VARIABLE),
        # (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_POOL),
        (permissions.ACTION_CAN_EDIT, permissions.RESOURCE_HITL_DETAIL),
    ]

    def _ensure_role_permissions(self, role, perm_pairs):
        for action_name, resource_name in perm_pairs:
            perm = self.get_permission(action_name, resource_name)
            if perm is None:
                perm = self.create_permission(action_name, resource_name)
            self.add_permission_to_role(role, perm)

    def _get_or_create_capability_role(self, fab_role_name: str):
        role = self.find_role(fab_role_name) or self.add_role(fab_role_name)
        self._ensure_role_permissions(role, self.ONBOARDING_ROLE)
        return role

    def _get_or_create_team_role(self, az_role_name: str):
        role = self.find_role(az_role_name) or self.add_role(az_role_name)
        self._ensure_role_permissions(role, self.ONBOARDING_TEAM)
        return role

    @staticmethod
    def _now_local() -> datetime.datetime:
        return datetime.datetime.now(tz=LOCAL_TZ)

    def get_oauth_user_info(self, provider, response=None):
        if provider != "azure":
            return {}
       
        claims = (response or {}).get("userinfo", {})
        username = claims.get("preferred_username") or claims.get("email")
        roles = claims.get("roles", [])

        log.info(">>>>> [login] username=%s, roles=%s", 
                 username, roles)

        return {
            "username": username,
            "email": claims.get("email"),
            "first_name": claims.get("given_name"),
            "last_name": claims.get("family_name"),
            "role_keys": roles,
        }
    
    def _oauth_calculate_user_roles(self, userinfo) -> list[str]:
        roles = []
        pending_teams: dict[str, str] = {}
        for az_role in userinfo.get("role_keys", []):
            if not isinstance(az_role, str):
                continue

            if not az_role.startswith(self.AIRFLOW_ROLE_PREFIX):
                continue

            if az_role in self.DEFAULT_ROLE_MAPPING:
                role = self.DEFAULT_ROLE_MAPPING[az_role]
                self._get_or_create_capability_role(role)
                roles.append(role)
            else:
                team_name = az_role.removeprefix(self.AIRFLOW_ROLE_PREFIX)
                if not team_name:
                    continue

                pending_teams[team_name] = az_role
                self._get_or_create_team_role(az_role)
                roles.append(az_role)

        if pending_teams:
            existing_teams = Team.get_all_team_names()
            with create_session() as session:
                for team_name in pending_teams:
                    if team_name in existing_teams:
                        continue
                    session.add(Team(name=team_name))
                session.commit()

        return roles
    
    def _get_user_role_names(self, user_id: int) -> set[str]:
        return set(
            self.session.scalars(
                select(self.role_model.name)
                .join(assoc_user_role, assoc_user_role.c.role_id == self.role_model.id)
                .where(assoc_user_role.c.user_id == user_id)
            ).all()
        )

    def _sync_user_roles(self, user: User, roles: list[str]) -> None:
        new_roles = set(roles)
        current_roles = self._get_user_role_names(user.id)

        # not change => skip
        if new_roles == current_roles:
            return
  
        role_ids = list(
            self.session.scalars(
                select(self.role_model.id).where(self.role_model.name.in_(new_roles))
            ).all()
        ) if new_roles else []
        
        self.session.execute(
            delete(assoc_user_role).where(assoc_user_role.c.user_id == user.id)
        )
        
        if role_ids:
            self.session.execute(
                assoc_user_role.insert(),
                [{"user_id": user.id, "role_id": role_id} for role_id in role_ids],
            )

        self.session.expire(user, ["roles"])
        self._reset_user_permissions_cache(user)
    
    def auth_user_oauth(self, userinfo):
        username = userinfo.get("username") or userinfo.get("email")
        if not username:
            log.error("OAUTH userinfo does not have username or email %s", userinfo)
            return None

        if (username is None) or username == "":
            return None
        
        # Search the DB for this user
        user = self.find_user(username=username)
        if user and not user.is_active:
            return None

        # If user is not registered, and not self-registration, go away
        if not user and not self.auth_user_registration:
            return None

        # Sync the user's roles
        if user and self.auth_roles_sync_at_login:
            roles = self._oauth_calculate_user_roles(userinfo)
            self._sync_user_roles(user, roles)
            user.changed_on = self._now_local()

        if not user and self.auth_user_registration:
            user = self.add_user(
                username=username,
                first_name=userinfo.get("first_name", ""),
                last_name=userinfo.get("last_name", ""),
                email=userinfo.get("email", "") or f"{username}@vietcredit.com.vn",
                role=self._oauth_calculate_user_roles(userinfo),
            )
            log.debug(">>>> New user registered: %s", user)
            if not user:
                log.error("Error creating a new OAuth user %s", username)
                return None
            
        # LOGIN SUCCESS (only if user is now registered)
        if user:
            self._rotate_session_id()
            self.update_user_auth_stat(user)
            return user
        else:
            return None
        
    def update_user(self, user: User) -> bool:
        try:
            bound_user = self.session.get(self.user_model, user.id)
            if not bound_user:
                return False
            
            for attr in (
                "login_count", 
                "last_login", 
                "fail_login_count",
                "first_name", 
                "last_name", 
                "email", 
                "active", 
                "changed_on",
            ):
                setattr(bound_user, attr, getattr(user, attr))
            self.session.commit()
            # self._reset_user_permissions_cache(bound_user)
            return True
        except Exception as e:
            log.error("Error updating user to database. %s", e)
            self.session.rollback()
            return False
    
SECURITY_MANAGER_CLASS = AzureSecurityManager
