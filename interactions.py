import matplotlib.dates as mdates


class Interaction:

    def nombre_en_date(self, x):
        #Convertit la coordonnée X matplotlib (float) en datetime Python
        return mdates.num2date(x).replace(tzinfo=None)
        # mdates.num2date transforme un float matplotlib en datetime
        #replace pour eviter les bud , enlever une inf qui est le fuseau horaire
        


    def info_point(self, event):
        #Affiche les infos du point le plus proche quand la souris bouge
    
        # Si la souris n’est pas sur le graphe /pas de donnée / tooltip absent
        if event.inaxes != self.ax2d or event.xdata is None or self.tooltip is None:
            if self.tooltip:
                self.tooltip.set_visible(False)  # cache le tooltip
                self.canvas2d.draw_idle()        
            return

        # Convertit la position souris en datetime
        date_souris = self.nombre_en_date(event.xdata)

        # Garde uniquement les points non supprimés
        points_valides = self.donnees[self.donnees["smps_flag"] == 0]
        if points_valides.empty:
            return

        # Calcule la distance temporelle entre la souris et chaque point
        ecarts = (points_valides["datetime"] - date_souris).abs()

        # Recup index du point le plus proche
        idx = ecarts.idxmin()

        # Si le point est trop loin (> 5 minutes), on cache le tooltip
        if ecarts[idx].total_seconds() > 300:
            self.tooltip.set_visible(False)
            self.canvas2d.draw_idle()
            return

        # Récupère la ligne correspondante
        ligne = points_valides.loc[idx]

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
