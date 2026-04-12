from __future__ import annotations


import copy
import logging
import os
import pandas as pd


from datetime import datetime
from pandas import DataFrame, Index


class Donnees:

    def __init__(self):
        self.logger = logging.getLogger()
        self.initialiser_donnees()

    def initialiser_donnees(self) -> None:
        self.dataframe = pd.DataFrame()
        self.chemin_absolu = ""
        self.nom_fichier = ""

    def est_vide(self) -> bool:
        return self.dataframe.empty

    def obtenir_dataframe(self) -> DataFrame:
        return self.dataframe

    def charger_fichier_csv(self, chemin_absolu_chargement) -> None:
        self.chemin_absolu = chemin_absolu_chargement
        self.nom_fichier = os.path.basename(self.chemin_absolu)

        self.dataframe = pd.read_csv(self.chemin_absolu, parse_dates=["datetime"], index_col="datetime")

        self.convertir_donnees_en_float()
        self.ajouter_drapeaux()

        # copie de sauvegarde pour pouvoir faire un reset plus tard
        self.donnees_original = self.dataframe.copy()

        self.logger.info(f"Fichier {self.nom_fichier} chargé.")

    def fermer_fichier_csv(self) -> None:
        self.logger.info(f"Fichier {self.nom_fichier} fermé.")

        self.initialiser_donnees()

        # TODO : Ajouter messages de debugging dans le terminal.

    def sauvegarder_fichier_csv(
        self, chemin_absolu_sauvegarde, dossier_resultats="resultats/", dossier_flags="resultats/flags/"
    ) -> None:

        if self.dataframe is None:
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
            filetypes=[("CSV files", "*.csv")],
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
            filetypes=[("CSV files", "*.csv")],
        )
        if not chemin_flags:
            return
        df_flags = self.donnees[self.donnees["smps_flag"] != 0]
        df_flags.to_csv(chemin_flags, index=False)
        print(f"Fichier flags sauvegardé : {os.path.basename(chemin_flags)}")
        self.logger.info(f"Fichier {self.nom_fichier} sauvegardé en {chemin_absolu_sauvegarde}.")

    def obtenir_nombre_dates(self) -> int:
        return self.dataframe.shape[0]

    def obtenir_nombre_colonnes(self) -> int:
        return self.dataframe.shape[1]

    def obtenir_premiere_date(self) -> datetime:
        return self.dataframe.index.min()

    def obtenir_derniere_date(self) -> datetime:
        return self.dataframe.index.max()

    def obtenir_noms_colonnes(self) -> Index:
        return self.dataframe.columns

    def obtenir_date(self, date: datetime) -> Donnees:
        donnees_date = copy.copy(self)
        donnees_date.dataframe = donnees_date.dataframe.loc[date]

        return donnees_date

    def obtenir_dates(self, debut: datetime, fin: datetime) -> Donnees:
        donnees_dates = copy.copy(self)
        donnees_dates.dataframe = donnees_dates.dataframe.loc[debut:fin]

        return donnees_dates

    def obtenir_dates_echantillon(self, indices_echantillon: Index) -> Donnees:
        donnees_dates_echantillon = copy.copy(self)
        donnees_dates_echantillon.dataframe = donnees_dates_echantillon.dataframe.index[indices_echantillon]

        return donnees_dates_echantillon

    def obtenir_donnees_valides(self) -> Donnees:
        donnees_valides = copy.copy(self)
        donnees_valides.dataframe = donnees_valides.dataframe.query("smps_flag == 0")

        return donnees_valides

    def obtenir_donnees_invalides(self) -> Donnees:
        donnees_invalides = copy.copy(self)
        donnees_invalides.dataframe = donnees_invalides.dataframe.query("smps_flag == 1")

        return donnees_invalides

    def obtenir_particules(self) -> Donnees:
        particules = copy.copy(self)
        masque = particules.dataframe.columns.str.startswith("smps_d_")
        particules.dataframe = particules.dataframe.loc[:, masque]

        return particules

    # Remarque : copy.copy() renvoie une vue de l'objet Donnees.
    # Le DataFrame du champ donnees est donc partagé par ces deux objets.
    # Si on modifie les valeurs de ce DataFrame dans un des deux objets,
    # alors on modifie les valeurs de l'autre objet également.
    # C'est le comportement souhaité par souci d'optimisation.
    # Si l'on souhaite copier réellement l'objet, remplacer copy.copy() par copy.deepcopy().

    def invalider_date(self, date: datetime) -> None:
        self.dataframe.loc[date, "smps_flag"] = 1

    def invalider_dates(self, debut: datetime, fin: datetime) -> None:
        self.dataframe.loc[debut:fin, "smps_flag"] = 1

    def multiplier_concentration(self, facteur) -> None:
        self.dataframe["smps_concTotal"] *= facteur

    def convertir_titre_particules_en_float(self) -> None:
        self.dataframe.columns = [float(colonne.split("_")[2]) for colonne in self.dataframe.columns]

    def convertir_donnees_en_float(self) -> None:
        self.dataframe = self.dataframe.apply(pd.to_numeric, errors="coerce")

        # En cas d'erreur, la chaîne de caractères est remplacée
        # par Not A Number, en raison du drapeau "coerce".

    def ajouter_drapeaux(self) -> None:
        self.dataframe["smps_flag"] = 0
