from datetime import datetime, timedelta


class Temps:

    def __init__(self, pas_heures: int):
        self.pas_heures = timedelta(hours=pas_heures)

    def ajouter_24_heures(self, jour: datetime):
        return jour + self.pas_heures

    def soustraire_24_heures(self, jour: datetime):
        return jour - self.pas_heures

    def ajouter_23_heures_59_minutes_et_59_secondes(self, jour: datetime):
        return jour + self.pas_heures - timedelta(seconds=1)
