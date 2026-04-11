import tkinter as tk
from tkinter import ttk


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
