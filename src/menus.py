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


DescriptionBarreOutils: TypeAlias = list[tuple[str, Callable]]
# (Titre de l'outil, Fonction appelée).


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
        self.etiquette = tk.Label(self.barre_outils, text="Aucun fichier chargé.", font=("Arial", 10, "bold"))
        self.etiquette.pack(side=tk.RIGHT, padx=10)

    def modifier_etiquette(self, message: str):
        self.etiquette.config(text=message)


DescriptionBarreOnglets: TypeAlias = list[tuple[str, list[Graphe]]]


class BarreOnglets:

    def __init__(self, application: tk.Tk, description_barre_onglets: DescriptionBarreOnglets):
        self.application = application
        self.description_barre_onglets = description_barre_onglets

        self.onglets: dict[str, Onglet] = {}

    def construire_barre_onglets(self):
        self.barre_onglets = ttk.Notebook(self.application)
        self.barre_onglets.pack(fill=tk.BOTH, expand=True)

        for nom_onglet, _ in self.description_barre_onglets:
            self.onglets[nom_onglet] = Onglet()

            conteneur = ttk.Frame(self.barre_onglets)
            self.definir_conteneur(nom_onglet, conteneur)
            self.barre_onglets.add(conteneur, text=nom_onglet)

    def construire_onglets(self):
        for nom_onglet, liste_graphes in self.description_barre_onglets:
            onglet = self.onglets[nom_onglet]

            if len(liste_graphes) == 0:
                onglet.construire_onglet_texte()

            elif len(liste_graphes) == 1:
                onglet.construire_onglet_simple(*liste_graphes)

            elif len(liste_graphes) == 2:
                onglet.construire_onglet_double(*liste_graphes)

    def obtenir_conteneur(self, nom_onglet: str):
        return self.onglets[nom_onglet].conteneur

    def definir_conteneur(self, nom_onglet: str, onglet: Frame):
        self.onglets[nom_onglet].conteneur = onglet

    def obtenir_widget(self, nom_onglet: str):
        return self.onglets[nom_onglet].widget

    def definir_widget(self, nom_onglet: str, widget: Widget):
        self.onglets[nom_onglet].widget = widget

    def obtenir_toile(self, nom_onglet: str, numero_toile: int = 0):
        return self.onglets[nom_onglet].toiles[numero_toile]

    def definir_toile(self, nom_onglet: str, liste_toiles: list[FigureCanvasTkAgg]):
        self.onglets[nom_onglet].toiles = liste_toiles

    def definir_texte(self, nom_onglet: str, message: str):
        self.onglets[nom_onglet].modifier_onglet_texte(message)


# FIXME : Corriger l'affichage des graphes qui est coupé sur les bords sur Mac.


class Onglet:

    def __init__(self):
        # Un Widget peut être, entre autres, un Frame ou un Text.

        # Un widget conteneur...
        self.conteneur: Widget = None
        # ...le widget contenu dans cet onglet...
        self.widget: Widget = None
        # ...et potentiellement la ou les deux toile/s contenue/s dans le widget.
        self.toiles: list[FigureCanvasTkAgg] = [None, None]

    def construire_onglet_texte(self):
        self.widget = tk.Text(self.conteneur)

        self.widget.pack(fill=tk.BOTH, expand=True)
        self.widget.config(state="disabled")

    def modifier_onglet_texte(self, message: str):
        self.widget.config(state="normal")
        self.widget.delete("1.0", "end")
        self.widget.insert("end", message)
        self.widget.config(state="disabled")

    def construire_onglet_simple(self, graphe: Graphe):
        self.widget = tk.Frame(self.conteneur)
        self.widget.pack(fill="both", expand=True)

        self.toiles[0] = FigureCanvasTkAgg(graphe.fig, master=self.widget)
        self.toiles[0].get_tk_widget().pack(fill="both", expand=True)

    def construire_onglet_double(self, graphe_haut: Graphe, graphe_bas: Graphe):
        self.widget = tk.Frame(self.conteneur)
        self.widget.pack(fill="both", expand=True)

        self.widget.rowconfigure(0, weight=1)
        self.widget.rowconfigure(1, weight=1)
        self.widget.columnconfigure(0, weight=1)

        cadre_haut = tk.Frame(self.widget)
        cadre_haut.grid(row=0, column=0, sticky="nsew")

        toile_haute = FigureCanvasTkAgg(graphe_haut.fig, master=cadre_haut)
        toile_haute.get_tk_widget().pack(fill="both", expand=True)

        cadre_bas = tk.Frame(self.widget)
        cadre_bas.grid(row=1, column=0, sticky="nsew")

        toile_basse = FigureCanvasTkAgg(graphe_bas.fig, master=cadre_bas)
        toile_basse.get_tk_widget().pack(fill="both", expand=True)

        self.toiles = [toile_haute, toile_basse]
