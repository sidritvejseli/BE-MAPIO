import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from graphes_2D import Heatmap


class Heatmap3d:
    

    def __init__(self, parent):
        #onglet
        self.parent = parent
        # création de l'objet Heatmap
        self.heatmap = Heatmap()

        # Frame principal qui va contenir le graphique
        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        # Création du canvas matplotlib dans Tkinter
        self.canvas = FigureCanvasTkAgg(self.heatmap.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_day(self, df, day):
        if df is None or day is None:
            return
        # On demande à la classe Heatmap de dessiner le graphique
        self.heatmap.plot_day(df, day)
        # On met à jour l'affichage dans Tkinter
        self.canvas.draw()