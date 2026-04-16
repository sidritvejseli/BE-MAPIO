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

        #les deux borne de la plage selectionne
        self.date_debut: datetime = None
        self.date_fin: datetime = None

        #trait rouge verticaux du graphe
        self.ligne_debut: Line2D = None
        self.ligne_fin: Line2D = None

        # distances calculees entre chaque point et la souris
        self.distances_point_souris: DataFrame = None

        #points visibles a l'ecran
        self.points_valides: Donnees = None
        #nb clc pour enlever les trait
        self.nombre_clics = 0







    # calcule la distance normalisee entre chaque point et la souris
    def calculer_distances(self, evenement: Event, donnees: Donnees, ax_2d: Axes) -> DataFrame:
        dataframe = donnees.obtenir_dataframe()

        x_points = mdates.date2num(dataframe.index)
        y_points = dataframe["smps_concTotal"]

        x_souris = evenement.xdata
        y_souris = evenement.ydata

        # coordonnees de la souris
        x_limite = ax_2d.get_xlim()
        y_limite = ax_2d.get_ylim()

        # Normalisation par rapport aux limites visibles (pas aux données).
        x_echelle = 1 / (x_limite[1] - x_limite[0])
        y_echelle = 1 / (y_limite[1] - y_limite[0])

        # Calcul de la distance euclidienne.
        distances = np.sqrt(
            ((x_points - x_souris) * x_echelle) ** 2 + 
            ((y_points - y_souris) * y_echelle) ** 2)

        return distances
    
    #--------- Calcule des distances


    # retourne la date du point le plus proche de la souris
    def trouver_date_plus_proche(self) -> datetime:
        if self.points_valides.est_vide():
            return

        return self.distances_point_souris.idxmin()



    def maj_donnees_affichees(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        self.points_valides = donnees.obtenir_donnees_valides()
        self.points_valides = self.points_valides.obtenir_dates(date_debut, date_fin)


    # recalcule les distances entre les points valides et la souris
    def maj_distances(self, evenement: Event, ax_2d: Axes):
        self.distances_point_souris = self.calculer_distances(
            evenement, self.points_valides, ax_2d
        )


#--------Gestion plage

    # incremente le compteur de clics en bouclant : 0 - 1 - 2 - 0
    def incrementer_nombre_clics(self):
        self.nombre_clics = (self.nombre_clics + 1) % 3

    def supprimer_ligne_debut(self):
        if self.ligne_debut is None:
            return

        try:
            self.ligne_debut.remove()
        except NotImplementedError:
            pass

        self.ligne_debut = None

    def supprimer_ligne_fin(self):
        if self.ligne_fin is None:
            return

        try:
            self.ligne_fin.remove()
        except NotImplementedError:
            pass

        self.ligne_fin = None

    
    
    # supprime les deux traits et remet tout a zero
    def reinitialiser_plage(self):
        self.supprimer_ligne_debut()
        self.supprimer_ligne_fin()
        self.date_debut = None
        self.date_fin = None
        self.nombre_clics = 0


#-----infobulle

    def info_point(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
        infobulle: Annotation,
    ):
        doit_rafraichir = False

        # si pas de donnees ou pas de tooltip on ne fait rien du tout
        if donnees.est_vide() or infobulle is None:
            return doit_rafraichir

        doit_rafraichir = True

        # Si la souris n’est pas sur le graphe, alors on n'affiche pas l'infobulle.
        if evenement.inaxes != ax_2d or evenement.xdata is None:
            infobulle.set_visible(False)
            return doit_rafraichir

        self.maj_donnees_affichees(donnees, date_debut, date_fin)


        # si toutes les concentrations sont NaN il n'y a rien a afficher
        if self.points_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.maj_distances(evenement, ax_2d)
        date_plus_proche = self.trouver_date_plus_proche()

        # Seuil adaptatif (2% de la diagonale du graphe).
        seuil = 0.02
        if self.distances_point_souris.loc[date_plus_proche] > seuil:
            infobulle.set_visible(False)
            return doit_rafraichir


        #recupere la concentration du point le plus proche
        dataframe_valides: DataFrame = self.points_valides.obtenir_dataframe()
        concentration = dataframe_valides.loc[date_plus_proche, "smps_concTotal"]

        # met a jour le texte et la position du tooltip sur le graphe
        infobulle.set_text(
            f"{date_plus_proche.strftime('%d/%m %H:%M')}\nConc : {concentration:.1f}")

        # Positionnement de l'infobulle sur le graphe.
        infobulle.xy = (mdates.date2num(date_plus_proche), concentration)
        infobulle.set_visible(True)

        return doit_rafraichir



#------Gestion des clic

    def repondre_apres_clic_souris(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
    ):
        doit_rafraichir = False

        # clic hors du graphe : on ignore
        if evenement.inaxes != ax_2d or evenement.xdata is None:
            return doit_rafraichir
        

        # bouton 1 = clic gauche → selection de plage
        if evenement.button == 1:
            self.traiter_clic_gauche(evenement, ax_2d, date_debut, date_fin)
            doit_rafraichir = 1


         # bouton 3 = clic droit → suppression d'un point
        if evenement.button == 3:
            doit_rafraichir = self.traiter_clic_droit(evenement, donnees, ax_2d, date_debut, date_fin)

        return doit_rafraichir
    




    def tracer_ligne_debut(self, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        if self.date_debut is None or date_debut is None or date_fin is None:
            return

        if self.date_debut < date_debut or self.date_debut > date_fin:
            return

        self.ligne_debut = ax_2d.axvline(self.date_debut, color="red", linestyle="--")





    def tracer_ligne_fin(self, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        if self.date_fin is None or date_debut is None or date_fin is None:
            return

        if self.date_fin < date_debut or self.date_fin > date_fin:
            return

        self.ligne_fin = ax_2d.axvline(self.date_fin, color="red", linestyle="--")




    def tracer_lignes(self, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        self.tracer_ligne_debut(ax_2d, date_debut, date_fin)
        self.tracer_ligne_fin(ax_2d, date_debut, date_fin)

    def traiter_clic_gauche(self, evenement: Event, ax_2d: Axes, date_debut: datetime, date_fin: datetime):
        date = mdates.num2date(evenement.xdata).replace(tzinfo=None)

        if self.nombre_clics == 0:
            self.date_debut = date
            self.tracer_ligne_debut(ax_2d, date_debut, date_fin)
            self.incrementer_nombre_clics()

        elif self.nombre_clics == 1:
            self.date_fin = date
            self.tracer_ligne_fin(ax_2d, date_debut, date_fin)
            self.incrementer_nombre_clics()

        elif self.nombre_clics == 2:
            self.reinitialiser_plage()



    def traiter_clic_droit(
        self, evenement: Event, donnees: Donnees, ax_2d: Axes, date_debut: datetime, date_fin: datetime
    ):
        doit_rafraichir = False

        self.maj_donnees_affichees(donnees, date_debut, date_fin)

        if self.points_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.maj_distances(evenement, ax_2d)

        date_plus_proche = self.trouver_date_plus_proche()

        seuil = 0.02
        if self.distances_point_souris.loc[date_plus_proche] > seuil:
            return doit_rafraichir

        donnees.invalider_date(date_plus_proche)

        self.reinitialiser_plage()

        doit_rafraichir = evenement.button
        return doit_rafraichir
    

    #-----Suppression plage

    def supprimer_plage(self, donnees: Donnees):
        doit_rafraichir = False

        # il faut exactement 2 clics
        if self.nombre_clics != 2:
            self.logger.info("Suppression de la plage impossible, car aucune plage sélectionnée.")
            self.reinitialiser_plage()
            return doit_rafraichir

        self.date_debut, self.date_fin = sorted((self.date_debut, self.date_fin))

        donnees.invalider_dates(self.date_debut, self.date_fin)

        self.reinitialiser_plage()

        doit_rafraichir = True
        return doit_rafraichir

        # TODO : Une ligne où la concentration est NaN, doit-elle pouvoir être invalidée ? Ou faut-il l'ignorer ?

        # FIXME : Si on invalide la toute dernière donnée ou bien toutes les données d'une page, toutes les données sont invalidées.

        # FIXME : Corriger le débordement de la plage sur les autres pages quand on sélectionne une plage sur une extrémité.
