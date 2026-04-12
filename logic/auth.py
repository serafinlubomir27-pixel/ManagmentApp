from repositories import user_repo


def login_user(username, password):
    """
    Overí meno a heslo v databáze.
    Ak sú správne, vráti informácie o užívateľovi ako dict.
    Ak nie, vráti None.
    """
    try:
        return user_repo.get_by_username_and_password(username, password)
    except Exception as e:
        print(f"Chyba pri prihlasovaní: {e}")
        return None
