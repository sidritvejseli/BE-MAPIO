import tkinter as tk
from tkinter import ttk, messagebox


# MENU
def build_menu(app):
    menubar = tk.Menu(app)

    menu_fichier = tk.Menu(menubar, tearoff=0)
    menu_fichier.add_command(label="Charger un fichier", command=app._action_charger)
    menu_fichier.add_command(label="Fermer sans sauvegarder", command=app._action_fermer)
    menu_fichier.add_separator()
    menu_fichier.add_command(label="Enregistrer sous", command=app._action_sauvegarder)
    menu_fichier.add_separator()
    menu_fichier.add_command(label="Quitter", command=app._action_quitter)
    menubar.add_cascade(label="Fichier", menu=menu_fichier)

    menu_actions = tk.Menu(menubar, tearoff=0)
    menu_actions.add_command(label="Invalider toutes les donnees", command=app._non_dispo)
    menu_actions.add_command(label="Invalider les donnees du jour", command=app._non_dispo)
    menu_actions.add_separator()
    menu_actions.add_command(label="Annuler (Ctrl+Z)", command=app._non_dispo)
    menu_actions.add_separator()
    menu_actions.add_command(label="Appliquer un facteur de correction", command=app._non_dispo)
    menubar.add_cascade(label="Actions", menu=menu_actions)

    menu_nav = tk.Menu(menubar, tearoff=0)
    menu_nav.add_command(label="Premier jour", command=app._non_dispo)
    menu_nav.add_command(label="Jour precedent", command=app.jour_precedent)
    menu_nav.add_command(label="Jour suivant", command=app.jour_suivant)
    menubar.add_cascade(label="Navigation", menu=menu_nav)

    app.configure(menu=menubar)


# TOOLBAR
def build_toolbar(app):
    toolbar = tk.Frame(app, bd=1, relief=tk.RAISED)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    tk.Button(toolbar, text="|◀ Premier", command=app.premier_jour).pack(side=tk.LEFT, padx=2, pady=2)
    tk.Button(toolbar, text="◀ Precedent", command=app.jour_precedent).pack(side=tk.LEFT, padx=2, pady=2)
    tk.Button(toolbar, text="Suivant ▶", command=app.jour_suivant).pack(side=tk.LEFT, padx=2, pady=2)
    tk.Button(toolbar, text="Dernier ▶|", command=app.dernier_jour).pack(side=tk.LEFT, padx=2, pady=2)

    tk.Label(toolbar, text="  |  ").pack(side=tk.LEFT)

    tk.Button(toolbar, text="Actualiser", state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)
    tk.Button(toolbar, text="Invalider jour", state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)
    tk.Button(toolbar, text="Annuler (Z)", state=tk.DISABLED).pack(side=tk.LEFT, padx=2, pady=2)

    # ajout par rapport facteur dans interactions
    tk.Button(toolbar, text="Facteur", command=app.demander_facteur).pack(side=tk.LEFT)
    # bouton suppression plage ajout
    tk.Button(toolbar, text="Supprimer plage", command=app.supprimer_plage).pack(side=tk.LEFT, padx=2, pady=2)

    label_jour = tk.Label(toolbar, text="Aucun fichier charge", font=("Arial", 10, "bold"))
    label_jour.pack(side=tk.RIGHT, padx=10)

    return label_jour


# TABS
def build_tabs(app):
    notebook = ttk.Notebook(app)
    notebook.pack(fill=tk.BOTH, expand=True)

    tab_particules = ttk.Frame(notebook)
    notebook.add(tab_particules, text="  Particules  ")

    tab_fonctionnement = ttk.Frame(notebook)
    notebook.add(tab_fonctionnement, text="  Fonctionnement  ")

    tab_heatmap_3d = ttk.Frame(notebook)
    notebook.add(tab_heatmap_3d, text="  Heatmap 3D  ")

    return notebook, tab_particules, tab_fonctionnement, tab_heatmap_3d


def show_placeholder(parent):
    tk.Label(
        parent,
        text="Chargez un fichier CSV via Fichier → Charger un fichier",
        font=("Arial", 13),
        fg="grey",
    ).place(relx=0.5, rely=0.5, anchor="center")
