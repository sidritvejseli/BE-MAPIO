import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button
import numpy as np
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
        

class Graphe3D:

    def __init__(self):

        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def tracer_jour(self, donnees: DataFrame, jour):

        self.effacer_jour()

        donnees_jour = donnees[donnees["datetime"].dt.date == jour]
        donnees_jour = donnees_jour.set_index("datetime")
        donnees_jour = donnees_jour.loc[
            :, donnees_jour.columns.str.startswith("smps_d")
        ]

        carte_thermique = self.ax.imshow(
            donnees_jour.T, aspect="auto", origin="lower", cmap="RdYlBu"
        )

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

        graduations_abscisse = np.linspace(
            0, len(donnees_jour) - 1, nombre_graduations
        ).astype(int)
        libelles_abscisse = donnees_jour.index[graduations_abscisse].strftime("%H:%M")

        self.ax.set_xticks(graduations_abscisse)
        self.ax.set_xticklabels(libelles_abscisse, rotation=45, ha="right")

    def legender_ordonnees(self, donnees_jour: DataFrame, nombre_graduations=10):

        self.ax.set_ylabel("Taille des particules (nanomètres)")

        graduations_ordonnee = np.linspace(
            0, len(donnees_jour.columns) - 1, nombre_graduations
        ).astype(int)
        libelles_ordonnee = [donnees_jour.columns[i] for i in graduations_ordonnee]
        libelles_ordonnee = np.array(
            [float(colonne.split("_")[2]) for colonne in libelles_ordonnee]
        )

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
