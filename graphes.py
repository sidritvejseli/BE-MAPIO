import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button
import numpy as np
from pandas import DataFrame
import tkinter as tk
from donnees import Donnees
import pandas as pd
from datetime import datetime


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

        self.effacer_jour()

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

    def effacer_jour(self):
        self.ax.clear()


class Graphe3D:

    def __init__(self):

        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def tracer_jour(self, donnees: Donnees, jour):

        self.effacer_jour()

        donnees_jour = donnees.obtenir_donnees(jour, jour + pd.Timedelta(days=1))
        donnees_jour = donnees_jour.loc[:, donnees_jour.columns.str.startswith("smps_d")]

        carte_thermique = self.ax.imshow(donnees_jour.T, aspect="auto", origin="lower", cmap="RdYlBu")

        # TODO : Affichage des couleurs logarithmique, à la place de linéaire.

        self.legender_abscisses(donnees_jour)
        self.legender_ordonnees(donnees_jour)
        self.legender_barre_couleurs(carte_thermique)

    def effacer_jour(self):

        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()

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

    def tracer_jour(self, donnees: DataFrame, jour):
        if donnees is None or jour is None:
            return
        # On demande à la classe Heatmap de dessiner le graphique
        self.heatmap.tracer_jour(donnees, jour)
        # On met à jour l'affichage dans Tkinter
        self.canvas.draw()
