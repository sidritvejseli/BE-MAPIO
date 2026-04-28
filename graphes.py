import logging
import matplotlib.pyplot as plt
import numpy as np


from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.image import AxesImage


from donnees import Donnees


class Graphe2D:

    def __init__(self):
        self.logger = logging.getLogger()

        self.fig, self.ax = plt.subplots()

    def est_vide(self):
        return not self.ax.has_data()

    def tracer_graphe_2d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        self.effacer_graphe_2d()

        donnees_dates = donnees.obtenir_dates(date_debut, date_fin)

        donnees_valides = donnees_dates.obtenir_donnees_valides()
        donnees_invalides = donnees_dates.obtenir_donnees_invalides()

        self.tracer_donnees(
            donnees_valides,
            taille=1,
            couleur="blue",
            marqueur="x",
        )

        self.tracer_donnees(
            donnees_invalides,
            taille=8,
            couleur="red",
            marqueur="x",
            legende_boite=f"Invalidés ({donnees_invalides.obtenir_nombre_dates()})",
        )

        self.legender_titre(date_debut)
        self.legender_abscisses()
        self.legender_ordonnees()
        # self.legender_boite()

        self.tracer_grille()

    def effacer_graphe_2d(self):
        self.ax.clear()

    def tracer_donnees(
        self, donnees: Donnees, taille: int = "1", couleur: str = "blue", marqueur: str = "x", legende_boite: str = ""
    ):
        dataframe_dates = donnees.obtenir_colonne_dates().obtenir_dataframe()
        dataframe_concentration = donnees.obtenir_colonne_concentration().obtenir_dataframe()

        self.ax.scatter(
            dataframe_dates,
            dataframe_concentration,
            s=taille,
            color=couleur,
            marker=marqueur,
            label=legende_boite,
        )

    def legender_titre(self, date: datetime):
        self.ax.set_title(f"Jour : {date.date()}")

    def legender_abscisses(self):
        self.ax.set_xlabel("Date et heure")

        formatter = mdates.DateFormatter("%H:%M")

        self.ax.xaxis.set_major_formatter(formatter)

        self.ax.tick_params(axis="x")

    def legender_ordonnees(self):
        self.ax.set_ylabel("Concentration totale")

    def legender_boite(self):
        self.ax.legend()

    def tracer_grille(self):
        self.ax.grid(True, linestyle="--")


class Graphe3D:

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def tracer_graphe_3d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime, teneur_maximum):
        self.effacer_graphe_3d()

        donnees_dates = donnees.obtenir_dates(date_debut, date_fin)

        donnees_invalides = donnees_dates.obtenir_donnees_invalides()

        particules = donnees_dates.obtenir_particules()
        particules_invalides = donnees_invalides.obtenir_particules()

        # Remarque : Il faut d'abord récupérer la validité des données avant de filtrer par particules,
        # car filtrer par particules enlève la colonne "smps_flag" qui note la validité d'une donnée.

        dataframe = particules.obtenir_dataframe()
        dataframe_invalides = particules_invalides.obtenir_dataframe()

        dataframe.loc[dataframe_invalides.index] = np.nan  # Suppression des données invalidées dans le graphe 3D.

        carte_thermique = self.ax.imshow(
            dataframe.T,
            aspect="auto",
            origin="lower",
            cmap="Spectral_r",
            vmin=0,
            vmax=teneur_maximum,
        )

        particules.convertir_titre_particules_en_float()

        self.legender_titre(date_debut)
        self.legender_abscisses(particules)
        self.legender_ordonnees(particules)
        self.legender_barre_couleurs(carte_thermique)

        # TODO : Affichage des couleurs sur une échelle logarithmique, à la place de linéaire.

        # FIXME : Le graphe 3D affiche les espaces blancs des données invalidées uniquement lorsqu'elles font toujours partie du fichier.
        # Si on charge un fichier qui ne contient que les données filtrées,
        # alors l'espace blanc n'apparaît plus, et le graphe donne l'impression d'être continu.

    def effacer_graphe_3d(self):
        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()

    def legender_titre(self, date: datetime):
        self.ax.set_title(f"Jour : {date.date()}")

    def legender_abscisses(self, particules: Donnees, nombre_graduations: int = 12):
        self.ax.set_xlabel("Heure")

        graduations_abscisse = np.linspace(
            start=0,
            stop=particules.obtenir_nombre_dates() - 1,
            num=nombre_graduations,
            dtype=int,
        )

        libelles_abscisse = particules.obtenir_dates_echantillon(graduations_abscisse)
        libelles_abscisse = libelles_abscisse.obtenir_dataframe()[:].strftime("%H:%M")

        self.ax.set_xticks(graduations_abscisse)
        self.ax.set_xticklabels(libelles_abscisse)

    def legender_ordonnees(self, particules: Donnees, nombre_graduations: int = 10):
        self.ax.set_ylabel("Taille des particules (nanomètres)")

        graduations_ordonnee = np.linspace(
            start=0,
            stop=particules.obtenir_nombre_colonnes() - 1,
            num=nombre_graduations,
            dtype=int,
        )

        libelles_ordonnee = particules.obtenir_noms_colonnes()
        libelles_ordonnee = libelles_ordonnee[graduations_ordonnee]

        self.ax.set_yticks(graduations_ordonnee)
        self.ax.set_yticklabels(libelles_ordonnee)

    def legender_barre_couleurs(self, carte_thermique: AxesImage):

        self.colorbar = self.ax.figure.colorbar(carte_thermique, ax=self.ax)
        self.colorbar.set_label("Teneur")
