import numpy as np
import matplotlib.dates as mdates
import matplotlib.colors as plc
import matplotlib.pyplot as plt
import tkinter as tk
import pandas as pd

import matplotlib.pyplot as plt


class Graphe2D:
    def __init__(self):
        self.fig, self.ax = plt.subplots()

    def plot_day(self, df, day):
        df_day = df[df["datetime"].dt.date == day]

        # Sépare valides et invalidés
        invalides = df_day[df_day["smps_flag"] != 0]

        self.ax.clear()
        self.ax.set_title(f"Jour : {day}", fontsize = 12)
        self.ax.tick_params(axis='x', rotation=45)

        self.ax.scatter(
            df_day["datetime"],
            df_day["smps_concTotal"],
            s=1,
            color="blue"
        )

        # Points invalidés en rouge pour différencié
        if len(invalides) > 0:
            self.ax.scatter(          
                invalides["datetime"],
                invalides["smps_concTotal"],
                s=8,
                color="red",
                marker="x",
                label=f"Invalidés ({len(invalides)})",
            )

       
        self.ax.set_xlabel("Date et heure", fontsize=5)
        self.ax.set_ylabel("Concentration totale", fontsize=5)

        self.ax.grid(True, linestyle="--")
        self.fig.autofmt_xdate()



        #-------------

class Heatmap:
    def __init__(self):
        # Creation de la figure matplotlib et l axe
        # fig = la "fenêtre" du graphe
        # ax = la zone où on dessine
        self.fig, self.ax = plt.subplots()
        self.colorbar = None  # pour éviter les duplications

    def plot_day(self, df, day):
        # Filtrer le jour
        # On garde uniquement les lignes correspondant au jour selectionne:

        df_day = df[df["datetime"].dt.date == day]

        # On garde seulement les donnees valides (voir si pas deja fait ailleur)
        valides = df_day[df_day["smps_flag"] == 0].sort_values("datetime")

        # Colonnes des tailles
        bin_cols = sorted([c for c in df.columns if c.startswith("smps_d_")])
        # Tailles en nm
        bins_nm  = np.array([float(c.split("_")[2]) for c in bin_cols])


        # Supprimer l'ancienne colorbar avant de redessiner(car jai eu des probleme)
        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None
        
    
        # Nettoyer le graphe
        self.ax.clear()
        self.ax.set_title(f"Heatmap - {day}")
        self.ax.set_xlabel("Temps")
        self.ax.set_ylabel("Taille (nm)")


        

        # On construit une matrice :
        # lignes = tailles
        # colonnes = temps
        data = np.array(valides[bin_cols]).T
        # Nettoyage simple
        data = np.where(data <= 0, np.nan, data)

        # Calcul des bornes pour la couleur
        vmin = max(np.nanpercentile(data, 2), 1)
        vmax = np.nanpercentile(data, 99)

        

        # Heatmap
        im = self.ax.pcolormesh(
                np.array(valides["datetime"]),# axe X = temp
                  bins_nm, # axe Y = tailles
                  data,# matrice des valeurs
                norm=plc.LogNorm(vmin=vmin, vmax=vmax),# échelle
                cmap="Spectral_r",# palette de couleurs
                  shading="auto",
            )

        # Axe log (important pour SMPS)
        self.ax.set_yscale("log")
        self.ax.set_ylim(bins_nm[0], bins_nm[-1])
        self.ax.tick_params(axis='x', rotation=45)

        # On crée la colorbar (échelle des couleurs)
        self.colorbar = self.fig.colorbar(im, ax=self.ax, fraction=0.02, pad=0.02)
        self.colorbar.set_label("Concentration")

        # Vérifier données
        if len(df_day) == 0:
            self.ax.text(0.5, 0.5, "Pas de données", ha="center")
            return

         # Ajuste automatiquement les dates pour qu'elles ne se chevauchent pas
        self.fig.autofmt_xdate()
        
        