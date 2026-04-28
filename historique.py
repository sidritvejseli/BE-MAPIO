from collections import deque
from datetime import datetime


class Historique:

    def __init__(self):
        self.pile_retour_arriere = deque()
        self.pile_retour_avant = deque()

    def ajouter_action(self, date: datetime) -> None:
        self.pile_retour_arriere.append(date)
        self.pile_retour_avant = deque()

    def est_possible_retour_arriere(self) -> bool:
        return len(self.pile_retour_arriere) > 0

    def retourner_en_arriere(self) -> datetime:
        if not self.est_possible_retour_arriere():
            raise IndexError("Erreur : Impossible d'annuler car aucune action à annuler.")

        action = self.pile_retour_arriere.pop()

        self.pile_retour_avant.append(action)

        return action

    def est_possible_retour_avant(self) -> bool:
        return len(self.pile_retour_avant) > 0

    def retourner_en_avant(self) -> datetime:
        if not self.est_possible_retour_avant():
            raise IndexError("Erreur : Impossible de rétablir car aucune action à rétablir.")

        action = self.pile_retour_avant.pop()

        self.pile_retour_arriere.append(action)

        return action
