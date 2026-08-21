"""Helpers to read and write role-based access on Django groups."""

from django.contrib.auth.models import Group, Permission

from .roles import (
    ALL_ROLES,
    RBAC_ACTIONS,
    RBAC_MODULES,
    ROLE_DESCRIPTIONS,
    ROLE_LABELS,
    ROLE_PERMISSIONS,
    SUPER_ADMIN,
)


def role_label(role_name: str) -> str:
    return ROLE_LABELS.get(role_name, role_name)


def role_description(role_name: str) -> str:
    return ROLE_DESCRIPTIONS.get(role_name, "")


def get_role_group(role_name: str) -> Group:
    if role_name not in ALL_ROLES:
        raise ValueError(f"Unknown role: {role_name}")
    group, _ = Group.objects.get_or_create(name=role_name)
    return group


def permission_key(permission: Permission) -> str:
    return f"{permission.content_type.app_label}.{permission.codename}"


def group_permission_keys(group: Group) -> set[str]:
    return {
        permission_key(perm)
        for perm in group.permissions.select_related("content_type")
    }


def resolve_permissions(keys: list[str] | set[str]) -> list[Permission]:
    wanted = set(keys)
    found = []
    for perm in Permission.objects.select_related("content_type"):
        if permission_key(perm) in wanted:
            found.append(perm)
    return found


def resolve_codenames(codenames: list[str]) -> list[Permission]:
    """Resolve bare Django codenames, preferring unique matches."""
    wanted = set(codenames)
    index: dict[str, list[Permission]] = {}
    for perm in Permission.objects.select_related("content_type"):
        index.setdefault(perm.codename, []).append(perm)

    found = []
    for code in wanted:
        matches = index.get(code) or []
        if len(matches) == 1:
            found.append(matches[0])
        elif matches:
            # Prefer project apps over django.contrib when names collide.
            preferred = [
                perm
                for perm in matches
                if perm.content_type.app_label
                in {
                    "accounts",
                    "academics",
                    "contact",
                    "core",
                    "courses",
                    "documents",
                    "events",
                    "gallery",
                    "news",
                    "pages",
                    "students",
                    "teachers",
                }
            ]
            found.extend(preferred or matches)
    return found


def managed_permission_keys() -> set[str]:
    keys: set[str] = set()
    for module in RBAC_MODULES:
        for perms in module["actions"].values():
            keys.update(perms)
    return keys


def matrix_rows(group: Group | None, *, unlocked: bool = True) -> list[dict]:
    keys = group_permission_keys(group) if group is not None else set()
    if group is not None and group.name == SUPER_ADMIN:
        keys = managed_permission_keys()
        unlocked = False

    rows = []
    for module in RBAC_MODULES:
        cells = []
        for action, label in RBAC_ACTIONS:
            perms = module["actions"].get(action)
            if not perms:
                cells.append(
                    {
                        "action": action,
                        "label": label,
                        "enabled": False,
                        "checked": False,
                        "value": "",
                    }
                )
                continue
            cells.append(
                {
                    "action": action,
                    "label": label,
                    "enabled": unlocked,
                    "checked": perms[0] in keys,
                    "value": f"{module['key']}.{action}",
                }
            )
        rows.append({"key": module["key"], "label": module["label"], "cells": cells})
    return rows


def apply_matrix_selection(group: Group, selected_values: set[str]) -> None:
    """Update only matrix-managed permissions; leave unrelated ones intact."""
    current = set(group.permissions.all())
    managed = {permission_key(perm): perm for perm in resolve_permissions(managed_permission_keys())}
    keep = {perm for perm in current if permission_key(perm) not in managed}

    selected_keys: set[str] = set()
    for module in RBAC_MODULES:
        for action, perms in module["actions"].items():
            if f"{module['key']}.{action}" in selected_values:
                selected_keys.update(perms)

    selected_perms = [managed[key] for key in selected_keys if key in managed]
    group.permissions.set(keep.union(selected_perms))


def apply_default_role_permissions(group: Group) -> None:
    if group.name == SUPER_ADMIN:
        group.permissions.set(Permission.objects.all())
        return
    codenames = ROLE_PERMISSIONS.get(group.name, [])
    group.permissions.set(resolve_codenames(codenames))


def iter_role_summaries():
    for role in ALL_ROLES:
        group = get_role_group(role)
        yield {
            "name": role,
            "label": role_label(role),
            "description": role_description(role),
            "member_count": group.user_set.filter(is_active=True).count(),
            "permission_count": (
                Permission.objects.count()
                if role == SUPER_ADMIN
                else group.permissions.count()
            ),
            "locked": role == SUPER_ADMIN,
        }
