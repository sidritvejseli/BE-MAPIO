import os
import pandas as pd
from datetime import datetime


class Donnees:

    def __init__(self):

        self.initialiser_donnees()

    def initialiser_donnees(self):

        self.donnees = pd.DataFrame()
        self.chemin_absolu = ""
        self.nom_fichier = ""

    def est_vide(self):
        return self.donnees.empty

    def obtenir_jour_minimum(self):
        return self.donnees.index.min()

    def obtenir_jour_maximum(self):
        return self.donnees.index.max()

    def obtenir_donnees(self, debut: datetime, fin: datetime):
        return self.donnees.loc[debut:fin]

    def obtenir_donnees_valides(self, debut: datetime, fin: datetime):
        return self.obtenir_donnees(debut, fin).query("smps_flag == 0")

    def obtenir_donnees_invalides(self, debut: datetime, fin: datetime):
        return self.obtenir_donnees(debut, fin).query("smps_flag == 1")

    def supprimer_ligne(self, date: datetime):
        self.donnees.loc[date, "smps_flag"] = 1

    def supprimer_donnees(self, debut: datetime, fin: datetime):
        self.donnees.loc[debut:fin, "smps_flag"] = 1

    def multiplier_concentration(self, facteur):
        self.donnees["smps_concTotal"] *= facteur

    def convertir_donnees(self):

        self.donnees = self.donnees.apply(pd.to_numeric, errors="coerce")

        # En cas d'erreur, la chaîne de caractères est remplacée
        # par Not A Time ou Not A Number, en raison du drapeau "coerce".

    def ajouter_drapeaux(self):

        self.donnees["smps_flag"] = 0

    def charger_fichier_csv(self, chemin_absolu_chargement):

        self.chemin_absolu = chemin_absolu_chargement
        self.nom_fichier = os.path.basename(self.chemin_absolu)

        self.donnees = pd.read_csv(self.chemin_absolu, parse_dates=["datetime"], index_col="datetime")

        self.convertir_donnees()

        self.ajouter_drapeaux()

    def fermer_fichier_csv(self):

        self.initialiser_donnees()

    def sauvegarder_fichier_csv(self, chemin_absolu_sauvegarde):

        self.donnees.to_csv(chemin_absolu_sauvegarde)

        # TODO : Ajout de la sauvegarde séparée du fichier "filtre" et des drapeaux.
