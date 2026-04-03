import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
from pandas import DataFrame
import tkinter as tk


class Graphe2D:

    def __init__(self):

        self.fig, self.ax = plt.subplots()

    def tracer_jour(self, donnees: DataFrame, jour):

        donnees_jour = donnees[donnees["datetime"].dt.date == jour]

        # Séparation des données valides aux données invalides.

        donnees_invalides = donnees_jour[donnees_jour["smps_flag"] != 0]

        self.ax.clear()
        self.ax.set_title(f"Jour : {jour}", fontsize=12)
        self.ax.tick_params(axis="x", rotation=45)

        self.ax.scatter(
            donnees_jour["datetime"], donnees_jour["smps_concTotal"], s=1, color="blue"
        )

        # Traçage des données invalidées en rouge, afin de les différencier.

        if not donnees_invalides.empty:
            self.ax.scatter(
                donnees_invalides["datetime"],
                donnees_invalides["smps_concTotal"],
                s=8,
                color="red",
                marker="x",
                label=f"Invalidés ({len(donnees_invalides)})",
            )

        self.ax.set_xlabel("Date et heure", fontsize=5)
        self.ax.set_ylabel("Concentration totale", fontsize=5)

        self.ax.grid(True, linestyle="--")
        self.fig.autofmt_xdate()


class Heatmap:

    def __init__(self):

        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def tracer_jour(self, donnees: DataFrame, jour):

        donnees_jour = donnees[donnees["datetime"].dt.date == jour]

        # Séparation des données valides aux données invalides.

        donnees_valides = donnees_jour[donnees_jour["smps_flag"] == 0]

        colonnes = sorted(donnees.columns[donnees.columns.str.startswith("smps_d_")])

        taille_colonne = np.array([float(c.split("_")[2]) for c in colonnes])

        # Suppression de l'ancienne barre de couleurs.

        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        # Nettoyage du graphe.

        self.ax.clear()
        self.ax.set_title(f"Heatmap - {jour}")
        self.ax.set_xlabel("Temps")
        self.ax.set_ylabel("Taille (nm)")

        # On construit une matrice :
        # lignes = tailles
        # colonnes = temps

        data = np.array(donnees_valides[colonnes]).T

        # Nettoyage simple.

        data = np.where(data <= 0, np.nan, data)

        # Calcul des bornes pour la couleur
        vmin = max(np.nanpercentile(data, 2), 1)
        vmax = np.nanpercentile(data, 99)

        # Heatmap
        im = self.ax.pcolormesh(
            np.array(donnees_valides["datetime"]),  # axe X = temp
            taille_colonne,  # axe Y = tailles
            data,  # matrice des valeurs
            norm=mcolors.LogNorm(vmin=vmin, vmax=vmax),  # échelle
            cmap="Spectral_r",  # palette de couleurs
            shading="auto",
        )

        # Axe log (important pour SMPS)
        self.ax.set_yscale("log")
        self.ax.set_ylim(taille_colonne[0], taille_colonne[-1])
        self.ax.tick_params(axis="x", rotation=45)

        # On crée la colorbar (échelle des couleurs)
        self.colorbar = self.fig.colorbar(im, ax=self.ax, fraction=0.02, pad=0.02)
        self.colorbar.set_label("Concentration")

        # Vérifier données
        if len(donnees_jour) == 0:
            self.ax.text(0.5, 0.5, "Pas de données", ha="center")
            return

        # Ajuste automatiquement les dates pour qu'elles ne se chevauchent pas
        self.fig.autofmt_xdate()


class Heatmap3d:

    def __init__(self, parent):
        # onglet
        self.parent = parent
        # création de l'objet Heatmap
        self.heatmap = Heatmap()

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
