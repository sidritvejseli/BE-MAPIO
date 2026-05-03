from datetime import datetime, timedelta


class Temps:

    def __init__(self, pas_heures: int):
        self.pas_heures = timedelta(hours=pas_heures)

    def ajouter_pas_heures(self, jour: datetime):
        return jour + self.pas_heures

    def soustraire_pas_heures(self, jour: datetime):
        return jour - self.pas_heures

    def ajouter_pas_heures_moins_une_seconde(self, jour: datetime):
        return jour + self.pas_heures - timedelta(seconds=1)
