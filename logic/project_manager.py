from repositories import project_repo


def get_user_projects(user_id):
    """
    Vráti projekty:
    1. Ktoré som vytvoril JA (ako manažér)
    2. ALEBO v ktorých mám pridelenú aspoň jednu úlohu (ako zamestnanec)
    """
    try:
        return project_repo.get_user_projects(user_id)
    except Exception as e:
        print(f"Chyba pri načítaní projektov: {e}")
        return []


def create_test_project(user_id):
    """Pomocná funkcia na vytvorenie testovacieho projektu (aby si tam niečo videl)"""
    try:
        project_repo.create_project(
            user_id,
            "Nový Projekt 2025",
            "Toto je automaticky vytvorený testovací projekt.",
            status="active",
        )
        return True
    except Exception as e:
        print(e)
        return False
