from __future__ import annotations


import copy
import logging
import os
import pandas as pd


from datetime import datetime
from pandas import DataFrame, Index
from typing import TypeAlias


from historique import Historique


class Donnees:

    def __init__(
        self,
        nom_colonne_smps: str,
        nom_colonne_cpc: str,
        nom_colonne_drapeau_sauvegarde: str,
        nom_drapeau_prefixe_particules: str,
        nom_drapeau_pollution: str,
    ):
        self.logger = logging.getLogger()

        self.nom_colonne_smps: str = nom_colonne_smps
        self.nom_colonne_cpc: str = nom_colonne_cpc
        self.nom_colonne_concentration_courante = self.nom_colonne_smps

        self.nom_colonne_drapeau_sauvegarde: str = nom_colonne_drapeau_sauvegarde

        self.nom_drapeau_prefixe_particules: str = nom_drapeau_prefixe_particules

        self.nom_drapeau_pollution: str = nom_drapeau_pollution

        self.initialiser_donnees()

    def initialiser_donnees(self) -> None:
        self.dataframe = pd.DataFrame()
        self.chemin_absolu = ""
        self.nom_fichier = ""
        self.historique = Historique()

    def est_vide(self) -> bool:
        return self.dataframe.empty

    def est_tout_na_concentration(self) -> bool:
        return self.dataframe[self.nom_colonne_concentration_courante].isna().all()

    def obtenir_dataframe(self) -> DataFrame:
        return self.dataframe

    def obtenir_colonne_dates(self) -> Donnees:
        colonne_dates = copy.copy(self)
        colonne_dates.dataframe = colonne_dates.dataframe.index

        return colonne_dates

    def obtenir_colonne_concentration(self) -> Donnees:
        colonne_concentrations = copy.copy(self)
        colonne_concentrations.dataframe = colonne_concentrations.dataframe[self.nom_colonne_concentration_courante]

        return colonne_concentrations

    def supprimer_concentration_smps_non_definie(self) -> Donnees:
        concentration_definie = copy.copy(self)
        concentration_definie.dataframe = concentration_definie.dataframe.dropna(subset=[self.nom_colonne_smps])

        return concentration_definie

    def supprimer_concentration_cpc_non_definie(self) -> Donnees:
        concentration_definie = copy.copy(self)
        concentration_definie.dataframe = concentration_definie.dataframe.dropna(subset=[self.nom_colonne_cpc])

        return concentration_definie

    def supprimer_concentration_courante_non_definie(self) -> Donnees:
        concentration_definie = copy.copy(self)
        concentration_definie.dataframe = concentration_definie.dataframe.dropna(
            subset=[self.nom_colonne_concentration_courante]
        )

        return concentration_definie

    def obtenir_colonnes_concentrations(self) -> Donnees:
        colonnes_concentrations = copy.copy(self)
        colonnes_concentrations.dataframe = colonnes_concentrations.dataframe[
            [self.nom_colonne_smps, self.nom_colonne_cpc]
        ]

        return colonnes_concentrations

    def obtenir_colonnes_concentrations_non_nulles(self) -> Donnees:
        colonnes_concentrations = copy.copy(self)
        colonnes_concentrations = (
            colonnes_concentrations.supprimer_concentration_smps_non_definie()
            .supprimer_concentration_cpc_non_definie()
            .obtenir_colonnes_concentrations()
        )

        return colonnes_concentrations

    def obtenir_colonne_concentration_courante_non_nulle(self) -> Donnees:
        colonnes_concentrations = copy.copy(self)
        colonnes_concentrations = (
            colonnes_concentrations.supprimer_concentration_courante_non_definie().obtenir_colonnes_concentrations()
        )

        return colonnes_concentrations

    def obtenir_drapeaux_sauvegarde(self) -> Donnees:
        drapeaux_sauvegarde = copy.copy(self)
        drapeaux_sauvegarde.dataframe = drapeaux_sauvegarde.dataframe[self.nom_colonne_drapeau_sauvegarde]

        return drapeaux_sauvegarde

    def supprimer_drapeaux_sauvegarde(self) -> Donnees:
        drapeaux_sauvegarde = copy.copy(self)
        drapeaux_sauvegarde.dataframe = drapeaux_sauvegarde.dataframe.drop(self.nom_colonne_drapeau_sauvegarde, axis=1)

        return drapeaux_sauvegarde

    def supprimer_lignes_polluees(self) -> Donnees:
        lignes_non_polluees = copy.copy(self)
        lignes_non_polluees.dataframe = lignes_non_polluees.dataframe.loc[
            lignes_non_polluees.dataframe[self.nom_drapeau_pollution] == 0
        ]

        return lignes_non_polluees

    def supprimer_donnees_manquantes_colonne_concentration(self, nom_colonne_concentration: str):
        donnees_supprimees = copy.deepcopy(self)
        donnees_supprimees.dataframe = donnees_supprimees.dataframe.dropna(subset=[nom_colonne_concentration])

        return donnees_supprimees

    def supprimer_donnees_manquantes_colonnes_concentrations(self):
        donnees_supprimees = self.supprimer_donnees_manquantes_colonne_concentration(self.nom_colonne_smps)
        donnees_supprimees = donnees_supprimees.supprimer_donnees_manquantes_colonne_concentration(self.nom_colonne_cpc)

        return donnees_supprimees

    def echanger_nom_colonne_concentration(self) -> None:
        if self.nom_colonne_concentration_courante == self.nom_colonne_smps:
            self.nom_colonne_concentration_courante = self.nom_colonne_cpc

        elif self.nom_colonne_concentration_courante == self.nom_colonne_cpc:
            self.nom_colonne_concentration_courante = self.nom_colonne_smps

    def obtenir_valeur_maximum(self):
        return self.dataframe.max().max()

    def soustraire_donnees(self, donnees_a_soustraire: Donnees) -> Donnees:
        donnees_soustraites = copy.deepcopy(self)
        # FIXME : Par souci d'optimisation, la copie complète est-elle nécessaire ?

        donnees_soustraites.obtenir_dataframe().loc[donnees_a_soustraire.obtenir_dataframe().index] = pd.NA

        return donnees_soustraites

    def completer_valeurs_manquantes_jour(self, date_debut: datetime, date_fin: datetime) -> Donnees:
        jour_et_valeurs_manquantes = copy.deepcopy(self)
        # FIXME : Par souci d'optimisation, la copie complète est-elle nécessaire ?

        plage = pd.date_range(start=date_debut, end=date_fin, freq="5min")

        jour_et_valeurs_manquantes.dataframe = jour_et_valeurs_manquantes.dataframe.reindex(plage)

        return jour_et_valeurs_manquantes

    def charger_fichier_csv(self, chemin_absolu_chargement) -> None:
        self.chemin_absolu = chemin_absolu_chargement
        self.nom_fichier = os.path.basename(self.chemin_absolu)

        self.dataframe = pd.read_csv(self.chemin_absolu, parse_dates=["datetime"], index_col="datetime")

        self.convertir_donnees_en_float()
        self.ajouter_drapeaux()

        self.dataframe = self.supprimer_lignes_polluees().dataframe

        self.logger.info(f"Fichier {self.nom_fichier} chargé.")

    def fermer_fichier_csv(self) -> None:
        self.logger.info(f"Fichier {self.nom_fichier} fermé.")

        self.initialiser_donnees()

    def sauvegarder_fichier_filtre_csv(self, chemin_absolu_donnees_filtrees) -> None:
        donnees_valides = self.obtenir_donnees_valides().supprimer_drapeaux_sauvegarde()
        donnees_valides.obtenir_dataframe().to_csv(chemin_absolu_donnees_filtrees)

        self.logger.info(f"Fichier filtré {self.nom_fichier} sauvegardé en {chemin_absolu_donnees_filtrees}.")

    def sauvegarder_fichier_drapeaux_csv(self, chemin_absolu_flags) -> None:
        donnees_invalides = self.obtenir_donnees_invalides().obtenir_drapeaux_sauvegarde()
        donnees_invalides.obtenir_dataframe().to_csv(chemin_absolu_flags)

        self.logger.info(f"Fichier flags {self.nom_fichier} sauvegardé en {chemin_absolu_flags}.")

    def obtenir_nombre_dates(self) -> int:
        return self.dataframe.shape[0]

    def obtenir_nombre_colonnes(self) -> int:
        return self.dataframe.shape[1]

    def obtenir_premiere_date(self) -> datetime:
        return self.dataframe.index.min()

    def obtenir_derniere_date(self) -> datetime:
        return self.dataframe.index.max()

    def obtenir_minuit_date(self, date: datetime) -> datetime:
        return date.floor("D")

    def obtenir_minuit_premiere_date(self) -> datetime:
        return self.obtenir_minuit_date(self.obtenir_premiere_date())

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
        donnees_valides.dataframe = donnees_valides.dataframe.query(f"{self.nom_colonne_drapeau_sauvegarde} == 0")

        return donnees_valides

    def obtenir_donnees_invalides(self) -> Donnees:
        donnees_invalides = copy.copy(self)
        donnees_invalides.dataframe = donnees_invalides.dataframe.query(f"{self.nom_colonne_drapeau_sauvegarde} == 1")

        return donnees_invalides

    def obtenir_particules(self) -> Donnees:
        particules = copy.copy(self)
        masque = particules.dataframe.columns.str.startswith(self.nom_drapeau_prefixe_particules)
        particules.dataframe = particules.dataframe.loc[:, masque]

        return particules

    def obtenir_concentration_intervalle(self, concentration_minimum, concentration_maximum) -> Donnees:
        intervalle = copy.copy(self)

        masque = (intervalle.dataframe[self.nom_colonne_concentration_courante] >= concentration_minimum) & (
            intervalle.dataframe[self.nom_colonne_concentration_courante] <= concentration_maximum
        )

        intervalle.dataframe = intervalle.dataframe[masque]

        return intervalle

    # Remarque : copy.copy() renvoie une vue de l'objet Donnees.
    # Le DataFrame du champ donnees est donc partagé par ces deux objets.
    # Si on modifie les valeurs de ce DataFrame dans un des deux objets,
    # alors on modifie les valeurs de l'autre objet également.
    # C'est le comportement souhaité par souci d'optimisation.
    # Si l'on souhaite copier réellement l'objet, remplacer copy.copy() par copy.deepcopy().

    def invalider_drapeau_date(self, date: datetime) -> None:
        self.dataframe.loc[date, self.nom_colonne_drapeau_sauvegarde] = 1

    def invalider_drapeau_dates(self, masque: list[datetime]) -> None:
        self.dataframe.loc[masque, self.nom_colonne_drapeau_sauvegarde] = 1

    def valider_drapeau_date(self, date: datetime) -> None:
        self.dataframe.loc[date, self.nom_colonne_drapeau_sauvegarde] = 0

    def valider_drapeau_dates(self, masque: list[datetime]) -> None:
        self.dataframe.loc[masque, self.nom_colonne_drapeau_sauvegarde] = 0

    def invalider_date(self, date: datetime) -> None:
        self.invalider_drapeau_date(date)
        self.historique.ajouter_action([date])

    def annuler_invalidation_date(self) -> None:
        if not self.historique.est_possible_retour_arriere():
            return

        dates = self.historique.retourner_en_arriere()
        self.valider_drapeau_dates(dates)

    def retablir_invalidation_date(self) -> None:
        if not self.historique.est_possible_retour_avant():
            return

        dates = self.historique.retourner_en_avant()
        self.invalider_drapeau_dates(dates)

    def invalider_dates(self, masque: list[datetime]) -> None:
        self.invalider_drapeau_dates(masque)
        self.historique.ajouter_action(self.dataframe.loc[masque].index)

    def est_tout_invalide(self) -> bool:
        colonnes = [self.nom_colonne_smps, self.nom_colonne_cpc]
        dataframe_non_nan = self.dataframe[colonnes].notna().all(axis=1)
        return (self.dataframe.loc[dataframe_non_nan, self.nom_colonne_drapeau_sauvegarde] == 1).all()

    def multiplier_concentration(self, facteur) -> None:
        self.dataframe[[self.nom_colonne_smps, self.nom_colonne_cpc]] *= facteur

    def convertir_titre_particules_en_float(self) -> None:
        self.dataframe.columns = [float(colonne.split("_")[2]) for colonne in self.dataframe.columns]

    def convertir_donnees_en_float(self) -> None:
        self.dataframe = self.dataframe.apply(pd.to_numeric, errors="coerce")

        # En cas d'erreur, la chaîne de caractères est remplacée
        # par Not A Number, en raison du drapeau "coerce".

    def ajouter_drapeaux(self) -> None:
        self.dataframe[self.nom_colonne_drapeau_sauvegarde] = 0
