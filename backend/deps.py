"""FastAPI dependency injection — aktuálny prihlásený používateľ."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from backend.auth import decode_token
from repositories import project_repo, task_repo, client_repo, user_repo, org_repo
from logic.hierarchy import get_full_tree
from logic import plans

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Overí JWT token a vráti user payload: {id, username, role}."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Neplatný alebo expirovaný token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int | None = payload.get("id")
        if user_id is None:
            raise credentials_exc
        return payload
    except JWTError:
        raise credentials_exc


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vyžaduje sa rola admin")
    return current_user


def require_manager_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vyžaduje sa rola manager alebo admin")
    return current_user


# ── Object-level authorization + izolácia organizácií ────────────────────────
# Tieto helpery vynucujú DVE veci naraz:
#   1. objekt patrí do ROVNAKEJ organizácie ako prihlásený používateľ (multi-tenancy),
#   2. používateľ má na objekt reálne právo (vlastník / priradený / admin).
#
# Cross-org prístup vracia 404 (nie 403), aby neprezradil, že objekt v cudzej
# organizácii vôbec existuje. Poradie je dôležité: org sa kontroluje PRED rolou —
# inak by admin organizácie A videl dáta organizácie B.

def current_org_id(current_user: dict) -> int:
    """Organizácia prihláseného používateľa. Token bez org_id (starý) → 401, nech sa preloguje."""
    org_id = current_user.get("org_id")
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token neobsahuje organizáciu — prihlás sa znova",
        )
    return org_id


def _in_same_org(entity: dict, current_user: dict) -> bool:
    """True ak entita patrí do organizácie prihláseného používateľa."""
    return entity.get("organization_id") == current_org_id(current_user)


def assert_project_access(project_id: int, current_user: dict) -> dict:
    """Vráti projekt ak naň má používateľ prístup, inak 404/403.

    Prístup má: admin TEJ ISTEJ organizácie, vlastník projektu, alebo osoba
    s priradenou úlohou v ňom.
    """
    project = project_repo.get_project_by_id(project_id)
    if not project or not _in_same_org(project, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenájdený")
    if current_user.get("role") == "admin":
        return project
    if project.get("user_id") == current_user["id"]:
        return project
    if project_repo.user_has_access(current_user["id"], project_id):
        return project
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemáš prístup k tomuto projektu")


def assert_task_access(task_id: int, current_user: dict) -> dict:
    """Vráti úlohu ak má používateľ prístup k jej projektu, inak 404/403.

    Úloha nemá vlastné organization_id — príslušnosť dedí cez projekt, ktorý
    kontroluje assert_project_access.
    """
    task = task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Úloha nenájdená")
    assert_project_access(task["project_id"], current_user)
    return task


def assert_client_access(client_id: int, current_user: dict) -> dict:
    """Vráti klienta ak má používateľ prístup, inak 404/403.

    Prístup má: admin/manager TEJ ISTEJ organizácie, alebo advisor daného klienta.
    """
    client = client_repo.get_client_by_id(client_id)
    if not client or client.get("archived") or not _in_same_org(client, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Klient nenájdený")
    if current_user.get("role") in ("admin", "manager"):
        return client
    if client.get("advisor_id") == current_user["id"]:
        return client
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemáš prístup k tomuto klientovi")


# ── Vynútenie limitov cenového plánu ─────────────────────────────────────────
# Vráti 402 (Payment Required) keď organizácia dosiahla limit svojho plánu —
# frontend na to môže naviazať upgrade CTA.

def _org_plan(org_id: int) -> str:
    org = org_repo.get_organization(org_id)
    return (org or {}).get("plan") or "free"


def assert_org_can_add_project(org_id: int) -> None:
    plan = _org_plan(org_id)
    if not plans.can_add_project(plan, project_repo.count_projects_for_org(org_id)):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Dosiahol si limit projektov pre plán {plans.PLAN_LABELS.get(plan, plan)}. "
                   f"Prejdi na vyšší plán a pridaj viac projektov.",
        )


def assert_org_can_add_user(org_id: int) -> None:
    plan = _org_plan(org_id)
    if not plans.can_add_user(plan, user_repo.count_users_for_org(org_id)):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Dosiahol si limit členov tímu pre plán {plans.PLAN_LABELS.get(plan, plan)}. "
                   f"Prejdi na vyšší plán a pozvi viac ľudí.",
        )


def assert_can_add_project(current_user: dict) -> None:
    assert_org_can_add_project(current_org_id(current_user))


def assert_can_add_user(current_user: dict) -> None:
    assert_org_can_add_user(current_org_id(current_user))


def assert_can_view_user(target_user_id: int, current_user: dict) -> None:
    """Povolené: admin vlastnej organizácie, používateľ sám seba, manažér svojich
    (aj nepriamych) podriadených — vždy v rámci tej istej organizácie."""
    target = user_repo.get_user_by_id(target_user_id)
    if not target or not _in_same_org(target, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Používateľ nenájdený")
    if current_user.get("role") == "admin":
        return
    if target_user_id == current_user["id"]:
        return
    if current_user.get("role") == "manager":
        subordinate_ids = {m["id"] for m in get_full_tree(current_user["id"], current_org_id(current_user))}
        if target_user_id in subordinate_ids:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemáš prístup k tomuto používateľovi")
