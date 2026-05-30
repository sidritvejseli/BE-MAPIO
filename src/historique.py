from collections import deque
from datetime import datetime
from enum import Enum


class Action(Enum):
    SUPPRIMER = 1
    RESTAURER = 2


class Historique:

    def __init__(self):
        self.pile_retour_arriere: deque[tuple[Action, list[datetime]]] = deque()
        self.pile_retour_avant: deque[tuple[Action, list[datetime]]] = deque()

    def convertir_dates_en_message(self, action: Action, dates: list[datetime]):
        adjectif = ""
        if action is Action.SUPPRIMER:
            adjectif = "supprimée"
        elif action is Action.RESTAURER:
            adjectif = "restaurée"

        if len(dates) == 0:
            return ""

        if len(dates) == 1:
            return f"Date {adjectif} : " + dates[0].strftime("%d/%m/%Y %Hh%M") + ".\n"

        debut, fin = dates[0], dates[-1]
        message_debut = debut.strftime("%d/%m/%Y %Hh%M")
        message_fin = fin.strftime("%d/%m/%Y %Hh%M")
        return f"Dates {adjectif}s : du " + message_debut + " jusqu'au " + message_fin + ".\n"

    def obtenir_journal(self):
        journal = ""
        for action, dates in reversed(self.pile_retour_arriere):
            journal += self.convertir_dates_en_message(action, dates) + "\n"
        return journal

    def ajouter_action(self, action: Action, dates: list[datetime]) -> None:
        self.pile_retour_arriere.append((action, dates))
        self.pile_retour_avant = deque()

    def est_possible_retour_arriere(self) -> bool:
        return len(self.pile_retour_arriere) > 0

    def retourner_en_arriere(self) -> tuple[Action, list[datetime]]:
        if not self.est_possible_retour_arriere():
            raise IndexError("Erreur : Impossible d'annuler car aucune action à annuler.")

        action, dates = self.pile_retour_arriere.pop()

        self.pile_retour_avant.append((action, dates))

        return action, dates

    def est_possible_retour_avant(self) -> bool:
        return len(self.pile_retour_avant) > 0

    def retourner_en_avant(self) -> tuple[Action, list[datetime]]:
        if not self.est_possible_retour_avant():
            raise IndexError("Erreur : Impossible de rétablir car aucune action à rétablir.")

        action, dates = self.pile_retour_avant.pop()

        self.pile_retour_arriere.append((action, dates))

        return action, dates
