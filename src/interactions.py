import logging
import matplotlib.dates as mdates
import numpy as np


from datetime import datetime
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.text import Annotation
from matplotlib.widgets import RectangleSelector
from pandas import DataFrame


from donnees import Donnees


class Interactions:

    def __init__(self):
        self.logger = logging.getLogger()

        # distances calculees entre chaque point et la souris
        self.distances_point_souris: DataFrame = None

        # points visibles a l'ecran
        self.points_valides: Donnees = None

        # RectangleSelector pour la sélection de plage
        self.rectangle_selector = None
        self.rect_x1 = None
        self.rect_x2 = None
        self.rect_y1 = None
        self.rect_y2 = None
        self.rectangle_actif = False  # True = un rectangle est dessiné et prêt

    def initialiser_rectangle_selector(self, ax_2d):  #: Axes
        self.rectangle_selector = RectangleSelector(
            ax_2d,  # graphe ou il dessine
            self.enregistrement_rectangle,  # quand on relache la souris , il fait ça
            useblit=True,  # trouver sur internet (redessine que le rectangle pas le graphe)
            button=[1],  # clic gauche
            minspanx=5,
            minspany=5,  # taille min de laxe x et y
            spancoords="pixels",
            interactive=True,  # affiche le rectangle pendant le glisser
            props=dict(
                facecolor="red",
                edgecolor="darkred",
                alpha=0.2,
                fill=True,
                linestyle="--",
            ),
        )
        self.rectangle_selector.set_active(False)  # on desactive le rect apres

    # utile pour apres relacher (stock les infos)
    def enregistrement_rectangle(self, clique, relache):

        self.rect_x1 = min(clique.xdata, relache.xdata)
        self.rect_x2 = max(clique.xdata, relache.xdata)
        self.rect_y1 = min(clique.ydata, relache.ydata)
        self.rect_y2 = max(clique.ydata, relache.ydata)
        self.rectangle_actif = True
        # self.logger.info("Rectangle sélectionné.")

    # appler par le bouton selectinner plage
    def activer_mode_rectangle(self):
        if self.rectangle_selector is None:
            return
        self.reinitialiser_rectangle()
        self.rectangle_selector.set_active(True)

    # remet tout a zero
    def reinitialiser_rectangle(self):
        # effache les cordonner stocker en haut
        self.rect_x1 = self.rect_x2 = None
        self.rect_y1 = self.rect_y2 = None
        # remet le flag a faux pour dire plus rine a supprimer
        self.rectangle_actif = False
        if self.rectangle_selector is not None:
            self.rectangle_selector.set_active(False)
            self.rectangle_selector.clear()

    # Invalide tous les points valides contenus dans le rectangle def supprimer_plage_rectangle(self, donnees: Donnees) -> bool:
    def supprimer_plage_rectangle(self, donnees: Donnees):

        # Si aucun rectangle dessine, on ne fait rien
        if not self.rectangle_actif:
            self.logger.info("Suppression des données impossible car aucun rectangle sélectionné.")
            return False

        # replace(tzinfo=None) pour pas que pandas plante (vuseau pas attendu)
        date_debut = mdates.num2date(self.rect_x1).replace(tzinfo=None)
        date_fin = mdates.num2date(self.rect_x2).replace(tzinfo=None)
        y_min = self.rect_y1
        y_max = self.rect_y2

        # On récupère le tableau pandas complet
        # le point est dans le  rectangle et il est encore valide
        masque = (
            donnees.obtenir_donnees_valides()
            .obtenir_dates(date_debut, date_fin)
            .obtenir_concentration_intervalle(y_min, y_max)
            .obtenir_colonne_concentration()
            .obtenir_colonne_dates()
            .obtenir_dataframe()
        )

        # si correspond au masque , on le vire
        donnees.invalider_dates(masque)

        self.reinitialiser_rectangle()
        return True

    def zoomer_rectangle(self, ax_2d):

        # si pas de rectangle , on fait rien
        if not self.rectangle_actif:
            return False

        ax_2d.set_xlim(self.rect_x1, self.rect_x2)
        ax_2d.set_ylim(self.rect_y1, self.rect_y2)

        self.reinitialiser_rectangle()
        return True

    # calcule la distance normalisee entre chaque point et la souris
    def calculer_distances(self, evenement: Event, donnees: Donnees, ax_2d: Axes) -> DataFrame:

        x_points = mdates.date2num(donnees.obtenir_colonne_dates().obtenir_dataframe())
        y_points = donnees.obtenir_colonne_concentration().obtenir_dataframe()

        x_souris = evenement.xdata
        y_souris = evenement.ydata

        # coordonnees de la souris
        x_limite = ax_2d.get_xlim()
        y_limite = ax_2d.get_ylim()

        # Normalisation par rapport aux limites visibles (pas aux données).
        x_echelle = 1 / (x_limite[1] - x_limite[0])
        y_echelle = 1 / (y_limite[1] - y_limite[0])

        # Calcul de la distance euclidienne.
        distances = np.sqrt(((x_points - x_souris) * x_echelle) ** 2 + ((y_points - y_souris) * y_echelle) ** 2)

        return distances

    # --------- Calcule des distances

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
        self.distances_point_souris = self.calculer_distances(evenement, self.points_valides, ax_2d)

    # -----infobulle

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

        # recupere la concentration du point le plus proche
        concentration = (
            self.points_valides.obtenir_colonne_concentration().obtenir_date(date_plus_proche).obtenir_dataframe()
        )

        # met a jour le texte et la position du tooltip sur le graphe
        infobulle.set_text(f"{date_plus_proche.strftime('%d/%m %H:%M')}\nConc : {concentration:.1f}")

        # Positionnement de l'infobulle sur le graphe.
        infobulle.xy = (mdates.date2num(date_plus_proche), concentration)
        infobulle.set_visible(True)

        return doit_rafraichir

    # ------Gestion des clic

    def repondre_apres_clic_souris(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
    ):
        doit_rafraichir = False

        # Clic hors du graphe : on ignore.
        if evenement.inaxes != ax_2d or evenement.xdata is None:
            return doit_rafraichir

        # Bouton 3 = clic droit : suppression d'un point unique.
        if evenement.button == 3:
            doit_rafraichir = self.traiter_clic_droit(evenement, donnees, ax_2d, date_debut, date_fin)

        return doit_rafraichir

    def traiter_clic_droit(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
    ):
        if date_debut is None or date_fin is None:
            return False

        doit_rafraichir = False

        self.maj_donnees_affichees(donnees, date_debut, date_fin)

        if self.points_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.maj_distances(evenement, ax_2d)
        date_plus_proche = self.trouver_date_plus_proche()

        if date_plus_proche is None:
            return doit_rafraichir

        seuil = 0.02
        if self.distances_point_souris.loc[date_plus_proche] > seuil:
            return doit_rafraichir

        donnees.invalider_date(date_plus_proche)

        doit_rafraichir = True
        return doit_rafraichir

        # FIXME : Une ligne où la concentration est NaN, doit-elle pouvoir être invalidée ? Ou faut-il l'ignorer ?
