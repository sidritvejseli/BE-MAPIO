from collections import deque
from datetime import datetime


class Historique:

    def __init__(self):
        self.pile_retour_arriere: deque[list[datetime]] = deque()
        self.pile_retour_avant: deque[list[datetime]] = deque()

    def convertir_dates_en_message(self, dates: list[datetime]):
        if len(dates) == 1:
            return "Date supprimée : " + dates[0].strftime("%d/%m/%Y %Hh%M") + ".\n"

        debut, fin = dates[0], dates[-1]
        message_debut = debut.strftime("%d/%m/%Y %Hh%M")
        message_fin = fin.strftime("%d/%m/%Y %Hh%M")
        return "Dates supprimées : du " + message_debut + " jusqu'au " + message_fin + ".\n"

    def obtenir_journal(self):
        journal = ""
        for dates in reversed(self.pile_retour_arriere):
            journal += self.convertir_dates_en_message(dates) + "\n"
        return journal

    def ajouter_action(self, dates: list[datetime]) -> None:
        self.pile_retour_arriere.append(dates)
        self.pile_retour_avant = deque()

    def est_possible_retour_arriere(self) -> bool:
        return len(self.pile_retour_arriere) > 0

    def retourner_en_arriere(self) -> list[datetime]:
        if not self.est_possible_retour_arriere():
            raise IndexError("Erreur : Impossible d'annuler car aucune action à annuler.")

        action = self.pile_retour_arriere.pop()

        self.pile_retour_avant.append(action)

        return action

    def est_possible_retour_avant(self) -> bool:
        return len(self.pile_retour_avant) > 0

    def retourner_en_avant(self) -> list[datetime]:
        if not self.est_possible_retour_avant():
            raise IndexError("Erreur : Impossible de rétablir car aucune action à rétablir.")

        action = self.pile_retour_avant.pop()

        self.pile_retour_arriere.append(action)

        return action
