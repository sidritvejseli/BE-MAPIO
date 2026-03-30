import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

from loader import LoaderMixin
from savers import SaversMixin

from graphes_2D import Graphe2D

# les imports suivants seront actives au fur et a mesure
# from corrections import CorrectionsMixin
# from filters import FiltersMixin


# classe principale qui assemble les mixins
class App(tk.Tk, LoaderMixin, SaversMixin):

    def __init__(self):
        super().__init__()

        # on charge la config pour avoir les chemins et parametres
        self.config = self._load_config("config.yaml")

        # variables globales de l'application
        self.df           = None    # dataframe courant
        self.df_original  = None    # copie pour le reset
        self.current_file = None    # chemin du fichier charge
        self.current_day  = None    # jour affiche sur les graphes

        #frame afin d'ajouter les graphes

        # ces variables seront utiles quand on ajoutera les corrections et filtres
        # self.annuler_stack = []
        # self.sel_x1 = self.sel_x2 = None
        # self.click_n = 0

        # configuration de la fenetre
        cfg_aff = self.config.get("affichage", {})
        self.title(cfg_aff.get("titre", "Outil SMPS - MAP-IO"))
        w = cfg_aff.get("largeur", 1400)
        h = cfg_aff.get("hauteur", 800)
        self.geometry(f"{w}x{h}")
        self.resizable(True, True)

        self.plotter = Graphe2D()

        # construction de l'interface
        self._build_menu()
        self._build_toolbar()
        self._build_tabs()

        #affichage du graphe

        #frame principal de l'app : graphe2d, graphe3d, log
# Frame principal
        self.main_frame = tk.Frame(self.tab_particules)
        self.main_frame.pack(fill="both", expand=True)

        # Configurer les lignes : ligne 0 = 50%, ligne 1 = 50%
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.main_frame.rowconfigure(0, weight=1, minsize=300)
        self.main_frame.rowconfigure(1, weight=1, minsize=300)

        # GRAPHE 2D 
        self.frame_graphe2d = tk.Frame(self.main_frame)
        self.frame_graphe2d.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.canvas = FigureCanvasTkAgg(self.plotter.fig, master=self.frame_graphe2d)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        self.plotter.fig

    # ----------------------------------------------------------------
    # chargement de la config yaml
    # ----------------------------------------------------------------

    def _load_config(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        print(f"config.yaml introuvable : {path}")
        return {}

    # ----------------------------------------------------------------
    # menu principal
    # ----------------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        # menu Fichier
        menu_fichier = tk.Menu(menubar, tearoff=0)
        menu_fichier.add_command(label="Charger un fichier",      command=self._action_charger)
        menu_fichier.add_command(label="Fermer sans sauvegarder", command=self._action_fermer)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Sauvegarder",             command=self._action_sauvegarder)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter",                 command=self._action_quitter)
        menubar.add_cascade(label="Fichier", menu=menu_fichier)

        # menu Actions (sera complete avec corrections et filtres)
        menu_actions = tk.Menu(menubar, tearoff=0)
        menu_actions.add_command(label="Invalider toutes les donnees",       command=self._non_dispo)
        menu_actions.add_command(label="Invalider les donnees du jour",      command=self._non_dispo)
        menu_actions.add_separator()
        menu_actions.add_command(label="Annuler (Ctrl+Z)",                   command=self._non_dispo)
        menu_actions.add_separator()
        menu_actions.add_command(label="Appliquer un facteur de correction", command=self._non_dispo)
        menubar.add_cascade(label="Actions", menu=menu_actions)

        # menu Navigation (sera complete avec les graphes)
        menu_nav = tk.Menu(menubar, tearoff=0)
        menu_nav.add_command(label="Premier jour",   command=self._non_dispo)
        menu_nav.add_command(label="Jour precedent", command=self.prev_day)
        menu_nav.add_command(label="Jour suivant",   command=self.next_day)
        #menu_nav.add_command(label="Dernier jour",   command=self._non_dispo)
        menubar.add_cascade(label="Navigation", menu=menu_nav)

        self.configure(menu=menubar)

    def _non_dispo(self):
        # fonction temporaire pour les boutons pas encore implementes
        messagebox.showinfo("Info", "Fonctionnalite pas encore disponible")

    # ----------------------------------------------------------------
    # barre d'outils (navigation desactivee pour l'instant)
    # ----------------------------------------------------------------

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # boutons de navigation, seront relies aux graphes plus tard
        tk.Button(toolbar, text="|◀ Premier",  command = self.premier_jour ).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="◀ Precedent", command=self.prev_day).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Suivant ▶",   command=self.next_day).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Dernier ▶|",  state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Label(toolbar, text="  |  ").pack(side=tk.LEFT)

        tk.Button(toolbar, text="Invalider jour", state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Annuler (Z)",    state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)

        # label qui affiche le jour courant
        self.label_jour = tk.Label(toolbar, text="Aucun fichier charge", font=("Arial", 10, "bold"))
        self.label_jour.pack(side=tk.RIGHT, padx=10)

    # ----------------------------------------------------------------
    # onglets
    # ----------------------------------------------------------------

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # onglet 1 : particules
        self.tab_particules = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_particules, text="  Particules  ")

        # onglet 2 : fonctionnement
        self.tab_fonctionnement = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fonctionnement, text="  Fonctionnement  ")

        self._show_placeholder(self.tab_particules)
        self._show_placeholder(self.tab_fonctionnement)

    def _show_placeholder(self, parent):
        tk.Label(
            parent,
            text="Chargez un fichier CSV via Fichier → Charger un fichier",
            font=("Arial", 13), fg="grey"
        ).place(relx=0.5, rely=0.5, anchor="center")

    # ----------------------------------------------------------------
    # refresh : sera complete quand les graphes seront prets
    # ----------------------------------------------------------------

    def _refresh_all(self):
        if self.df is None:
            return
        if self.current_day is not None:
            self.label_jour.config(text=f"Jour affiche : {self.current_day}")
        # self._plot_conc_total()
        # self._plot_3D()
        # self._plot_correlation()

    # ----------------------------------------------------------------
    # actions menu Fichier
    # ----------------------------------------------------------------

    def _action_charger(self):
        dossier_defaut = self.config.get("repertoires", {}).get("donnees", "")
        self.load_csv(dossier_defaut)

        #apres avoir chargées les données, initialiser le jour courant pour l'affichage
        self.current_day = self.df["datetime"].dt.date.min()
        self.afficher_graphe()
        if self.df is not None:
            self.current_day = self.df["datetime"].dt.date.min()
            self.label_jour.config(text=f"Jour affiche : {self.current_day}")
            # self._build_graphes()

    def _action_fermer(self):
        if self.df is None:
            return
        if messagebox.askyesno("Confirmer", "Fermer sans sauvegarder ?"):
            self.close_file()
            self.current_day = None
            self.label_jour.config(text="Aucun fichier charge")

    def _action_sauvegarder(self):
        cfg_rep = self.config.get("repertoires", {})
        dossier_resultats = cfg_rep.get("resultats", "resultats/")
        dossier_flags     = cfg_rep.get("flags", "resultats/flags/")
        self.save_csv(dossier_resultats, dossier_flags)

    def _action_quitter(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.destroy()

#fonction utilisée dans le app pour afficher le graphe
    def afficher_graphe(self):
        if self.df is None or self.current_day is None:
            return

        self.plotter.plot_day(self.df, self.current_day)
        self.canvas.draw()

#fonctions pour modifier le jour courant 

    def next_day(self):
        if self.df is None:
            return

        max_day = self.df["datetime"].dt.date.max()
        if self.current_day < max_day:
            self.current_day += pd.Timedelta(days=1)
            self.afficher_graphe()

    def prev_day(self):
        if self.df is None:
            return

        min_day = self.df["datetime"].dt.date.min()
        if self.current_day > min_day:
            self.current_day -= pd.Timedelta(days=1)
            self.afficher_graphe()

    def premier_jour(self):
        if self.df is None:
            return
        self.current_day = self.df["datetime"].dt.date.min()
        

# point d'entree
if __name__ == "__main__":
    app = App()
    app.mainloop()