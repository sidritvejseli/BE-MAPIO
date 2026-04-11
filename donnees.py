from tkinter import filedialog, messagebox
import os
import pandas as pd


class Donnees:

    def __init__(self):

        self.donnees = None
        self.chemin_absolu = None
        self.nom_fichier = None

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
        # En cas d'erreur, la chaîne de caractères est remplacée par Not A Time ou Not A Number, en raison du drapeau "coerce".

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

        # copie de sauvegarde pour pouvoir faire un reset plus tard
        self.donnees_original = self.donnees.copy()

        print(f"Fichier {self.nom_fichier} chargé.")

    def fermer_fichier_csv(self):

        print(f"Fichier {self.nom_fichier} fermé.")

        self.donnees = None
        self.chemin_absolu = None
        self.nom_fichier = None

    # TODO : Ajout de la sauvegarde séparée du fichier "filtre" et des drapeaux.

    def sauvegarder_fichier_csv(self, dossier_resultats="resultats/", dossier_flags="resultats/flags/"):

        if self.donnees is None:
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        # on cree les dossiers s'ils n'existent pas
        os.makedirs(dossier_resultats, exist_ok=True)
        os.makedirs(dossier_flags, exist_ok=True)
 
        # sauvegarde du fichier filtre (lignes valides uniquement)
        chemin_filtre = filedialog.asksaveasfilename(
            title="Sauvegarder les données filtrées",
            initialdir=dossier_resultats,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not chemin_filtre:
            return
        df_filtre = self.donnees[self.donnees["smps_flag"] == 0]
        df_filtre.to_csv(chemin_filtre, index=False)
        print(f"Fichier filtré sauvegardé : {os.path.basename(chemin_filtre)}")
 
        # sauvegarde du fichier des flags (lignes invalidees)
        chemin_flags = filedialog.asksaveasfilename(
            title="Sauvegarder le fichier des flags",
            initialdir=dossier_flags,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not chemin_flags:
            return
        df_flags = self.donnees[self.donnees["smps_flag"] != 0]
        df_flags.to_csv(chemin_flags, index=False)
        print(f"Fichier flags sauvegardé : {os.path.basename(chemin_flags)}")



    
