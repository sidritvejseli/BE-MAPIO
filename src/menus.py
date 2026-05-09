import tkinter as tk


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, Menu, Frame, Label, Widget
from typing import Callable, TypeAlias


from graphes import Graphe

# (Titre de l'item, Raccourci, Fonction appelée). Pour un séparateur, on met None.
DescriptionMenuItems: TypeAlias = list[tuple[str, str, Callable]]

# (Nom du menu déroulant, Description du menu déroulant).
DescriptionBarreMenus: TypeAlias = list[tuple[str, DescriptionMenuItems]]


class BarreMenus:

    def __init__(self, application: tk.Tk, description_barre_menus: DescriptionBarreMenus):
        self.application: tk.Tk = application
        self.description_barre_menus: DescriptionBarreMenus = description_barre_menus

    def construire_barre_menus(self):
        barre_menus: Menu = tk.Menu(self.application)

        for nom_menu_deroulant, items_menu_deroulant in self.description_barre_menus:
            self.construire_menu_deroulant(barre_menus, nom_menu_deroulant, items_menu_deroulant)

        self.application.configure(menu=barre_menus)

    def construire_menu_deroulant(
        self, barre_menus: Menu, nom_menu_deroulant: str, items_menu_deroulant: DescriptionMenuItems
    ):
        menu_deroulant = tk.Menu(barre_menus, tearoff=False)

        for item in items_menu_deroulant:
            if item is None:
                menu_deroulant.add_separator()
                continue

            etiquette, raccourci, fonction = item
            menu_deroulant.add_command(label=etiquette, command=fonction, accelerator=raccourci)

        barre_menus.add_cascade(label=nom_menu_deroulant, menu=menu_deroulant)


# (Titre de l'outil, Fonction appelée).
DescriptionBarreOutils: TypeAlias = list[tuple[str, Callable]]


class BarreOutils:

    def __init__(self, application: tk.Tk, description_barre_outils: DescriptionBarreOutils):
        self.application = application
        self.description_barre_outils = description_barre_outils

        self.barre_outils: Frame = None

        self.etiquette: Label = None

    def construire_barre_outils(self):
        self.barre_outils: Frame = tk.Frame(self.application, bd=1, relief=tk.RAISED)
        self.barre_outils.pack(side=tk.TOP, fill=tk.X)

        for item in self.description_barre_outils:
            if item is None:
                tk.Label(self.barre_outils, text="  |  ").pack(side=tk.LEFT)
                continue

            etiquette, fonction = item

            if fonction is None:
                tk.Button(self.barre_outils, text=etiquette, state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)
                continue

            tk.Button(self.barre_outils, text=etiquette, command=fonction).pack(side=tk.LEFT, padx=2, pady=2)

    def construire_etiquette(self):
        self.etiquette = tk.Label(self.barre_outils, text="", font=("Arial", 10, "bold"))
        self.etiquette.pack(side=tk.RIGHT, padx=10)

    def modifier_etiquette(self, message: str):
        self.etiquette.config(text=message)


# (Titre de l'onglet, Graphes à afficher).
# Si la liste de graphes est vide, on affiche un onglet de texte.
# Si la liste contient deux graphes, alors on affiche un onglet double.
# Sinon, si la liste contient un unique graphe, alors on l'affiche normalement.
DescriptionBarreOnglets: TypeAlias = list[tuple[str, list[Graphe]]]


class BarreOnglets:

    def __init__(self, application: tk.Tk, description_barre_onglets: DescriptionBarreOnglets):
        self.application = application
        self.description_barre_onglets = description_barre_onglets

        self.onglets_par_nom: dict[str, Onglet] = {}
        self.toiles_par_graphe: dict[Graphe, FigureCanvasTkAgg] = {}

    def construire_barre_onglets(self):
        self.barre_onglets = ttk.Notebook(self.application)
        self.barre_onglets.pack(fill=tk.BOTH, expand=True)

        for nom_onglet, _ in self.description_barre_onglets:
            self.onglets_par_nom[nom_onglet] = Onglet()

            conteneur = ttk.Frame(self.barre_onglets)
            self.onglets_par_nom[nom_onglet].conteneur = conteneur
            self.barre_onglets.add(conteneur, text=nom_onglet)

    def construire_onglets(self):
        for nom_onglet, liste_graphes in self.description_barre_onglets:
            onglet = self.onglets_par_nom[nom_onglet]

            if len(liste_graphes) == 0:
                onglet.construire_onglet_texte()

            elif len(liste_graphes) == 1:
                onglet.construire_onglet_simple(*liste_graphes)

            elif len(liste_graphes) == 2:
                onglet.construire_onglet_double(*liste_graphes)

            elif len(liste_graphes) == 3:
                onglet.construire_onglet_triple(*liste_graphes)

            for graphe, toile in zip(liste_graphes, self.onglets_par_nom[nom_onglet].toiles):
                self.toiles_par_graphe[graphe] = toile

    def obtenir_toile(self, graphe: Graphe) -> FigureCanvasTkAgg:
        return self.toiles_par_graphe[graphe]

    def modifier_texte(self, nom_onglet: str, message: str) -> None:
        self.onglets_par_nom[nom_onglet].modifier_onglet_texte(message)


class Onglet:

    taille_marge_largeur = 10
    taille_marge_hauteur = 10

    def __init__(self):
        # Un Widget peut être, entre autres, un Frame ou un Text.

        # Un widget conteneur...
        self.conteneur: Widget = None
        # ...le widget contenu dans cet onglet...
        self.widget: Widget = None
        # ...et potentiellement la ou les deux toile/s contenue/s dans le widget.
        self.toiles: list[FigureCanvasTkAgg] = [None, None]

    def construire_onglet_texte(self):
        self.widget = tk.Text(self.conteneur, padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur)

        self.widget.pack(fill=tk.BOTH, expand=True)
        self.widget.config(state="disabled")

    def modifier_onglet_texte(self, message: str):
        self.widget.config(state="normal")
        self.widget.delete("1.0", "end")
        self.widget.insert("end", message)
        self.widget.config(state="disabled")

    def construire_onglet_simple(self, graphe: Graphe):
        self.widget = tk.Frame(self.conteneur)
        self.widget.pack(fill="both", expand=True, padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur)

        self.toiles[0] = FigureCanvasTkAgg(graphe.fig, master=self.widget)
        self.toiles[0].get_tk_widget().pack(fill="both", expand=True)

    def construire_onglet_double(self, graphe_haut: Graphe, graphe_bas: Graphe):
        self.widget = tk.Frame(self.conteneur)
        self.widget.pack(fill="both", expand=True)

        self.widget.rowconfigure(0, weight=1)
        self.widget.rowconfigure(1, weight=1)
        self.widget.columnconfigure(0, weight=1)

        cadre_haut = tk.Frame(self.widget)
        cadre_haut.grid(row=0, column=0, sticky="nsew", padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur)

        toile_haute = FigureCanvasTkAgg(graphe_haut.fig, master=cadre_haut)
        toile_haute.get_tk_widget().pack(fill="both", expand=True)

        cadre_bas = tk.Frame(self.widget)
        cadre_bas.grid(row=1, column=0, sticky="nsew", padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur)

        toile_basse = FigureCanvasTkAgg(graphe_bas.fig, master=cadre_bas)
        toile_basse.get_tk_widget().pack(fill="both", expand=True)

        self.toiles = [toile_haute, toile_basse]

    def construire_onglet_triple(self, graphe_haut: Graphe, graphe_milieu: Graphe, graphe_bas: Graphe):
        self.widget = tk.Frame(self.conteneur)
        self.widget.pack(fill="both", expand=True)

        self.widget.rowconfigure(0, weight=1)
        self.widget.rowconfigure(1, weight=1)
        self.widget.rowconfigure(2, weight=1)
        self.widget.columnconfigure(0, weight=1)

        cadre_haut = tk.Frame(self.widget)
        cadre_haut.grid(row=0, column=0, sticky="nsew", padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur)

        toile_haute = FigureCanvasTkAgg(graphe_haut.fig, master=cadre_haut)
        toile_haute.get_tk_widget().pack(fill="both", expand=True)

        cadre_milieu = tk.Frame(self.widget)
        cadre_milieu.grid(
            row=1, column=0, sticky="nsew", padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur
        )

        toile_milieu = FigureCanvasTkAgg(graphe_milieu.fig, master=cadre_milieu)
        toile_milieu.get_tk_widget().pack(fill="both", expand=True)

        cadre_bas = tk.Frame(self.widget)
        cadre_bas.grid(row=2, column=0, sticky="nsew", padx=self.taille_marge_largeur, pady=self.taille_marge_hauteur)

        toile_basse = FigureCanvasTkAgg(graphe_bas.fig, master=cadre_bas)
        toile_basse.get_tk_widget().pack(fill="both", expand=True)

        self.toiles = [toile_haute, toile_milieu, toile_basse]


# FIXME : Corriger l'affichage des graphes qui est coupé sur les bords sur Mac.
