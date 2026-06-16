import os
import logging

from airflow.providers.fab.auth_manager.security_manager.override import (
    FabAirflowSecurityManagerOverride,
)
from flask_appbuilder.const import AUTH_OAUTH
from airflow.security import permissions
from airflow.models.team import Team
from airflow.utils.session import create_session

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
    
    def _oauth_calculate_user_roles(self, userinfo):
        roles = []
        pending_teams: dict[str, str] = {}

        for az_role in userinfo.get("role_keys", []):
            if not isinstance(az_role, str):
                continue

            if not az_role.startswith(self.AIRFLOW_ROLE_PREFIX):
                continue

            if az_role in self.DEFAULT_ROLE_MAPPING:
                roles.append(
                    self._get_or_create_capability_role(self.DEFAULT_ROLE_MAPPING[az_role])
                )
            else:
                team_name = az_role.removeprefix(self.AIRFLOW_ROLE_PREFIX)
                if not team_name:
                    continue

                pending_teams[team_name] = az_role
                roles.append(self._get_or_create_team_role(az_role))

        if pending_teams:
            existing_teams = Team.get_all_team_names()
            with create_session() as session:
                for team_name, az_role in pending_teams.items():
                    if team_name in existing_teams:
                        continue
                    session.add(Team(name=team_name))
                session.commit()

        return roles
    
SECURITY_MANAGER_CLASS = AzureSecurityManager
