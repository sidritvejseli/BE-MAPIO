from tkinter import filedialog, messagebox
import os
import pandas as pd


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
        return self.donnees["datetime"].dt.date.min()

    def obtenir_jour_maximum(self):
        return self.donnees["datetime"].dt.date.max()

    def obtenir_donnees_jour(self, jour):
        return self.donnees[self.donnees["datetime"].dt.date == jour]

    def obtenir_donnees_valides(self):
        return self.donnees[self.donnees["smps_flag"] == 0]

    def supprimer_ligne(self, ligne):
        self.donnees.loc[ligne, "smps_flag"] = 1

    def supprimer_donnees(self, date_debut, date_fin):
        masque = (self.donnees["datetime"] >= date_debut) & (self.donnees["datetime"] <= date_fin)
        self.supprimer_ligne(masque)

    def multiplier_concentration(self, facteur):
        self.donnees["smps_concTotal"] *= facteur

    def charger_fichier_csv(self, chemin_initial=""):

        self.chemin_absolu = filedialog.askopenfilename(
            initialdir=chemin_initial,
            filetypes=[("CSV files", "*.csv"), ("All", "*.*")],
        )

        if not self.chemin_absolu:
            return

        self.nom_fichier = os.path.basename(self.chemin_absolu)

        self.donnees = pd.read_csv(self.chemin_absolu)

        # Transtypage des chaînes de caractères en leur bon type.
        # En cas d'erreur, la chaîne de caractères est remplacée par Not A Time ou Not A Number,
        # en raison du drapeau "coerce".

        self.donnees["datetime"] = pd.to_datetime(self.donnees["datetime"], errors="coerce")

        for colonne in self.donnees.columns:

            if colonne == "datetime":
                continue

            self.donnees[colonne] = pd.to_numeric(self.donnees[colonne], errors="coerce")

        # Création de deux colonnes pour les drapeaux.

        if "smps_flag" not in self.donnees.columns:
            self.donnees["smps_flag"] = 0

        if "pollution_flag" not in self.donnees.columns:
            self.donnees["pollution_flag"] = 0

        print(f"Fichier {self.nom_fichier} chargé.")

    def fermer_fichier_csv(self):

        print(f"Fichier {self.nom_fichier} fermé.")

        self.initialiser_donnees()

    def sauvegarder_fichier_csv(self):

        if self.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        chemin_absolu_sauvegarde = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )

        if not chemin_absolu_sauvegarde:
            return

        self.donnees.to_csv(chemin_absolu_sauvegarde, index=False)

        nom_fichier_sauvegarde = os.path.basename(chemin_absolu_sauvegarde)

        print(f"Fichier {nom_fichier_sauvegarde} sauvegardé.")

    # TODO : Ajout de la sauvegarde séparée du fichier "filtre" et des drapeaux.
