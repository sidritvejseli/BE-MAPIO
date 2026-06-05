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
from historique import Action


class Interactions:

    def __init__(self):
        self.logger = logging.getLogger()

        self.distances_point_souris: DataFrame = None

        self.points_valides: Donnees = None  # Points visibles à l'écran.

        self.rectangle_selector: RectangleSelector = None
        self.rect_x1 = None
        self.rect_x2 = None
        self.rect_y1 = None
        self.rect_y2 = None
        self.est_en_mouvement_rectangle = False  # True = un rectangle est en train d'être modifié.
        self.est_valide_rectangle = False  # True = un rectangle est dessiné et prêt.

    #
    #
    # Rectangle de sélection.
    #
    #

    def initialiser_rectangle_selector(self, ax_2d):
        self.rectangle_selector = RectangleSelector(
            ax_2d,
            self.enregistrement_rectangle,  # Fonction appelée quand la souris est relâchée.
            useblit=True,  # On redessine uniquement le rectangle, et pas le graphe.
            button=[1],  # Clic gauche.
            minspanx=5,
            minspany=5,  # Taille minimum des axes.
            spancoords="pixels",
            interactive=True,  # Le rectangle est affiché pendant sa modification.
            props=dict(
                facecolor="red",
                edgecolor="darkred",
                alpha=0.2,
                fill=True,
                linestyle="--",
            ),
        )
        self.rectangle_selector.set_active(
            False
        )  # On désactive le rectangle pour l'activer uniquement quand le fichier est chargé.

    # Stockage des informations utiles du rectangle.
    def enregistrement_rectangle(self, clique, relache):
        self.rect_x1 = min(clique.xdata, relache.xdata)
        self.rect_x2 = max(clique.xdata, relache.xdata)
        self.rect_y1 = min(clique.ydata, relache.ydata)
        self.rect_y2 = max(clique.ydata, relache.ydata)
        self.est_en_mouvement_rectangle = False
        self.est_valide_rectangle = True

    # Réinitialisation des informations du rectangle.
    def reinitialiser_rectangle(self):
        self.rect_x1 = self.rect_x2 = None
        self.rect_y1 = self.rect_y2 = None

        self.est_en_mouvement_rectangle = False
        self.est_valide_rectangle = False

        if self.rectangle_selector is not None:
            self.rectangle_selector.clear()
            self.rectangle_selector.set_active(
                True
            )  # On réactive le widget pour pouvoir dessiner un nouveau rectangle.

    def mode_rectangle(self, donnees: Donnees, mode: Action, date_debut: datetime, date_fin: datetime):
        if not self.est_valide_rectangle:
            self.logger.info(f"L'action est impossible : aucun rectangle sélectionné.")
            return False

        # Conversion des coordonnées en dates.
        x_min = mdates.num2date(self.rect_x1).replace(tzinfo=None)
        x_max = mdates.num2date(self.rect_x2).replace(tzinfo=None)

        date_debut_selection = max(date_debut, min(x_min, date_fin))
        date_fin_selection = max(date_debut, min(x_max, date_fin))

        y_min = self.rect_y1
        y_max = self.rect_y2

        if mode is Action.SUPPRIMER:
            source = donnees.obtenir_donnees_valides()  # cible point valide
        elif mode is Action.RESTAURER:
            source = donnees.obtenir_donnees_invalides()  # cible point invalide

        # On filtre les points hors rectangle.
        masque = (
            source.obtenir_dates(date_debut_selection, date_fin_selection)
            .obtenir_concentration_smps_intervalle(y_min, y_max)
            .obtenir_colonne_concentration_smps_courante_non_nulle()
            .obtenir_colonne_dates()
            .obtenir_dataframe()
        )

        self.reinitialiser_rectangle()

        if masque.empty:
            return False

        if mode is Action.SUPPRIMER:
            donnees.invalider_dates(masque)

        elif mode is Action.RESTAURER:
            donnees.restaurer_dates(masque)

        return True

    def supprimer_plage_rectangle(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        return self.mode_rectangle(donnees, Action.SUPPRIMER, date_debut, date_fin)

    def restaurer_plage_rectangle(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        return self.mode_rectangle(donnees, Action.RESTAURER, date_debut, date_fin)

    #
    #
    # Zoom.
    #
    #

    def zoomer_rectangle(self, ax_2d):
        if not self.est_valide_rectangle:
            return False

        ax_2d.set_xlim(self.rect_x1, self.rect_x2)
        ax_2d.set_ylim(self.rect_y1, self.rect_y2)

        self.reinitialiser_rectangle()
        return True

    #
    #
    # Infobulle.
    #
    #

    # Calcul de la distance normalisée entre chaque point et la souris.
    def calculer_distances(self, evenement: Event, donnees: Donnees, ax_2d: Axes) -> DataFrame:
        x_points = mdates.date2num(donnees.obtenir_colonne_dates().obtenir_dataframe())
        y_points = donnees.obtenir_colonne_concentration_smps().obtenir_dataframe()

        x_souris = evenement.xdata
        y_souris = evenement.ydata

        # Coordonnées de la souris
        x_limite = ax_2d.get_xlim()
        y_limite = ax_2d.get_ylim()

        # Normalisation par rapport aux limites visibles (pas aux données).
        x_echelle = 1 / (x_limite[1] - x_limite[0])
        y_echelle = 1 / (y_limite[1] - y_limite[0])

        # Calcul de la distance euclidienne.
        distances = np.sqrt(((x_points - x_souris) * x_echelle) ** 2 + ((y_points - y_souris) * y_echelle) ** 2)

        return distances

    def trouver_date_plus_proche(self) -> datetime:
        return self.distances_point_souris.idxmin()

    def maj_donnees_affichees(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        self.points_valides = donnees.obtenir_dates(date_debut, date_fin)

    def maj_distances(self, evenement: Event, ax_2d: Axes):
        self.distances_point_souris = self.calculer_distances(evenement, self.points_valides, ax_2d)

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

        if donnees.est_vide() or infobulle is None:
            return doit_rafraichir

        doit_rafraichir = True

        # Si la souris n’est pas sur le graphe, alors on n'affiche pas l'infobulle.
        if evenement.inaxes != ax_2d or evenement.xdata is None:
            infobulle.set_visible(False)
            return doit_rafraichir

        self.maj_donnees_affichees(donnees, date_debut, date_fin)

        if self.points_valides.est_tout_na_concentration():
            return doit_rafraichir

        self.maj_distances(evenement, ax_2d)

        if self.distances_point_souris.isna().all():
            return doit_rafraichir

        date_plus_proche = self.trouver_date_plus_proche()

        # Seuil adaptatif (2% de la diagonale du graphe).
        seuil = 0.02
        if self.distances_point_souris.loc[date_plus_proche] > seuil:
            infobulle.set_visible(False)
            return doit_rafraichir

        # On récupère la concentration du point le plus proche.
        concentration = (
            self.points_valides.obtenir_colonne_concentration_smps().obtenir_date(date_plus_proche).obtenir_dataframe()
        )

        infobulle.set_text(f"{date_plus_proche.strftime('%d/%m %H:%M')}\nConc : {concentration:.1f}")

        # Positionnement de l'infobulle sur le graphe.
        infobulle.xy = (mdates.date2num(date_plus_proche), concentration)
        infobulle.set_visible(True)

        return doit_rafraichir

    #
    #
    # Gestion des clics.
    #
    #

    def repondre_apres_clic_souris(
        self,
        evenement: Event,
        donnees: Donnees,
        ax_2d: Axes,
        date_debut: datetime,
        date_fin: datetime,
    ):
        doit_rafraichir = False

        self.est_en_mouvement_rectangle = True

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

        if donnees.est_valide_date(date_plus_proche):
            donnees.invalider_date(date_plus_proche)
        else:
            donnees.restaurer_date(date_plus_proche)

        doit_rafraichir = True
        return doit_rafraichir
