import hashlib

from repositories import user_repo


def get_my_team(manager_id):
    """Vráti zoznam ľudí, ktorí majú v stĺpci manager_id tvoje ID (priami podriadení)."""
    try:
        return user_repo.get_team_by_manager(manager_id)
    except Exception as e:
        print(f"Chyba pri načítaní tímu: {e}")
        return []


def get_full_tree(manager_id) -> list[dict]:
    """Vráti celý strom podriadených rekurzívne (BFS).

    Každý člen dostane naviac kľúč 'depth' (0 = priamy podriadeý,
    1 = podriadeý podriadeého, ...) a 'manager_name' pre zobrazenie.
    Zastavuje na max hĺbke 10 ako ochrana voči cyklom v dátach.
    """
    MAX_DEPTH = 10
    all_users = {u["id"]: u for u in user_repo.get_all_users()}
    result: list[dict] = []
    visited: set[int] = {manager_id}

    queue: list[tuple[int, int]] = [(manager_id, 0)]  # (user_id, depth)
    while queue:
        current_id, depth = queue.pop(0)
        if depth >= MAX_DEPTH:
            continue
        directs = user_repo.get_team_by_manager(current_id)
        for member in directs:
            mid = member["id"] if isinstance(member, dict) else member[0]
            if mid in visited:
                continue
            visited.add(mid)
            enriched = dict(member) if isinstance(member, dict) else {
                "id": member[0], "full_name": member[1],
                "role": member[2], "username": member[3],
            }
            enriched["depth"] = depth
            manager_info = all_users.get(current_id, {})
            enriched["manager_name"] = manager_info.get("full_name") or manager_info.get("username", "")
            result.append(enriched)
            queue.append((mid, depth + 1))

    return result


def add_new_member(manager_id, full_name, username, password, role="employee"):
    """Vytvorí nového užívateľa a priradí ho pod aktuálneho manažéra"""
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        success, message = user_repo.create_user(username, hashed_password, full_name, role, manager_id)
        if not success and "UNIQUE constraint" in message:
            return False, "Užívateľské meno už existuje!"
        return success, message
    except Exception as e:
        return False, str(e)
