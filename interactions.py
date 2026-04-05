import matplotlib.dates as mdates
import math
import numpy as np
class Interaction:

    def calcul_distances(self, distances):
        pass

    def info_point(self, event):
        #Affiche les infos du point le plus proche quand la souris bouge

        # Si la souris n’est pas sur le graphe /pas de donnée / tooltip absent
        if event.inaxes != self.ax2d or event.xdata is None or self.tooltip is None:
            if self.tooltip:
                self.tooltip.set_visible(False)  # cache le tooltip
                self.canvas2d.draw_idle()        
            return
        

        # Garde uniquement les points non supprimés
        points_valides = self.donnees[self.donnees["smps_flag"] == 0]
        if points_valides.empty:
            return

        #coordonnées des points des graphes
        x_points = mdates.date2num(points_valides["datetime"])
        y_points = points_valides["smps_concTotal"]

        #coordonnées de la souris
        x_souris = event.xdata
        y_souris = event.ydata

        # poids pour équilibrer X et Y
        xlim = self.ax2d.get_xlim()
        ylim = self.ax2d.get_ylim()

        # Normaliser par rapport aux limites VISIBLES (pas aux données)
        echelle_x = 1 / (xlim[1] - xlim[0])
        echelle_y = 1 / (ylim[1] - ylim[0])

        distances = np.sqrt(
            ((x_points - x_souris) * echelle_x)**2 +
            ((y_points - y_souris) * echelle_y)**2
        )

        idx_min = distances.argmin()

        # Seuil adaptatif (2% de la diagonale du graphe)
        seuil = 0.02
        if distances[idx_min] > seuil:
            self.tooltip.set_visible(False)
            self.canvas2d.draw_idle()
            return

        # Récupère la ligne correspondante
        ligne = points_valides.loc[idx_min]

        # Texte affiché dans le tooltip
        self.tooltip.set_text(
            f"{ligne['datetime'].strftime('%d/%m %H:%M')}\n"
            f"Conc : {ligne['smps_concTotal']:.1f}"
        )

        # Position du tooltip sur le graphe
        self.tooltip.xy = (
            mdates.date2num(ligne["datetime"]),   
            ligne["smps_concTotal"],              
        )

        # Rend visible le tooltip
        self.tooltip.set_visible(True)
        self.canvas2d.draw_idle()
        


    def _au_clic(self, event):
        #Clic droit : supprime le point le plus proche

        # Vérifie : clic sur graphe + bouton droit en gros le 3 c clique droit
        if event.inaxes != self.ax2d or event.xdata is None or event.button != 3:
            return

        # Convertit position souris → datetime
        date_clic = self.nombre_en_date(event.xdata)

        # Garde points valides
        points_valides = self.donnees[self.donnees["smps_flag"] == 0]
        if points_valides.empty:
            return

        # Trouve le point le plus proche
        ecarts = (points_valides["datetime"] - date_clic).abs()
        idx = ecarts.idxmin()

        # Trop loin → on ne fait rien
        if ecarts[idx].total_seconds() > 300:
            return

        #on supprime en mettant flag = 1
        self.donnees.loc[idx, "smps_flag"] = 1

        # Recharge le graphe pour voir la suppression
        self.afficher_graphe()
