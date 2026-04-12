import logging
from matplotlib.axes import Axes
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
import numpy as np
import pandas as pd


from datetime import datetime
from matplotlib.backend_bases import Event
from pandas import DataFrame


from donnees import Donnees


class Interactions:

    def __init__(self):
        self.logger = logging.getLogger()

        self.selection_debut = None
        self.selection_fin = None

        self.ligne_debut: Line2D = None
        self.ligne_fin: Line2D = None

        self.distances_entre_donnees_et_souris: DataFrame = None
        self.donnees_affichees_valides: Donnees = None

    # fonction de calcul de distances entres les points et la souris et les points valides
    def calculer_distances_entre_donnees_et_souris(self, evenement: Event, donnees: Donnees, ax_2d: Axes) -> DataFrame:
        dataframe = donnees.obtenir_dataframe()

        x_points = mdates.date2num(dataframe.index)
        y_points = dataframe["smps_concTotal"]

        x_souris = evenement.xdata
        y_souris = evenement.ydata

        # Poids pour équilibrer les abscisses et les ordonnees.
        x_limite = ax_2d.get_xlim()
        y_limite = ax_2d.get_ylim()

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

    def mettre_a_jour_donnees_affichees(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        self.donnees_affichees_valides = donnees.obtenir_donnees_valides()
        self.donnees_affichees_valides = self.donnees_affichees_valides.obtenir_dates(date_debut, date_fin)

    def mettre_a_jour_distances_entre_donnees_et_souris(self, evenement: Event, ax_2d: Axes):
        self.distances_entre_donnees_et_souris = self.calculer_distances_entre_donnees_et_souris(
            evenement, self.donnees_affichees_valides, ax_2d
        )

    def afficher_infobulle_apres_survol_souris(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
        infobulle: Annotation,
    ):
        doit_rafraichir = False

        if donnees.est_vide() or infobulle is None:
            return doit_rafraichir

        doit_rafraichir = True

        # Si la souris n’est pas sur le graphe, alors on n'affiche pas l'infobulle.
        if evenement.inaxes != ax_2d or evenement.xdata is None:
            infobulle.set_visible(False)
            return doit_rafraichir

        self.mettre_a_jour_donnees_affichees(donnees, date_debut, date_fin)

        if self.donnees_affichees_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.mettre_a_jour_distances_entre_donnees_et_souris(evenement, ax_2d)

        date_plus_proche = self.trouver_date_plus_proche_souris()

        # Seuil adaptatif (2% de la diagonale du graphe).
        seuil = 0.02

        if self.distances_entre_donnees_et_souris.loc[date_plus_proche] > seuil:
            infobulle.set_visible(False)
            return doit_rafraichir

        dataframe_valides: DataFrame = self.donnees_affichees_valides.obtenir_dataframe()

        concentration = dataframe_valides.loc[date_plus_proche, "smps_concTotal"]

        infobulle.set_text(f"{date_plus_proche.strftime('%d/%m %H:%M')}\nConc : {concentration:.1f}")

        # Positionnement de l'infobulle sur le graphe.
        infobulle.xy = (mdates.date2num(date_plus_proche), concentration)

        infobulle.set_visible(True)

        return doit_rafraichir

    def repondre_apres_clic_souris(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
    ):
        doit_rafraichir = False

        if evenement.inaxes != ax_2d or evenement.xdata is None:
            return doit_rafraichir

        if evenement.button == 1:
            self.traiter_clic_gauche(evenement, ax_2d)
            doit_rafraichir = 1

        if evenement.button == 3:
            doit_rafraichir = self.traiter_clic_droit(evenement, donnees, ax_2d, date_debut, date_fin)

        return doit_rafraichir

    def traiter_clic_gauche(self, evenement: Event, ax_2d: Axes):
        date = mdates.num2date(evenement.xdata).replace(tzinfo=None)

        if self.selection_debut is None:
            self.selection_debut = date

            # Suppression des anciennes lignes si elles existent.
            if self.ligne_debut is not None:
                self.ligne_debut.remove()

            self.ligne_debut = ax_2d.axvline(date, color="red", linestyle="--")

        else:
            self.selection_fin = date

            # Suppression des anciennes lignes si elles existent.
            if self.ligne_fin is not None:
                self.ligne_fin.remove()

            self.ligne_fin = ax_2d.axvline(date, color="red", linestyle="--")

    def traiter_clic_droit(
        self, evenement: Event, donnees: Donnees, ax_2d: Axes, date_debut: datetime, date_fin: datetime
    ):
        doit_rafraichir = False

        if date_fin is None:
            date_fin = date_debut + pd.Timedelta(days=1)

        self.mettre_a_jour_donnees_affichees(donnees, date_debut, date_fin)

        if self.donnees_affichees_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.mettre_a_jour_distances_entre_donnees_et_souris(evenement, ax_2d)

        date_plus_proche = self.trouver_date_plus_proche_souris()

        seuil = 0.02
        if self.distances_entre_donnees_et_souris.loc[date_plus_proche] > seuil:
            return doit_rafraichir

        donnees.invalider_date(date_plus_proche)

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

        doit_rafraichir = evenement.button
        return doit_rafraichir

    def supprimer_plage(self, donnees: Donnees):
        doit_rafraichir = False

        if self.selection_debut is None or self.selection_fin is None:
            self.logger.info("Suppression de la plage impossible, car aucune plage sélectionnée.")
            return doit_rafraichir

        self.selection_debut, self.selection_fin = sorted((self.selection_debut, self.selection_fin))

        donnees.invalider_dates(self.selection_debut, self.selection_fin)

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

        doit_rafraichir = True
        return doit_rafraichir

        # TODO : Une ligne où la concentration est NaN, doit-elle pouvoir être invalidée ? Ou faut-il l'ignorer ?
