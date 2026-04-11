import os
import pandas as pd
import tkinter as tk
import yaml


from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, Label, Menu, messagebox, ttk
from tkinter.simpledialog import askfloat
from tkinter.ttk import Notebook
from typing import Callable, TypeAlias


from donnees import Donnees
from graphes import Graphe2D, Graphe3D
from interactions import Interactions


ItemsMenu: TypeAlias = list[tuple[str, Callable, str]]
BarreMenus: TypeAlias = list[tuple[str, ItemsMenu]]

BarreOutils: TypeAlias = list[tuple[str, Callable]]

Onglets: TypeAlias = dict[str, ttk.Frame]


class Interface(tk.Tk, Interactions):

    def __init__(self):

        super().__init__()

        self.description_barre_menus: BarreMenus = [
            (
                "Fichier",
                [
                    ("Charger un fichier", None, self._action_charger),
                    ("Fermer sans enregistrer", None, self._action_fermer),
                    None,
                    ("Enregistrer sous", None, self._action_sauvegarder),
                    None,
                    ("Quitter", None, self._action_quitter),
                ],
            ),
            (
                "Actions",
                [
                    ("Invalider toutes les données", None, self._non_dispo),
                    ("Invalider les données du jour", None, self._non_dispo),
                    None,
                    ("Annuler", "Ctrl+Z", self._non_dispo),
                    None,
                    ("Appliquer un facteur de correction", None, self._non_dispo),
                ],
            ),
            (
                "Navigation",
                [
                    ("Sauter au premier jour", None, self.premier_jour),
                    ("Sauter au dernier jour", None, self.dernier_jour),
                    None,
                    ("Sauter au jour précédent", None, self.jour_precedent),
                    ("Sauter au jour suivant", None, self.jour_suivant),
                ],
            ),
        ]

        self.description_barre_outils: BarreOutils = [
            ("|◀ Premier", self.premier_jour),
            ("◀ Precedent", self.jour_precedent),
            ("Suivant ▶", self.jour_suivant),
            ("Dernier ▶|", self.dernier_jour),
            None,
            ("Actualiser", None),
            ("Invalider jour", None),
            ("Annuler", None),
            ("Facteur", self.demander_facteur),
            ("Supprimer plage", self.supprimer_plage),
        ]

        self.description_barre_onglets = ["Particules", "Fonctionnement", "Graphe 3D"]

        # configuration
        self.config = self._load_config("config.yaml")

        # variable :
        self.donnees = Donnees()
        self.donnees_originales = Donnees()
        self.fichier_courant = None
        self.date_debut = None
        self.date_fin = None
        self.tooltip = None

        # pour la plage

        self.selection_debut = None
        self.selection_fin = None
        self.ligne_debut = None
        self.ligne_fin = None

        # la fentre
        cfg_aff = self.config.get("affichage", {})
        self.title(cfg_aff.get("titre", "Outil SMPS - MAP-IO"))
        w = cfg_aff.get("largeur", 1400)
        h = cfg_aff.get("hauteur", 800)
        self.geometry(f"{w}x{h}")
        self.resizable(True, True)

        # les graphes
        self.graphe_2d = Graphe2D()
        self.graphe_3d = Graphe3D()

        self.construire_barre_menus()

        self.barre_outils_etiquette_jour: Label = None
        self.construire_barre_outils()

        self.barre_onglets: Notebook = None
        self.onglets: Onglets = {}
        self.construire_barre_onglets()

        # self.afficher_onglet_provisoire(self.onglets["Particules"])
        self.afficher_onglet_provisoire(self.onglets["Fonctionnement"])

        self._build_graph_area()

        # Fenêtre individuelle du graphe 3D.

        # Frame principal qui va contenir le graphique
        self.frame_3d_individuel = tk.Frame(self.onglets["Graphe 3D"])
        self.frame_3d_individuel.pack(fill="both", expand=True)

        # Création du canvas matplotlib dans Tkinter
        self.canvas_3d_individuel = FigureCanvasTkAgg(self.graphe_3d.fig, master=self.frame_3d_individuel)
        self.canvas_3d_individuel.get_tk_widget().pack(fill="both", expand=True)

    # graphes
    def _build_graph_area(self):

        self.main_frame = tk.Frame(self.onglets["Particules"])
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.rowconfigure(0, weight=1, minsize=300)
        self.main_frame.rowconfigure(1, weight=1, minsize=300)
        self.main_frame.columnconfigure(0, weight=1)

        # GRAPHE 2D
        self.frame_graphe2d = tk.Frame(self.main_frame)
        self.frame_graphe2d.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.canvas = FigureCanvasTkAgg(self.graphe_2d.fig, master=self.frame_graphe2d)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        self.canvas2d = self.canvas
        self.ax2d = self.graphe_2d.ax
        # quand l’utilisateur clique : appelle _au_clic
        self.canvas2d.mpl_connect("button_press_event", self._au_clic)
        self.canvas2d.mpl_connect("motion_notify_event", self.afficher_informations_point)

        # HEATMAP
        self.frame_heatmap = tk.Frame(self.main_frame)
        self.frame_heatmap.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.canvas_heat = FigureCanvasTkAgg(self.graphe_3d.fig, master=self.frame_heatmap)
        self.canvas_heat.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        # plage
        # interaction de la plage
        self.canvas2d = self.canvas
        self.ax2d = self.graphe_2d.ax

        # plage connex event souris
        # Quand l’utilisateur clique sur le graphe ça appelle la fonction _au_clic
        self.canvas2d.mpl_connect("button_press_event", self._au_clic)
        self.canvas2d.mpl_connect("motion_notify_event", self.afficher_informations_point)

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
        if self.donnees.est_vide():
            return
        if self.date_debut is not None:
            self.barre_outils_etiquette_jour.config(text=f"Jour affiche : {self.date_debut}")

    def _action_charger(self):
        chemin_initial = self.config.get("repertoires", {}).get("donnees", "")

        chemin_absolu_chargement = filedialog.askopenfilename(
            initialdir=chemin_initial,
            filetypes=[("CSV files", "*.csv"), ("All", "*.*")],
        )

        if not chemin_absolu_chargement:
            return

        self.donnees.charger_fichier_csv(chemin_absolu_chargement)

        if not self.donnees.est_vide():
            self.date_debut = self.donnees.obtenir_jour_minimum()
            self.date_fin = self.calculer_jour_suivant(self.date_debut)
            self.afficher_graphe()
            self.barre_outils_etiquette_jour.config(text=f"Jour affiche : {self.date_debut}")

    def _action_fermer(self):
        if self.donnees.est_vide():
            return
        if messagebox.askyesno("Confirmer", "Fermer sans sauvegarder ?"):
            self.donnees.fermer_fichier_csv()
            self.date_debut = None
            self.date_fin = None
            self.barre_outils_etiquette_jour.config(text="Aucun fichier charge")

    def _action_sauvegarder(self):
        cfg_rep = self.config.get("repertoires", {})
        dossier_resultats = cfg_rep.get("resultats", "resultats/")
        dossier_flags = cfg_rep.get("flags", "resultats/flags/")

        if self.donnees.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        chemin_absolu_sauvegarde = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )

        if not chemin_absolu_sauvegarde:
            return

        self.donnees.sauvegarder_fichier_csv(chemin_absolu_sauvegarde)
        self.donnees.fermer_fichier_csv()

    def _action_quitter(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.destroy()

    # affichage graphe

    def afficher_graphe(self):

        # FIXME : Corriger l'erreur qui s'affiche quand on approche la souris d'un jour vide.

        if self.donnees.est_vide() or self.date_debut is None or self.date_fin is None:
            return

        self.date_fin = self.calculer_jour_suivant(self.date_debut)
        self.graphe_2d.tracer_graphe_2d(self.donnees, self.date_debut, self.date_fin)
        self.canvas.draw()

        # infos des points
        self.tooltip = self.ax2d.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="orange", alpha=0.9),
            fontsize=8,
            visible=False,
        )

        self.graphe_3d.tracer_graphe_3d(self.donnees, self.date_debut, self.date_fin)
        self.canvas_heat.draw()

        # On met à jour l'affichage dans Tkinter
        self.canvas_3d_individuel.draw()

        self.barre_outils_etiquette_jour.config(text=f"Jour affiche : {self.date_debut}")

    # navigation jours

    def jour_suivant(self):
        if self.donnees.est_vide():
            return

        max_day = self.donnees.obtenir_jour_maximum()
        if self.date_debut < max_day:
            self.date_debut += pd.Timedelta(days=1)
            self.afficher_graphe()

    def jour_precedent(self):
        if self.donnees.est_vide():
            return

        min_day = self.donnees.obtenir_jour_minimum()
        if self.date_debut > min_day:
            self.date_debut -= pd.Timedelta(days=1)
            self.afficher_graphe()

    def premier_jour(self):
        if self.donnees.est_vide():
            return
        premier_j = self.donnees.obtenir_jour_minimum()
        self.date_debut = premier_j
        self.afficher_graphe()

    def dernier_jour(self):
        if self.donnees.est_vide():
            return
        dernier_j = self.donnees.obtenir_jour_maximum()
        self.date_debut = dernier_j
        self.afficher_graphe()

    # demande du facteur
    def demander_facteur(self):
        facteur = askfloat("Facteur", "Multiplier par :")
        if facteur is None:
            return
        # appel de la fonction interaction
        self.appliquer_facteur(facteur)

    def calculer_jour_suivant(self, jour: datetime):
        return jour + pd.Timedelta(days=1)

    def construire_menu_deroulant(self, barre_menus: Menu, nom_menu_deroulant: str, items_menu_deroulant: ItemsMenu):
        menu_deroulant = tk.Menu(barre_menus, tearoff=False)

        for item in items_menu_deroulant:
            if item is None:
                menu_deroulant.add_separator()
                continue

            etiquette, raccourci, fonction = item
            menu_deroulant.add_command(label=etiquette, command=fonction, accelerator=raccourci)

        barre_menus.add_cascade(label=nom_menu_deroulant, menu=menu_deroulant)

    def construire_barre_menus(self):
        barre_menus = tk.Menu(self)

        for nom_menu_deroulant, items_menu_deroulant in self.description_barre_menus:
            self.construire_menu_deroulant(barre_menus, nom_menu_deroulant, items_menu_deroulant)

        self.configure(menu=barre_menus)

    def construire_barre_outils(self):
        barre_outils = tk.Frame(self, bd=1, relief=tk.RAISED)
        barre_outils.pack(side=tk.TOP, fill=tk.X)

        for item in self.description_barre_outils:
            if item is None:
                tk.Label(barre_outils, text="  |  ").pack(side=tk.LEFT)
                continue

            etiquette, fonction = item

            if fonction is None:
                tk.Button(barre_outils, text=etiquette, state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)
                continue

            tk.Button(barre_outils, text=etiquette, command=fonction).pack(side=tk.LEFT, padx=2, pady=2)

        self.barre_outils_etiquette_jour = tk.Label(
            barre_outils, text="Aucun fichier chargé", font=("Arial", 10, "bold")
        )
        self.barre_outils_etiquette_jour.pack(side=tk.RIGHT, padx=10)

    def construire_barre_onglets(self):
        self.barre_onglets = ttk.Notebook(self)
        self.barre_onglets.pack(fill=tk.BOTH, expand=True)

        for etiquette in self.description_barre_onglets:
            onglet = ttk.Frame(self.barre_onglets)
            self.barre_onglets.add(onglet, text=etiquette)

            self.onglets[etiquette] = onglet

    def afficher_onglet_provisoire(self, etiquette_onglet: str):
        tk.Label(
            etiquette_onglet,
            text="Chargez un fichier CSV via : Fichier → Charger un fichier",
            font=("Arial", 13),
            fg="grey",
        ).place(relx=0.5, rely=0.5, anchor="center")
