import matplotlib.dates as mdates
import numpy as np
import pandas as pd


class Interactions:
    # fonction de calcul de distances entres les points et la souris et les points valides
    def calculer_distances(self, event, points_valides):
        x_points = mdates.date2num(points_valides.index)
        y_points = points_valides["smps_concTotal"]

        # coordonnées de la souris
        x_souris = event.xdata
        y_souris = event.ydata

        # poids pour équilibrer X et Y
        xlim = self.ax2d.get_xlim()
        ylim = self.ax2d.get_ylim()

        # Normaliser par rapport aux limites VISIBLES (pas aux données)
        echelle_x = 1 / (xlim[1] - xlim[0])
        echelle_y = 1 / (ylim[1] - ylim[0])

        distances = np.sqrt(((x_points - x_souris) * echelle_x) ** 2 + ((y_points - y_souris) * echelle_y) ** 2)

        distances = pd.Series(distances, index=points_valides.index)
        return distances

    # Affiche les infos du point le plus proche quand la souris bouge
    def afficher_informations_point(self, event):

        # Si la souris n’est pas sur le graphe alors pas de donnée et le tooltip absent
        if event.inaxes != self.ax2d or event.xdata is None or self.tooltip is None:
            if self.tooltip:
                self.tooltip.set_visible(False)  # cache le tooltip
                self.canvas2d.draw_idle()
            return

        if self.donnees.est_vide():
            return

        # Garde uniquement les points non supprimés
        if not self.date_fin:
            self.date_fin = self.date_debut + pd.Timedelta(days=1)

        points_valides = self.donnees.obtenir_donnees_valides()
        points_valides = points_valides.obtenir_dates(self.date_debut, self.date_fin)
        points_valides = points_valides.obtenir_dataframe()

        if points_valides.empty:
            return

        distances = self.calculer_distances(event, points_valides)
        idx_min = distances.idxmin()

        # Seuil adaptatif (2% de la diagonale du graphe)
        seuil = 0.02
        if distances[idx_min] > seuil:
            self.tooltip.set_visible(False)
            self.canvas2d.draw_idle()
            return

        # Récupère la ligne correspondante
        ligne = points_valides.loc[idx_min]

        # Texte affiché dans le tooltip
        self.tooltip.set_text(f"{ligne.name.strftime('%d/%m %H:%M')}\n" f"Conc : {ligne['smps_concTotal']:.1f}")

        # Position du tooltip sur le graphe
        self.tooltip.xy = (
            mdates.date2num(ligne.name),
            ligne["smps_concTotal"],
        )

        # Rend visible le tooltip
        self.tooltip.set_visible(True)
        self.canvas2d.draw_idle()

    def _au_clic(self, event):

        # clique gauche pour plage
        if event.inaxes == self.ax2d and event.button == 1 and event.xdata is not None:
            date = mdates.num2date(event.xdata).replace(tzinfo=None)

            if self.selection_debut is None:
                self.selection_debut = date

                # supp ancienne ligne si elle existe
                # Si self a une ligne_fin et qu’elle n’est pas vide  alors on la supprime
                # hasattr nous permet de vérifier si un objet possède un attribut
                if hasattr(self, "ligne_debut") and self.ligne_debut:
                    self.ligne_debut.remove()

                # dessine ligne début
                self.ligne_debut = self.ax2d.axvline(date, color="red", linestyle="--")

            else:
                self.selection_fin = date

                # supp ancienne ligne si elle existe
                if hasattr(self, "ligne_fin") and self.ligne_fin:
                    self.ligne_fin.remove()

                # met unedessine ligne fin
                self.ligne_fin = self.ax2d.axvline(date, color="red", linestyle="--")

            # rediesine
            self.canvas2d.draw_idle()
            # je met un return pour que je stop qquad je met la deuxieme ligne
            return

        # Clic droit : supprime le point le plus proche

        # Vérifie : clic sur graphe + bouton droit en gros le 3 c clique droit
        if event.inaxes != self.ax2d or event.xdata is None or event.button != 3:
            return

        # Garde points valides
        if not self.date_fin:
            self.date_fin = self.date_debut + pd.Timedelta(days=1)

        points_valides = self.donnees.obtenir_donnees_valides()
        points_valides = points_valides.obtenir_dates(self.date_debut, self.date_fin)
        points_valides = points_valides.obtenir_dataframe()

        if points_valides.empty:
            return

        # Trouve le point le plus proche
        distances = self.calculer_distances(event, points_valides)
        index_min = distances.idxmin()

        # si on depasse le seuil on ne peut plus selectionner le point
        seuil = 0.02
        if distances[index_min] > seuil:
            return

        # on supprime en mettant flag = 1
        self.donnees.invalider_date(index_min)

        # correction bug plage
        # supprime ligne début si elle existe
        if hasattr(self, "ligne_debut") and self.ligne_debut:
            self.ligne_debut.remove()
            self.ligne_debut = None

        # supprime ligne fin si elle existe
        if hasattr(self, "ligne_fin") and self.ligne_fin:
            self.ligne_fin.remove()
            self.ligne_fin = None

        # le reset pour les bug
        self.selection_debut = None
        self.selection_fin = None

        # Recharge le graphe pour voir la suppression
        self.afficher_graphe()

    def appliquer_facteur(self, facteur):
        if self.donnees.est_vide():
            return
        # multiplication des valeurs
        self.donnees.multiplier_concentration(facteur)
        self.afficher_graphe()

    def supprimer_plage(self):

        if self.selection_debut is None or self.selection_fin is None:
            print("Aucune plage")
            return

        debut = min(self.selection_debut, self.selection_fin)
        fin = max(self.selection_debut, self.selection_fin)

        self.donnees.invalider_dates(debut, fin)

        # supprimer les lignes

        if hasattr(self, "ligne_debut") and self.ligne_debut:
            self.ligne_debut.remove()
            self.ligne_debut = None

        if hasattr(self, "ligne_fin") and self.ligne_fin:
            self.ligne_fin.remove()
            self.ligne_fin = None

        # pour recommencer de nouvelle ligne on doit reset
        self.selection_debut = None
        self.selection_fin = None

        self.afficher_graphe()
