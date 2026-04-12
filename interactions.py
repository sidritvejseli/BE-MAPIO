import logging
import matplotlib.dates as mdates
import numpy as np
import pandas as pd


from datetime import datetime
from matplotlib.backend_bases import Event
from pandas import DataFrame


from donnees import Donnees


class Interactions:

    def __init__(self):
        self.logger = logging.getLogger()

        self.ax_2d = None
        self.infobulle = None
        self.donnees = None
        self.date_fin = None
        self.date_debut = None
        self.zone_affichage_graphe_2d = None
        self.selection_debut = None
        self.selection_fin = None
        self.distances_entre_donnees_et_souris: DataFrame = None
        self.donnees_affichees_valides: Donnees = None

    # fonction de calcul de distances entres les points et la souris et les points valides
    def calculer_distances_entre_donnees_et_souris(self, evenement: Event, donnees: Donnees) -> DataFrame:
        dataframe = donnees.obtenir_dataframe()

        x_points = mdates.date2num(dataframe.index)
        y_points = dataframe["smps_concTotal"]

        x_souris = evenement.xdata
        y_souris = evenement.ydata

        # Poids pour équilibrer les abscisses et les ordonnees.
        x_limite = self.ax_2d.get_xlim()
        y_limite = self.ax_2d.get_ylim()

        # Normalisation par rapport aux limites visibles (pas aux données).
        x_echelle = 1 / (x_limite[1] - x_limite[0])
        y_echelle = 1 / (y_limite[1] - y_limite[0])

        # Calcul de la distance euclidienne.
        distances = np.sqrt(((x_points - x_souris) * x_echelle) ** 2 + ((y_points - y_souris) * y_echelle) ** 2)

        return distances

    def trouver_date_plus_proche_souris(self) -> datetime:
        if self.donnees_affichees_valides.est_vide():
            return

        return self.distances_entre_donnees_et_souris.idxmin()

    def mettre_a_jour_donnees_affichees(self):
        self.donnees_affichees_valides = self.donnees.obtenir_donnees_valides()
        self.donnees_affichees_valides = self.donnees_affichees_valides.obtenir_dates(self.date_debut, self.date_fin)

    def mettre_a_jour_distances_entre_donnees_et_souris(self, evenement: Event):
        self.distances_entre_donnees_et_souris = self.calculer_distances_entre_donnees_et_souris(
            evenement, self.donnees_affichees_valides
        )

    def afficher_infobulle_apres_survol_souris(self, evenement: Event):
        if self.donnees.est_vide() or self.infobulle is None:
            return

        # Si la souris n’est pas sur le graphe, alors on n'affiche pas l'infobulle.
        if evenement.inaxes != self.ax_2d or evenement.xdata is None:
            self.infobulle.set_visible(False)
            self.zone_affichage_graphe_2d.draw_idle()
            return

        # Garde uniquement les points non supprimés
        if not self.date_fin:
            self.date_fin = self.date_debut + pd.Timedelta(days=1)

        self.mettre_a_jour_donnees_affichees()
        self.mettre_a_jour_distances_entre_donnees_et_souris(evenement)

        date_plus_proche = self.trouver_date_plus_proche_souris()

        # Seuil adaptatif (2% de la diagonale du graphe).
        seuil = 0.02

        if self.distances_entre_donnees_et_souris.loc[date_plus_proche] > seuil:
            self.infobulle.set_visible(False)
            self.zone_affichage_graphe_2d.draw_idle()
            return

        dataframe_valides: DataFrame = self.donnees_affichees_valides.obtenir_dataframe()

        concentration = dataframe_valides.loc[date_plus_proche, "smps_concTotal"]

        self.infobulle.set_text(f"{date_plus_proche.strftime('%d/%m %H:%M')}\nConc : {concentration:.1f}")

        # Positionnement de l'infobulle sur le graphe.
        self.infobulle.xy = (mdates.date2num(date_plus_proche), concentration)

        self.infobulle.set_visible(True)
        self.zone_affichage_graphe_2d.draw_idle()

    def repondre_apres_clic_souris(self, evenement: Event):
        if evenement.inaxes != self.ax_2d or evenement.xdata is None:
            return

        if evenement.button == 1:
            self.traiter_clic_gauche(evenement)
            return

        if evenement.button == 3:
            self.traiter_clic_droit(evenement)
            return

    def traiter_clic_gauche(self, evenement: Event):
        date = mdates.num2date(evenement.xdata).replace(tzinfo=None)

        if self.selection_debut is None:
            self.selection_debut = date

            # Suppression des anciennes lignes si elles existent.
            if self.ligne_debut is not None:
                self.ligne_debut.remove()

            self.ligne_debut = self.ax_2d.axvline(date, color="red", linestyle="--")

        else:
            self.selection_fin = date

            # Suppression des anciennes lignes si elles existent.
            if self.ligne_fin is not None:
                self.ligne_fin.remove()

            self.ligne_fin = self.ax_2d.axvline(date, color="red", linestyle="--")

        self.zone_affichage_graphe_2d.draw_idle()

    def traiter_clic_droit(self, evenement: Event):
        if not self.date_fin:
            self.date_fin = self.date_debut + pd.Timedelta(days=1)

        points_valides = self.donnees.obtenir_donnees_valides()
        points_valides = points_valides.obtenir_dates(self.date_debut, self.date_fin)

        if points_valides.est_vide():
            return

        self.mettre_a_jour_donnees_affichees()
        self.mettre_a_jour_distances_entre_donnees_et_souris(evenement)

        date_plus_proche = self.trouver_date_plus_proche_souris()

        seuil = 0.02
        if self.distances_entre_donnees_et_souris.loc[date_plus_proche] > seuil:
            return

        self.donnees.invalider_date(date_plus_proche)

        # correction bug plage
        # supprime ligne début si elle existe
        if self.ligne_debut is not None:
            self.ligne_debut.remove()
            self.ligne_debut = None

        # supprime ligne fin si elle existe
        if self.ligne_fin is not None:
            self.ligne_fin.remove()
            self.ligne_fin = None

        # le reset pour les bug
        self.selection_debut = None
        self.selection_fin = None

        # Recharge le graphe pour voir la suppression
        self.afficher_graphe()

    def appliquer_facteur(self, facteur):
        if self.donnees.est_vide():
            return

        self.donnees.multiplier_concentration(facteur)
        self.afficher_graphe()

    def supprimer_plage(self):
        if self.selection_debut is None or self.selection_fin is None:
            self.logger.info("Suppression de la plage impossible, car aucune plage sélectionnée.")
            return

        self.selection_debut, self.selection_fin = sorted((self.selection_debut, self.selection_fin))

        self.donnees.invalider_dates(self.selection_debut, self.selection_fin)

        # Suppression des lignes.
        if self.ligne_debut is not None:
            self.ligne_debut.remove()
            self.ligne_debut = None

        if self.ligne_fin is not None:
            self.ligne_fin.remove()
            self.ligne_fin = None

        # Pour recommencer une nouvelle ligne on doit réinitaliser.
        self.selection_debut = None
        self.selection_fin = None

        self.afficher_graphe()
