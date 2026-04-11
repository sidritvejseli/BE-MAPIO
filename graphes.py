import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk


from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.image import AxesImage
from pandas import DataFrame


from donnees import Donnees


class Graphe2D:

    def __init__(self):
        self.fig, self.ax = plt.subplots()

    def tracer_graphe_2d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
        self.effacer_graphe_2d()

        donnees_dates = donnees.obtenir_dates(date_debut, date_fin)

        donnees_valides = donnees_dates.obtenir_donnees_valides()
        donnees_invalides = donnees_dates.obtenir_donnees_invalides()

        dataframe_valides = donnees_valides.obtenir_dataframe()
        dataframe_invalides = donnees_invalides.obtenir_dataframe()

        self.tracer_donnees(
            dataframe_valides,
            taille=1,
            couleur="blue",
            marqueur="x",
        )

        self.tracer_donnees(
            dataframe_invalides,
            taille=8,
            couleur="red",
            marqueur="x",
            legende_boite=f"Invalidés ({donnees_invalides.obtenir_nombre_dates()})",
        )

        self.legender_titre(date_debut)
        self.legender_abscisses()
        self.legender_ordonnees()
        self.legender_boite()

        self.tracer_grille()

    def effacer_graphe_2d(self):
        self.ax.clear()

    def tracer_donnees(
        self, donnees: Donnees, taille: int = "1", couleur: str = "blue", marqueur: str = "x", legende_boite: str = ""
    ):
        self.ax.scatter(
            donnees.index,
            donnees["smps_concTotal"],
            s=taille,
            color=couleur,
            marker=marqueur,
            label=legende_boite,
        )

    def legender_titre(self, date: datetime):
        self.ax.set_title(f"Jour : {date.date()}", fontsize=12)

    def legender_abscisses(self):
        self.ax.tick_params(axis="x", rotation=45)
        self.ax.set_xlabel("Date et heure", fontsize=5)

    def legender_ordonnees(self):
        self.ax.set_ylabel("Concentration totale", fontsize=5)

    def legender_boite(self):
        self.ax.legend()

    def tracer_grille(self):
        self.ax.grid(True, linestyle="--")


class Graphe3D:

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def tracer_graphe_3d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):
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

        carte_thermique = self.ax.imshow(dataframe.T, aspect="auto", origin="lower", cmap="RdYlBu")

        particules.convertir_titre_particules_en_float()

        self.legender_abscisses(particules)
        self.legender_ordonnees(particules)
        self.legender_barre_couleurs(carte_thermique)

        # TODO : Affichage des couleurs sur une échelle logarithmique, à la place de linéaire.

    def effacer_graphe_3d(self):
        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()

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
        self.ax.set_xticklabels(libelles_abscisse, rotation=45, ha="right")

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


class Heatmap3d:

    def __init__(self, parent):
        # onglet
        self.parent = parent
        # création de l'objet Heatmap
        self.heatmap = Graphe3D()

        # Frame principal qui va contenir le graphique
        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        # Création du canvas matplotlib dans Tkinter
        self.canvas = FigureCanvasTkAgg(self.heatmap.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def tracer_jour(self, donnees: DataFrame, date_debut: datetime, date_fin: datetime):
        if donnees is None or date_debut is None or date_fin is None:
            return
        # On demande à la classe Heatmap de dessiner le graphique
        self.heatmap.tracer_graphe_3d(donnees, date_debut, date_fin)
        # On met à jour l'affichage dans Tkinter
        self.canvas.draw()

    # TODO : Effacer la classe Heatmap3d.
