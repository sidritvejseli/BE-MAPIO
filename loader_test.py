import tkinter as tk
from donnees import Donnees
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.widgets import Button

# classe App pour tester le loader en affichant les données
# app.py fonctionne similairement


class App(tk.Tk, Donnees):
    def __init__(self):
        super().__init__()
        self.title("Test Loader")

        # bouton pour charger un CSV
        btn = tk.Button(self, text="Load CSV", command=self.charger_fichier_csv)
        btn.pack(pady=20)

        # initier les donner a None pour que les autres fonction n'essaye pas d'acceder a qq chose qui n'es pas chargé
        self.donnees = None
        self.donnees_original = None
        self.current_file = None
        # bouton pour afficher les données chargees
        tk.Button(self, text="afficher graphe", command=self.affichage_graphe2D).pack()

        tk.Button(self, text="Quit", command=self.destroy).pack()

    def affichage_graphe2D(self):
        if self.donnees is None:
            print("Aucune donnée chargée")
            return

        self.current_day = self.donnees["datetime"].dt.date.min()

        # Frame pour les contrôles
        control_frame = tk.Frame(self)
        control_frame.pack()

        tk.Button(control_frame, text="Jour précédent", command=self.prev_day_tk).pack(
            side=tk.LEFT
        )
        tk.Button(control_frame, text="Jour suivant", command=self.next_day_tk).pack(
            side=tk.LEFT
        )

        self.plot_day_simple()

    def plot_day_simple(self):
        df_day = self.donnees[self.donnees["datetime"].dt.date == self.current_day]

        plt.close("all")
        plt.figure()
        plt.scatter(df_day["datetime"], df_day["smps_concTotal"])
        plt.title(f"Jour : {self.current_day}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show(block=False)

    # fonctions pour modifier le jour courant
    def next_day_tk(self):
        max_day = self.donnees["datetime"].dt.date.max()
        if self.current_day < max_day:
            self.current_day += pd.Timedelta(days=1)
            self.plot_day_simple()

    def prev_day_tk(self):
        min_day = self.donnees["datetime"].dt.date.min()
        if self.current_day > min_day:
            self.current_day -= pd.Timedelta(days=1)
            self.plot_day_simple()


if __name__ == "__main__":
    app = App()
    app.mainloop()
