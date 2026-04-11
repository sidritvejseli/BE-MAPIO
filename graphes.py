import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pandas import DataFrame
import tkinter as tk
import pandas as pd
from datetime import datetime


from donnees import Donnees


class Graphe2D:

    def __init__(self):

        self.fig, self.ax = plt.subplots()

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

    def tracer_donnees(self, donnees: Donnees, taille="1", couleur="blue", marqueur="x", legende_boite=""):
        self.ax.scatter(
            donnees.index, donnees["smps_concTotal"], s=taille, color=couleur, marker=marqueur, label=legende_boite
        )

    def tracer_graphe_2d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):

        self.effacer_graphe_2d()

        donnees_valides = donnees.obtenir_donnees_valides(date_debut, date_fin)

        donnees_invalides = donnees.obtenir_donnees_invalides(date_debut, date_fin)

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
            legende_boite=f"Invalidés ({donnees_invalides.shape[0]})",
        )

        self.ax.scatter(donnees_invalides.index, donnees_invalides["smps_concTotal"], s=8, color="red", marker="x")

        self.legender_titre(date_debut)
        self.legender_abscisses()
        self.legender_ordonnees()
        self.legender_boite()

        self.tracer_grille()

    def effacer_graphe_2d(self):
        self.ax.clear()


class Graphe3D:

    def __init__(self):

        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def legender_abscisses(self, donnees_jour: DataFrame, nombre_graduations=12):

        self.ax.set_xlabel("Heure")

        graduations_abscisse = np.linspace(0, len(donnees_jour) - 1, nombre_graduations).astype(int)
        libelles_abscisse = donnees_jour.index[graduations_abscisse].strftime("%H:%M")

        self.ax.set_xticks(graduations_abscisse)
        self.ax.set_xticklabels(libelles_abscisse, rotation=45, ha="right")

    def legender_ordonnees(self, donnees_jour: DataFrame, nombre_graduations=10):

        self.ax.set_ylabel("Taille des particules (nanomètres)")

        graduations_ordonnee = np.linspace(0, len(donnees_jour.columns) - 1, nombre_graduations).astype(int)
        libelles_ordonnee = [donnees_jour.columns[i] for i in graduations_ordonnee]
        libelles_ordonnee = np.array([float(colonne.split("_")[2]) for colonne in libelles_ordonnee])

        self.ax.set_yticks(graduations_ordonnee)
        self.ax.set_yticklabels(libelles_ordonnee)

    def legender_barre_couleurs(self, carte_thermique):

        self.colorbar = self.ax.figure.colorbar(carte_thermique, ax=self.ax)
        self.colorbar.set_label("Teneur")

    def tracer_graphe_3d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime):

        self.effacer_graphe_3d()

        donnees_valides = donnees.obtenir_particules(date_debut, date_fin)
        donnees_invalides = donnees.obtenir_particules_invalides(date_debut, date_fin)

        donnees_graphe_3d = donnees_valides.copy()

        donnees_graphe_3d.loc[donnees_invalides.index] = np.nan

        carte_thermique = self.ax.imshow(donnees_graphe_3d.T, aspect="auto", origin="lower", cmap="RdYlBu")

        # TODO : Affichage des couleurs logarithmique, à la place de linéaire.

        self.legender_abscisses(donnees_graphe_3d)
        self.legender_ordonnees(donnees_graphe_3d)
        self.legender_barre_couleurs(carte_thermique)

    def effacer_graphe_3d(self):

        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()


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
