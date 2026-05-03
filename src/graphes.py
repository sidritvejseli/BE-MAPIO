import logging
import matplotlib.pyplot as plt
import numpy as np


import matplotlib.dates as mdates
import matplotlib.ticker as mticker


from datetime import datetime
from matplotlib.image import AxesImage
from sklearn.linear_model import LinearRegression
from scipy.stats import gaussian_kde


from donnees import Donnees


class Graphe2D:

    def __init__(self):
        self.logger = logging.getLogger()

        self.fig, self.ax = plt.subplots()

    def est_vide(self):
        return not self.ax.has_data()

    def tracer_graphe_2d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime, concentration_maximum):
        self.effacer_graphe_2d()

        donnees_dates = donnees.obtenir_dates(date_debut, date_fin)

        donnees_valides = donnees_dates.obtenir_donnees_valides()
        donnees_invalides = donnees_dates.obtenir_donnees_invalides()

        self.tracer_donnees(
            donnees_valides,
            taille=3,
            couleur="blue",
            marqueur="x",
        )

        self.tracer_donnees(
            donnees_invalides,
            taille=8,
            couleur="red",
            marqueur="x",
            legende_boite=f"Invalidés ({donnees_invalides.obtenir_nombre_dates()})",
        )

        self.legender_titre(date_debut, donnees.nom_colonne_concentration)
        self.legender_abscisses(date_debut, date_fin)
        self.legender_ordonnees(concentration_maximum)
        # self.legender_boite()

        self.tracer_grille()

        self.fig.tight_layout()

    def effacer_graphe_2d(self):
        self.ax.clear()

    def tracer_donnees(
        self, donnees: Donnees, taille: int = "1", couleur: str = "blue", marqueur: str = "x", legende_boite: str = ""
    ):
        dataframe_dates = donnees.obtenir_colonne_dates().obtenir_dataframe()
        dataframe_concentration = donnees.obtenir_colonne_concentration().obtenir_dataframe()

        self.ax.scatter(
            dataframe_dates,
            dataframe_concentration,
            s=taille,
            color=couleur,
            marker=marqueur,
            label=legende_boite,
        )

    def legender_titre(self, date: datetime, nom_colonne_concentration: str):
        self.ax.set_title(f"Jour : {date.date()}\n{nom_colonne_concentration}")

    def legender_abscisses(self, date_debut: datetime, date_fin: datetime):
        self.ax.set_xlabel("Heure")

        formatter = mdates.DateFormatter("%H:%M")

        self.ax.xaxis.set_major_formatter(formatter)

        self.ax.tick_params(axis="x")

        self.ax.set_xlim(date_debut, date_fin)

    def legender_ordonnees(self, concentration_maximum):
        self.ax.set_ylabel("Concentration totale")

        self.ax.set_ylim(0, concentration_maximum)

    def legender_boite(self):
        self.ax.legend()

    def tracer_grille(self):
        self.ax.grid(True, linestyle="--")


class Graphe3D:

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.colorbar = None

    def tracer_graphe_3d(self, donnees: Donnees, date_debut: datetime, date_fin: datetime, teneur_maximum):
        self.effacer_graphe_3d()

        donnees_dates = donnees.obtenir_dates(date_debut, date_fin)

        donnees_invalides = donnees_dates.obtenir_donnees_invalides()

        particules = donnees_dates.obtenir_particules()
        particules_invalides = donnees_invalides.obtenir_particules()

        # Remarque : Il faut d'abord récupérer la validité des données avant de filtrer par particules,
        # car filtrer par particules enlève la colonne "smps_flag" qui note la validité d'une donnée.

        # Suppression des données invalidées dans le graphe 3D.
        particules_valides = particules.soustraire_donnees(particules_invalides)
        particules_valides = particules_valides.completer_valeurs_manquantes_jour(date_debut, date_fin)

        dataframe = particules_valides.obtenir_dataframe()

        carte_thermique = self.ax.pcolormesh(
            dataframe.index,
            dataframe.columns,
            dataframe.T,
            cmap="Spectral_r",
            shading="auto",
            vmin=0,
            vmax=teneur_maximum,
        )

        particules.convertir_titre_particules_en_float()

        self.legender_titre(date_debut)
        self.legender_abscisses()
        self.legender_ordonnees()
        self.legender_barre_couleurs(carte_thermique)

        self.fig.tight_layout()

    def effacer_graphe_3d(self):
        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()

    def legender_titre(self, date: datetime):
        self.ax.set_title(f"Jour : {date.date()}")

    def legender_abscisses(self):
        self.ax.set_xlabel("Heure")

        formatter = mdates.DateFormatter("%H:%M")
        self.ax.xaxis.set_major_formatter(formatter)

        self.ax.tick_params(axis="x")

    def legender_ordonnees(self):
        self.ax.set_ylabel("Taille des particules (nanomètres)")

        self.ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=10))

        self.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

        self.ax.tick_params(axis="y")

        # FIXME : Les ordonnées ne sont pas sur une échelle linéaire.

    def legender_barre_couleurs(self, carte_thermique: AxesImage):

        self.colorbar = self.ax.figure.colorbar(carte_thermique, ax=self.ax)
        self.colorbar.set_label("Teneur")


class GrapheCorrelation:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.pente = None

    def est_vide(self):
        return not self.ax.has_data()

    def effacer_graphe_correlation(self):
        self.ax.clear()
        self.pente = None

    def legender_titre(self):
        self.ax.set_title(f"SMPS vs CPC (Pente: {self.pente:.2f})")

    def legender_abscisses(self, concentration_maximum_smps):
        self.ax.set_ylabel("Concentration total SMPS (smps_concTotal)")

        self.ax.set_xlim(0, 1.05 * concentration_maximum_smps)

    def legender_ordonnees(self, concentration_maximum_cpc):
        self.ax.set_xlabel("ConcentrationCPC (cpc_conc)")

        self.ax.set_ylim(0, 1.05 * concentration_maximum_cpc)

    def legender_boite(self):
        self.ax.legend(fontsize=8)

    def tracer_grille(self):
        self.ax.grid(True, linestyle="--", alpha=0.5)

    def tracer_graphe_correlation(self, donnees: Donnees, concentrations_maximum: dict[str, float]):
        self.effacer_graphe_correlation()

        self.tracer_donnees(donnees)

        concentration_maximum_smps = concentrations_maximum[donnees.noms_colonnes_concentrations[0]]
        self.legender_abscisses(concentration_maximum_smps)

        concentration_maximum_cpc = concentrations_maximum[donnees.noms_colonnes_concentrations[1]]
        self.legender_ordonnees(concentration_maximum_cpc)

        self.tracer_grille()
        self.legender_titre()

    def tracer_donnees(
        self,
        donnees: Donnees,
        taille: int = 0.5,
        marqueur: str = "o",
        legende_boite: str = "",
    ):
        df_colonnes = donnees.obtenir_donnees_valides().obtenir_colonnes_concentrations()

        smps_total = df_colonnes.obtenir_dataframe().iloc[:, 0]
        cpc_conc = df_colonnes.obtenir_dataframe().iloc[:, 1]

        xy = np.vstack([cpc_conc, smps_total])

        # couleurs qui changent avec si la densité de points est elevée
        z = gaussian_kde(xy)(xy)
        # FIXME : Si le graphe contient un unique point valide, la corrélation imprime une erreur.

        self.ax.scatter(
            smps_total,
            cpc_conc,
            s=taille,
            c=z,
            marker=marqueur,
            label=legende_boite,
        )

        self.tracer_regression(smps_total, cpc_conc)

    # FIXME verfier quel paramettre est l'abscisse et quel est l'ordonnee
    def tracer_regression(self, x, y):
        x_data = x.values.reshape(-1, 1)
        y_data = y.values
        model = LinearRegression(fit_intercept=False)

        model.fit(x_data, y_data)

        self.pente = model.coef_[0]
        y_max = y_data.max()
        yy = [0, y_max]

        self.ax.plot(yy / self.pente, yy, color="dimgrey", linewidth=1.5)
