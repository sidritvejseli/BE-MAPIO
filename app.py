import tkinter as tk
from tkinter import messagebox
import yaml
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from donnees import Donnees
from graphes import Graphe2D, Graphe3D, Heatmap3d
from menu import build_menu, build_toolbar, build_tabs, show_placeholder
from interactions import Interaction

class App(tk.Tk, Donnees,Interaction):

    def __init__(self):
        super().__init__()

        # configuration
        self.config = self._load_config("config.yaml")

        # variable :
        self.donnees = None
        self.donnees_original = None
        self.current_file = None
        self.current_day = None
        self.tooltip = None

        # la fentre
        cfg_aff = self.config.get("affichage", {})
        self.title(cfg_aff.get("titre", "Outil SMPS - MAP-IO"))
        w = cfg_aff.get("largeur", 1400)
        h = cfg_aff.get("hauteur", 800)
        self.geometry(f"{w}x{h}")
        self.resizable(True, True)

        # les graphes
        self.plotter = Graphe2D()
        self.heatmap = Graphe3D()

        build_menu(self)
        self.label_jour = build_toolbar(self)

        (
            self.notebook,
            self.tab_particules,
            self.tab_fonctionnement,
            self.tab_heatmap_3d,
        ) = build_tabs(self)

        show_placeholder(self.tab_particules)
        show_placeholder(self.tab_fonctionnement)

        self.heatmap3d = Heatmap3d(self.tab_heatmap_3d)

        self._build_graph_area()


    # graphes
    def _build_graph_area(self):

        self.main_frame = tk.Frame(self.tab_particules)
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.rowconfigure(0, weight=1, minsize=300)
        self.main_frame.rowconfigure(1, weight=1, minsize=300)
        self.main_frame.columnconfigure(0, weight=1)

        # GRAPHE 2D
        self.frame_graphe2d = tk.Frame(self.main_frame)
        self.frame_graphe2d.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.canvas = FigureCanvasTkAgg(self.plotter.fig, master=self.frame_graphe2d)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        self.canvas2d = self.canvas
        self.ax2d = self.plotter.ax
        #quand l’utilisateur clique : appelle _au_clic
        self.canvas2d.mpl_connect("button_press_event", self._au_clic)
        self.canvas2d.mpl_connect("motion_notify_event", self.info_point)

        # HEATMAP
        self.frame_heatmap = tk.Frame(self.main_frame)
        self.frame_heatmap.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.canvas_heat = FigureCanvasTkAgg(
            self.heatmap.fig, master=self.frame_heatmap
        )
        self.canvas_heat.get_tk_widget().pack(
            fill="both", expand=True, padx=20, pady=20
        )

    # config yaml

    def _load_config(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        print(f"config.yaml introuvable : {path}")
        return {}

    # fonctions utilitaires 

    def _non_dispo(self):
        messagebox.showinfo("Info", "Fonctionnalite pas encore disponible")

    # refresh 

    def _refresh_all(self):
        if self.donnees is None:
            return
        if self.current_day is not None:
            self.label_jour.config(text=f"Jour affiche : {self.current_day}")

    def _action_charger(self):
        dossier_defaut = self.config.get("repertoires", {}).get("donnees", "")
        self.charger_fichier_csv(dossier_defaut)

        if self.donnees is not None:
            self.current_day = self.donnees["datetime"].dt.date.min()
            self.afficher_graphe()
            self.label_jour.config(text=f"Jour affiche : {self.current_day}")

    def _action_fermer(self):
        if self.donnees is None:
            return
        if messagebox.askyesno("Confirmer", "Fermer sans sauvegarder ?"):
            self.fermer_fichier_csv()
            self.current_day = None
            self.label_jour.config(text="Aucun fichier charge")

    def _action_sauvegarder(self):
        cfg_rep = self.config.get("repertoires", {})
        dossier_resultats = cfg_rep.get("resultats", "resultats/")
        dossier_flags = cfg_rep.get("flags", "resultats/flags/")
        self.sauvegarder_fichier_csv()

    def _action_quitter(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.destroy()

    # affichage graphe

    def afficher_graphe(self):
        if self.donnees is None or self.current_day is None:
            return

        self.plotter.tracer_jour(self.donnees, self.current_day)
        self.canvas.draw()

        #infos des points
        self.tooltip = self.ax2d.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="orange", alpha=0.9),
            fontsize=8,
            visible=False
        )

        self.heatmap.tracer_jour(self.donnees, self.current_day)
        self.canvas_heat.draw()

        if hasattr(self, "heatmap3d"):
            self.heatmap3d.tracer_jour(self.donnees, self.current_day)

        self.label_jour.config(text=f"Jour affiche : {self.current_day}")

    # navigation jours

    def jour_suivant(self):
        if self.donnees is None:
            return

        max_day = self.donnees["datetime"].dt.date.max()
        if self.current_day < max_day:
            self.current_day += pd.Timedelta(days=1)
            self.afficher_graphe()

    def jour_precedent(self):
        if self.donnees is None:
            return

        min_day = self.donnees["datetime"].dt.date.min()
        if self.current_day > min_day:
            self.current_day -= pd.Timedelta(days=1)
            self.afficher_graphe()


    def premier_jour(self):
        if self.donnees is None:
            return
        premier_j = self.donnees["datetime"].dt.date.min()
        self.current_day = premier_j
        self.afficher_graphe()

    def dernier_jour(self):
        if self.donnees is None:
            return
        dernier_j = self.donnees["datetime"].dt.date.max()
        self.current_day = dernier_j
        self.afficher_graphe()
