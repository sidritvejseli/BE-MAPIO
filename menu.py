import tkinter as tk
from tkinter import ttk


def show_placeholder(parent):
    tk.Label(
        parent,
        text="Chargez un fichier CSV via Fichier → Charger un fichier",
        font=("Arial", 13),
        fg="grey",
    ).place(relx=0.5, rely=0.5, anchor="center")
