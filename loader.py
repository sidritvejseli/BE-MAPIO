from tkinter import filedialog
import os
import pandas as pd


class ChargementDonnees:

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
        # En cas d'erreur, la chaîne de caractère est remplacée par Not A Time ou Not A Number, en raison du drapeau "coerce".
        self.donnees["datetime"] = pd.to_datetime(
            self.donnees["datetime"], errors="coerce"
        )

        for colonne in self.donnees.columns:

            if colonne == "datetime":
                continue

            self.donnees[colonne] = pd.to_numeric(
                self.donnees[colonne], errors="coerce"
            )

        # Création de deux colonnes pour les drapeaux.

        if "smps_flag" not in self.donnees.columns:
            self.donnees["smps_flag"] = 0

        if "pollution_flag" not in self.donnees.columns:
            self.donnees["pollution_flag"] = 0

        print(f"Fichier {self.nom_fichier} chargé.")

    def fermer_fichier_csv(self):

        print(f"Fichier {self.nom_fichier} fermé.")

        self.donnees = None
        self.chemin_absolu = None
        self.nom_fichier = None
