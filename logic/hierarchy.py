from repositories import user_repo


def get_my_team(manager_id):
    """Vráti zoznam ľudí, ktorí majú v stĺpci manager_id tvoje ID"""
    try:
        return user_repo.get_team_by_manager(manager_id)
    except Exception as e:
        print(f"Chyba pri načítaní tímu: {e}")
        return []


def add_new_member(manager_id, full_name, username, password, role="employee"):
    """Vytvorí nového užívateľa a priradí ho pod aktuálneho manažéra"""
    try:
        success, message = user_repo.create_user(username, password, full_name, role, manager_id)
        if not success and "UNIQUE constraint" in message:
            return False, "Užívateľské meno už existuje!"
        return success, message
    except Exception as e:
        return False, str(e)
