from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from airflow.api_fastapi.auth.managers.base_auth_manager import BaseAuthManager
from airflow.api_fastapi.auth.managers.models.resource_details import AccessView, TeamDetails
from airflow.api_fastapi.common.types import MenuItem
from airflow.configuration import conf
from airflow.models import DagModel
from airflow.models.dagbundle import DagBundleModel
from airflow.models.team import Team, dag_bundle_team_association_table
from airflow.providers.fab.auth_manager.fab_auth_manager import FabAuthManager
from airflow.providers.fab.auth_manager.models import User
from airflow.providers.fab.auth_manager.models.anonymous_user import AnonymousUser
from airflow.utils.session import NEW_SESSION, provide_session
from sqlalchemy import select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from airflow.api_fastapi.auth.managers.base_auth_manager import ResourceMethod
    from airflow.api_fastapi.auth.managers.models.resource_details import (
        ConnectionDetails,
        DagAccessEntity,
        DagDetails,
        PoolDetails,
        VariableDetails,
    )


class AzureFabAuthManager(FabAuthManager):
    ADMIN_ROLE = "Admin"
    AIRFLOW_ROLE_PREFIX = "airflow_"
    DEFAULT_ROLE_MAPPING = {
        "airflow_admin": "Admin",
        "airflow_developer": "User",
        "airflow_view": "Viewer",
        "airflow_op": "Op",
    }
    TEAM_SCOPED_MENU_ITEMS = frozenset(
        {
            MenuItem.DAGS,
            # MenuItem.CONNECTIONS,
            # MenuItem.VARIABLES,
            # MenuItem.POOLS,
        }
    )
    TEAM_MEMBER_ACCESS_VIEWS = frozenset({AccessView.IMPORT_ERRORS})

    def _is_multi_team_enabled(self) -> bool:
        return conf.getboolean("core", "multi_team", fallback=False)

    def _get_teams(self) -> set[str]:
        return Team.get_all_team_names()

    def _has_capability_role(self, user: User | AnonymousUser) -> bool:
        if isinstance(user, AnonymousUser):
            return False
        capability_roles = set(self.DEFAULT_ROLE_MAPPING.values())
        return any(role.name in capability_roles for role in user.roles)

    def _is_admin(self, user: User | AnonymousUser) -> bool:
        if isinstance(user, AnonymousUser):
            return False
        return any(role.name == self.ADMIN_ROLE for role in user.roles)

    def _is_team_only_user(self, user: User | AnonymousUser) -> bool:
        return (
            self._is_multi_team_enabled()
            and bool(self._get_user_teams(user))
            and not self._has_capability_role(user)
            and not self._is_admin(user)
        )

    def _get_user_teams(self, user: User | AnonymousUser) -> set[str]:
        if isinstance(user, AnonymousUser):
            return set()

        db_teams = self._get_teams()
        return {
            role.name.removeprefix(self.AIRFLOW_ROLE_PREFIX)
            for role in user.roles
            if role.name.startswith(self.AIRFLOW_ROLE_PREFIX)
            and role.name not in self.DEFAULT_ROLE_MAPPING
            and role.name.removeprefix(self.AIRFLOW_ROLE_PREFIX) in db_teams
        }

    def _has_team_full_access(
        self,
        user: User | AnonymousUser,
        team_name: str | None,
    ) -> bool:
        if not team_name:
            return False
        if self._is_admin(user):
            return True
        return team_name in self._get_user_teams(user)

    def _is_team_scoped_authorized(
        self,
        user: User | AnonymousUser,
        team_name: str | None,
        *,
        method: ResourceMethod,
        has_details: bool,
        super_check: Callable[[], bool],
    ) -> bool:
        if method == "GET" and not has_details:
            return bool(self._get_user_teams(user))

        if team_name is not None:
            return self._has_team_full_access(user, team_name)

        # Global resource (team_name=NULL): team users may read shared resources.
        if self._get_user_teams(user):
            return method == "GET"

        return super_check()

    @provide_session
    def _get_dag_team_name(self, dag_id: str, *, session: Session = NEW_SESSION) -> str | None:
        stmt = (
            select(dag_bundle_team_association_table.c.team_name)
            .select_from(DagModel)
            .join(DagBundleModel, DagModel.bundle_name == DagBundleModel.name)
            .join(
                dag_bundle_team_association_table,
                DagBundleModel.name == dag_bundle_team_association_table.c.dag_bundle_name,
                isouter=True,
            )
            .where(DagModel.dag_id == dag_id)
        )
        return session.scalar(stmt)

    def _resolve_team_name(self, details: DagDetails | None) -> str | None:
        if details and details.team_name:
            return details.team_name
        if details and details.id:
            return self._get_dag_team_name(details.id)
        return None

    def is_authorized_team(
        self,
        *,
        method: ResourceMethod,
        user: User,
        details: TeamDetails | None = None,
    ) -> bool:
        if not details:
            return False
        if self._is_admin(user):
            return True
        return details.name in self._get_user_teams(user)

    def is_authorized_connection(
        self,
        *,
        method: ResourceMethod,
        user: User,
        details: ConnectionDetails | None = None,
    ) -> bool:
        if self._has_capability_role(user) or self._is_admin(user):
            return True

        if not self._is_multi_team_enabled():
            return super().is_authorized_connection(method=method, user=user, details=details)

        team_name = details.team_name if details else None
        return self._is_team_scoped_authorized(
            user,
            team_name,
            method=method,
            has_details=details is not None,
            super_check=lambda: super(AzureFabAuthManager, self).is_authorized_connection(
                method=method, user=user, details=details
            ),
        )

    def is_authorized_variable(
        self,
        *,
        method: ResourceMethod,
        user: User,
        details: VariableDetails | None = None,
    ) -> bool:
        if self._has_capability_role(user) or self._is_admin(user):
            return True

        if not self._is_multi_team_enabled():
            return super().is_authorized_variable(method=method, user=user, details=details)

        team_name = details.team_name if details else None
        return self._is_team_scoped_authorized(
            user,
            team_name,
            method=method,
            has_details=details is not None,
            super_check=lambda: super(AzureFabAuthManager, self).is_authorized_variable(
                method=method, user=user, details=details
            ),
        )
    
    def is_authorized_pool(
        self,
        *,
        method: ResourceMethod,
        user: User,
        details: PoolDetails | None = None,
    ) -> bool:
        if self._has_capability_role(user) or self._is_admin(user):
            return True

        if not self._is_multi_team_enabled():
            return super().is_authorized_pool(method=method, user=user, details=details)

        team_name = details.team_name if details else None
        return self._is_team_scoped_authorized(
            user,
            team_name,
            method=method,
            has_details=details is not None,
            super_check=lambda: super(AzureFabAuthManager, self).is_authorized_pool(
                method=method, user=user, details=details
            ),
        )

    def is_authorized_dag(
        self,
        *,
        method: ResourceMethod,
        user: User,
        access_entity: DagAccessEntity | None = None,
        details: DagDetails | None = None,
    ) -> bool:
        if self._has_capability_role(user) or self._is_admin(user):
            return True

        if not self._is_multi_team_enabled():
            return super().is_authorized_dag(
                method=method,
                user=user,
                access_entity=access_entity,
                details=details,
            )

        team_name = self._resolve_team_name(details)

        if method == "GET" and (not details or not details.id):
            return bool(self._get_user_teams(user)) or super().is_authorized_dag(
                method=method,
                user=user,
                access_entity=access_entity,
                details=details,
            )

        if team_name is not None:
            return self._has_team_full_access(user, team_name)

        if self._get_user_teams(user):
            return method == "GET"

        return super().is_authorized_dag(
            method=method,
            user=user,
            access_entity=access_entity,
            details=details,
        )

    def is_authorized_view(
        self,
        *,
        access_view: AccessView,
        user: User,
    ) -> bool:
        if self._has_capability_role(user) or self._is_admin(user):
            return True
        if self._is_team_only_user(user):
            return access_view in self.TEAM_MEMBER_ACCESS_VIEWS
        return super().is_authorized_view(access_view=access_view, user=user)

    def filter_authorized_menu_items(
        self,
        menu_items: list[MenuItem],
        *,
        user: User,
    ) -> list[MenuItem]:
        if self._is_team_only_user(user):
            return [item for item in menu_items if item in self.TEAM_SCOPED_MENU_ITEMS]
        return super().filter_authorized_menu_items(menu_items, user=user)

    @provide_session
    def get_authorized_dag_ids(
        self,
        *,
        user: User,
        method: ResourceMethod = "GET",
        session: Session = NEW_SESSION,
    ) -> set[str]:
        if self._is_multi_team_enabled():
            return BaseAuthManager.get_authorized_dag_ids(
                self, user=user, method=method, session=session
            )
        return super().get_authorized_dag_ids(user=user, method=method, session=session)

    @provide_session
    def get_authorized_variables(
        self,
        *,
        user: User,
        method: ResourceMethod = "GET",
        session: Session = NEW_SESSION,
    ) -> set[str]:
        if self._is_multi_team_enabled():
            return BaseAuthManager.get_authorized_variables(
                self, user=user, method=method, session=session
            )
        return super().get_authorized_variables(user=user, method=method, session=session)

    @provide_session
    def get_authorized_connections(
        self,
        *,
        user: User,
        method: ResourceMethod = "GET",
        session: Session = NEW_SESSION,
    ) -> set[str]:
        if self._is_multi_team_enabled():
            return BaseAuthManager.get_authorized_connections(
                self, user=user, method=method, session=session
            )
        return super().get_authorized_connections(user=user, method=method, session=session)

    @provide_session
    def get_authorized_pools(
        self,
        *,
        user: User,
        method: ResourceMethod = "GET",
        session: Session = NEW_SESSION,
    ) -> set[str]:
        if self._is_multi_team_enabled():
            return BaseAuthManager.get_authorized_pools(
                self, user=user, method=method, session=session
            )
        return super().get_authorized_pools(user=user, method=method, session=session)

    @provide_session
    def get_authorized_teams(
        self,
        *,
        user: User,
        method: ResourceMethod = "GET",
        session: Session = NEW_SESSION,
    ) -> set[str]:
        return BaseAuthManager.get_authorized_teams(
            self, user=user, method=method, session=session
        )
