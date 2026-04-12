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

        self.date_une: datetime = None
        self.date_deux: datetime = None

        self.ligne_une: Line2D = None
        self.ligne_deux: Line2D = None

        self.distances_entre_donnees_et_souris: DataFrame = None
        self.donnees_affichees_valides: Donnees = None

        self.nombre_clics = 0

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

    def incrementer_nombre_clics(self):
        self.nombre_clics = (self.nombre_clics + 1) % 3

    def supprimer_ligne_une(self):
        if self.ligne_une is None:
            return

        try:
            self.ligne_une.remove()
        except NotImplementedError:
            pass

        self.ligne_une = None

    def supprimer_ligne_deux(self):
        if self.ligne_deux is None:
            return

        try:
            self.ligne_deux.remove()
        except NotImplementedError:
            pass

        self.ligne_deux = None

    def reinitialiser_plage(self):
        self.supprimer_ligne_une()
        self.supprimer_ligne_deux()
        self.date_une = None
        self.date_deux = None
        self.nombre_clics = 0

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
            self.traiter_clic_gauche(evenement, ax_2d, date_debut, date_fin)
            doit_rafraichir = 1

        if evenement.button == 3:
            doit_rafraichir = self.traiter_clic_droit(evenement, donnees, ax_2d, date_debut, date_fin)

        return doit_rafraichir

    def tracer_ligne_une(self, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        if self.date_une is None or date_debut is None or date_fin is None:
            return

        if self.date_une < date_debut or self.date_une > date_fin:
            return

        self.ligne_une = ax_2d.axvline(self.date_une, color="red", linestyle="--")

    def tracer_ligne_deux(self, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        if self.date_deux is None or date_debut is None or date_fin is None:
            return

        if self.date_deux < date_debut or self.date_deux > date_fin:
            return

        self.ligne_deux = ax_2d.axvline(self.date_deux, color="red", linestyle="--")

    def tracer_lignes(self, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        self.tracer_ligne_une(ax_2d, date_debut, date_fin)
        self.tracer_ligne_deux(ax_2d, date_debut, date_fin)

    def obtenir_date_plus_proche_dans_plage(self, evenement: Event, date_debut: datetime, date_fin: datetime):
        date = mdates.num2date(evenement.xdata).replace(tzinfo=None)

        if date < date_debut:
            return date_debut

        if date > date_fin:
            return date_fin

        return date

    def traiter_clic_gauche(self, evenement: Event, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        date = self.obtenir_date_plus_proche_dans_plage(evenement, date_debut, date_fin)

        print("DEBUG")
        print(date_debut)
        print(date)
        print(date_fin)

        if self.nombre_clics == 0:
            self.date_une = date
            self.tracer_ligne_une(ax_2d, date_debut, date_fin)
            self.incrementer_nombre_clics()

        elif self.nombre_clics == 1:
            self.date_deux = date
            self.tracer_ligne_deux(ax_2d, date_debut, date_fin)
            self.incrementer_nombre_clics()

        elif self.nombre_clics == 2:
            self.reinitialiser_plage()

    def traiter_clic_droit(
        self, evenement: Event, donnees: Donnees, ax_2d: Axes, date_debut: datetime, date_fin: datetime
    ):
        doit_rafraichir = False

        self.mettre_a_jour_donnees_affichees(donnees, date_debut, date_fin)

        if self.donnees_affichees_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.mettre_a_jour_distances_entre_donnees_et_souris(evenement, ax_2d)

        date_plus_proche = self.trouver_date_plus_proche_souris()

        seuil = 0.02
        if self.distances_entre_donnees_et_souris.loc[date_plus_proche] > seuil:
            return doit_rafraichir

        donnees.invalider_date(date_plus_proche)

        self.reinitialiser_plage()

        doit_rafraichir = evenement.button
        return doit_rafraichir

    def supprimer_plage(self, donnees: Donnees):
        doit_rafraichir = False

        if self.nombre_clics != 2:
            self.logger.info("Suppression de la plage impossible, car aucune plage sélectionnée.")
            self.reinitialiser_plage()
            return doit_rafraichir

        self.date_une, self.date_deux = sorted((self.date_une, self.date_deux))

        donnees.invalider_dates(self.date_une, self.date_deux)

        self.reinitialiser_plage()

        doit_rafraichir = True
        return doit_rafraichir

        # TODO : Une ligne où la concentration est NaN, doit-elle pouvoir être invalidée ? Ou faut-il l'ignorer ?

        # FIXME : Si on invalide la toute dernière donnée ou bien toutes les données d'une page, toutes les données sont invalidées.

        # FIXME : Corriger le débordement de la plage sur les autres pages quand on sélectionne une plage sur une extrémité.
