import copy
import logging
import os
import pandas as pd
import tkinter as tk
import yaml


from datetime import datetime
from matplotlib.backend_bases import Event
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.text import Annotation
from tkinter import filedialog, Label, Menu, messagebox, ttk
from tkinter.simpledialog import askfloat
from tkinter.ttk import Notebook
from typing import Callable, TypeAlias


from donnees import Donnees
from graphes import Graphe2D, Graphe3D
from interactions import Interactions


ItemsMenu: TypeAlias = list[tuple[str, str, Callable]]
# (Titre de l'item, Raccourci, Fonction appelée). Pour un séparateur, on met None.

BarreMenus: TypeAlias = list[tuple[str, ItemsMenu]]
# (Nom du menu déroulant, Description du menu déroulant).

BarreOutils: TypeAlias = list[tuple[str, Callable]]
# (Titre de l'outil, Fonction appelée).

Onglets: TypeAlias = dict[str, ttk.Frame]
# (Nom de l'onglet -> Onglet).


class Interface(tk.Tk):

    def __init__(self):

        super().__init__()

        self.logger = logging.getLogger()

        self.description_barre_menus: BarreMenus = [
            (
                "Fichier",
                [
                    ("Charger un fichier", None, self.charger_fichier),
                    ("Fermer sans enregistrer", None, self.fermer_fichier),
                    None,
                    ("Enregistrer sous", None, self.sauvegarder_fichier),
                    None,
                    ("Quitter", None, self.quitter_programme),
                ],
            ),
            (
                "Actions",
                [
                    ("Invalider toutes les données", None, self.afficher_indisponible),
                    ("Invalider les données du jour", None, self.afficher_indisponible),
                    None,
                    ("Annuler", "Ctrl+Z", self.afficher_indisponible),
                    None,
                    ("Appliquer un facteur de correction", None, self.afficher_indisponible),
                ],
            ),
            (
                "Navigation",
                [
                    ("Sauter au premier jour", None, self.sauter_au_premier_jour),
                    ("Sauter au dernier jour", None, self.sauter_au_dernier_jour),
                    None,
                    ("Sauter au jour précédent", None, self.sauter_au_jour_precedent),
                    ("Sauter au jour suivant", None, self.sauter_au_jour_suivant),
                ],
            ),
        ]

        self.description_barre_outils: BarreOutils = [
            ("|◀ Premier", self.sauter_au_premier_jour),
            ("◀ Précédent", self.sauter_au_jour_precedent),
            ("Suivant ▶", self.sauter_au_jour_suivant),
            ("Dernier ▶|", self.sauter_au_dernier_jour),
            None,
            ("Actualiser", None),
            ("Invalider jour", None),
            ("Annuler", None),
            ("Facteur", self.demander_facteur),
            ("Supprimer plage", self.supprimer_plage),
        ]

        self.description_barre_onglets: list[str] = ["Particules", "Fonctionnement", "Graphe 3D"]

        # Configuration.
        self.config = self.charger_configuration("config.yaml")

        # Données.
        self.donnees = Donnees()
        self.donnees_sans_modification = Donnees()
        self.fichier_courant = None
        self.date_debut: datetime = None
        self.date_fin: datetime = None

        # Interactions.
        self.interactions = Interactions()
        self.infobulle: Annotation = None

        # Fenêtre.
        configuration_affichage = self.config.get("affichage", {})
        self.title(configuration_affichage.get("titre", "Outil SMPS - MAP-IO"))
        largeur = configuration_affichage.get("largeur", 1400)
        hauteur = configuration_affichage.get("hauteur", 800)
        self.geometry(f"{largeur}x{hauteur}")
        self.resizable(True, True)

        # Graphes.
        self.graphe_2d: Graphe2D = Graphe2D()
        self.graphe_3d: Graphe3D = Graphe3D()

        # Construction initiale.
        self.construire_barre_menus()

        self.barre_outils_etiquette_jour: Label = None
        self.construire_barre_outils()

        self.barre_onglets: Notebook = None
        self.onglets: Onglets = {}
        self.construire_barre_onglets()

        self.construire_onglet_particules()
        self.afficher_onglet_provisoire(self.onglets["Fonctionnement"])
        self.construire_onglet_graphe_3d()

    def afficher_infobulle_apres_survol_souris(self, evenement: Event):
        doit_rafraichir = self.interactions.afficher_infobulle_apres_survol_souris(
            evenement,
            self.donnees,
            self.ax_2d,
            self.date_debut,
            self.date_fin,
            self.infobulle,
        )

        if doit_rafraichir:
            self.zone_affichage_graphe_2d.draw_idle()

    def repondre_apres_clic_souris(self, evenement: Event):
        type_clic = self.interactions.repondre_apres_clic_souris(
            evenement,
            self.donnees,
            self.ax_2d,
            self.date_debut,
            self.date_fin,
        )

        if type_clic == 1:
            self.zone_affichage_graphe_2d.draw_idle()

        elif type_clic == 3:
            self.afficher_graphe()

    def supprimer_plage(self):
        self.interactions.supprimer_plage(self.donnees)
        self.afficher_graphe()

    def construire_onglet_particules(self):
        self.page_principale = tk.Frame(self.onglets["Particules"])
        self.page_principale.pack(fill="both", expand=True)

        self.page_principale.rowconfigure(0, weight=1, minsize=300)
        self.page_principale.rowconfigure(1, weight=1, minsize=300)
        self.page_principale.columnconfigure(0, weight=1)

        self.cadre_graphe_2d = tk.Frame(self.page_principale)
        self.cadre_graphe_2d.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.zone_affichage_graphe_2d = FigureCanvasTkAgg(self.graphe_2d.fig, master=self.cadre_graphe_2d)
        self.zone_affichage_graphe_2d.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        self.ax_2d = self.graphe_2d.ax

        self.zone_affichage_graphe_2d.mpl_connect("button_press_event", self.repondre_apres_clic_souris)
        self.zone_affichage_graphe_2d.mpl_connect("motion_notify_event", self.afficher_infobulle_apres_survol_souris)

        self.cadre_graphe_3d = tk.Frame(self.page_principale)
        self.cadre_graphe_3d.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.zone_affichage_graphe_3d = FigureCanvasTkAgg(self.graphe_3d.fig, master=self.cadre_graphe_3d)
        self.zone_affichage_graphe_3d.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        # FIXME : Corriger l'affichage des graphes qui est coupé sur les bords sur Mac.

    def construire_onglet_graphe_3d(self):
        # Frame principal qui va contenir le graphique
        self.frame_3d_individuel = tk.Frame(self.onglets["Graphe 3D"])
        self.frame_3d_individuel.pack(fill="both", expand=True)

        # Création du canvas matplotlib dans Tkinter
        self.canvas_3d_individuel = FigureCanvasTkAgg(self.graphe_3d.fig, master=self.frame_3d_individuel)
        self.canvas_3d_individuel.get_tk_widget().pack(fill="both", expand=True)

    def charger_configuration(self, chemin):
        if os.path.exists(chemin):
            with open(chemin, "r", encoding="utf-8") as fichier:
                return yaml.safe_load(fichier) or {}

        self.logger.warning(f"Fichier de configuration {chemin} introuvable.")
        return {}

    def afficher_indisponible(self):
        messagebox.showinfo("Info", "Fonctionnalité pas encore disponible.")

    def afficher_jour_barre_outils(self):
        if self.donnees.est_vide() or self.date_debut is None:
            return

        self.barre_outils_etiquette_jour.config(text=f"Jour affiché : {self.date_debut.strftime("%Y-%m-%d")}")

    def afficher_aucun_fichier_charge_barre_outils(self):
        if self.donnees.est_vide() or self.date_debut is None:
            return

        self.barre_outils_etiquette_jour.config(text="Aucun fichier chargé.")

    def charger_fichier(self):
        chemin_relatif_initial = self.config.get("repertoires", {}).get("donnees", "")

        # FIXME : Le chemin initial est relatif, bug potentiel si le répertoire de données inscrit dans le fichier config.yaml n'est pas dans le même dossier que le programme.

        chemin_absolu_chargement = filedialog.askopenfilename(
            initialdir=chemin_relatif_initial,
            filetypes=[("CSV files", "*.csv"), ("All", "*.*")],
        )

        if not chemin_absolu_chargement:
            return

        self.donnees.charger_fichier_csv(chemin_absolu_chargement)

        if not self.donnees.est_vide():
            self.date_debut = self.donnees.obtenir_premiere_date()
            self.date_fin = self.ajouter_23_heures_59_minutes_et_59_secondes(self.date_debut)
            self.afficher_graphe()
            self.afficher_jour_barre_outils()

        self.donnees_sans_modification = copy.deepcopy(self.donnees)
        # FIXME : Vérifier de la nécessité de la variable donnees_sans_modification.

    def fermer_fichier(self):
        if self.donnees.est_vide():
            return

        if messagebox.askyesno("Confirmer", "Fermer sans enregistrer ?"):
            self.donnees.fermer_fichier_csv()
            self.date_debut = None
            self.date_fin = None
            self.afficher_aucun_fichier_charge_barre_outils()

    def sauvegarder_fichier(self):
        repertoires_configuration = self.config.get("repertoires", {})
        dossier_resultats = repertoires_configuration.get("resultats", "resultats/")
        dossier_flags = repertoires_configuration.get("flags", "resultats/flags/")

        if self.donnees.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        # on cree les dossiers s'ils n'existent pas
        os.makedirs(dossier_resultats, exist_ok=True)
        os.makedirs(dossier_flags, exist_ok=True)

        # sauvegarde du fichier filtre (lignes valides uniquement)
        chemin_absolu_donnees_filtrees = filedialog.asksaveasfilename(
            title="Sauvegarder les données filtrées",
            initialdir=dossier_resultats,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        # sauvegarde du fichier des flags (lignes invalidees)
        chemin_absolu_flags = filedialog.asksaveasfilename(
            title="Sauvegarder le fichier des flags",
            initialdir=dossier_flags,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not chemin_absolu_donnees_filtrees or not chemin_absolu_flags:
            return

        self.donnees.sauvegarder_fichier_csv(chemin_absolu_donnees_filtrees, chemin_absolu_flags)

    def quitter_programme(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.destroy()

    def afficher_graphe(self):
        if self.donnees.est_vide() or self.date_debut is None or self.date_fin is None:
            return

        self.date_fin = self.ajouter_23_heures_59_minutes_et_59_secondes(self.date_debut)

        self.graphe_2d.tracer_graphe_2d(self.donnees, self.date_debut, self.date_fin)
        self.interactions.tracer_lignes(self.ax_2d, self.date_debut, self.date_fin)

        self.zone_affichage_graphe_2d.draw()

        # Initialisation de l'infobulle.
        # FIXME : Vérifier si l'initialisation de l'infobulle se fait au bon endroit.
        self.infobulle: Annotation = self.ax_2d.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="orange", alpha=0.9),
            visible=False,
        )

        self.graphe_3d.tracer_graphe_3d(self.donnees, self.date_debut, self.date_fin)
        self.zone_affichage_graphe_3d.draw()

        self.canvas_3d_individuel.draw()

        self.afficher_jour_barre_outils()

    def ajouter_24_heures(self, jour: datetime):
        return jour + pd.Timedelta(days=1)

    def soustraire_24_heures(self, jour: datetime):
        return jour - pd.Timedelta(days=1)

    def ajouter_23_heures_59_minutes_et_59_secondes(self, jour: datetime):
        return jour + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    def sauter_au_jour_suivant(self):
        if self.donnees.est_vide() or self.date_debut >= self.donnees.obtenir_derniere_date():
            return

        self.date_debut = self.ajouter_24_heures(self.date_debut)
        self.afficher_graphe()

    def sauter_au_jour_precedent(self):
        if self.donnees.est_vide() or self.date_debut <= self.donnees.obtenir_premiere_date():
            return

        self.date_debut = self.soustraire_24_heures(self.date_debut)
        self.afficher_graphe()

    def sauter_au_premier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_premiere_date()
        self.afficher_graphe()

    def sauter_au_dernier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_derniere_date()
        self.afficher_graphe()

    # demande du facteur
    def demander_facteur(self):
        facteur = askfloat("Facteur", "Multiplier par :")

        if facteur is None or self.donnees.est_vide():
            return

        self.donnees.multiplier_concentration(facteur)
        self.afficher_graphe()

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
            barre_outils, text="Aucun fichier chargé.", font=("Arial", 10, "bold")
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
