import logging
from matplotlib.colors import LogNorm, Normalize
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import matplotlib.dates as mdates
import matplotlib.ticker as mticker


from datetime import datetime, timedelta
from matplotlib.image import AxesImage
from sklearn.linear_model import LinearRegression
from scipy.stats import gaussian_kde


from donnees import Donnees


class Graphe:

    marge_relative = 0.05


class Graphe2D(Graphe):

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

        self.legender_titre(date_debut, donnees.nom_colonne_concentration_courante)
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

        duree = date_fin - date_debut
        marge = duree * self.marge_relative

        self.ax.set_xlim(date_debut - marge, date_fin + marge)

    def legender_ordonnees(self, concentration_maximum):
        self.ax.set_ylabel("Concentration totale")

        self.ax.set_ylim(0, (1 + self.marge_relative) * concentration_maximum)

    def legender_boite(self):
        self.ax.legend()

    def tracer_grille(self):
        self.ax.grid(True, linestyle="--")


class Graphe3D(Graphe):

    def __init__(
        self,
        echelle_logarithmique: bool = False,
    ):
        self.fig, self.ax = plt.subplots()
        self.colorbar = None

        self.echelle_logarithmique: bool = echelle_logarithmique

    def tracer_graphe_3d(
        self,
        donnees: Donnees,
        date_debut: datetime,
        date_fin: datetime,
        teneur_maximum,
    ):
        self.effacer_graphe_3d()

        donnees_dates = donnees.obtenir_dates(date_debut, date_fin)

        donnees_invalides = donnees_dates.obtenir_donnees_invalides()

        particules = donnees_dates.obtenir_particules()
        particules_invalides = donnees_invalides.obtenir_particules()

        # Remarque : Il faut d'abord récupérer la validité des données avant de filtrer par particules,
        # car filtrer par particules enlève la colonne "smps_flag" qui note la validité d'une donnée.

        # Suppression des données invalidées dans le graphe 3D.
        particules_valides = particules.soustraire_donnees(particules_invalides)
        particules_valides = particules_valides.completer_valeurs_manquantes_jour(
            date_debut, date_fin + timedelta(seconds=1)
        )

        particules_valides_taille_particules_converties_float = particules_valides.convertir_titre_particules_en_float()

        dataframe = particules_valides_taille_particules_converties_float.obtenir_dataframe()

        self.ax.set_yscale("log")

        if self.echelle_logarithmique:
            norme = LogNorm(vmin=1, vmax=teneur_maximum)
        else:
            norme = Normalize(vmin=0, vmax=teneur_maximum)

        carte_thermique = self.ax.pcolormesh(
            dataframe.index,
            dataframe.columns,
            dataframe.iloc[:-1, 1:].T,
            cmap="Spectral_r",
            shading="flat",
            norm=norme,
        )

        self.legender_titre(date_debut, donnees.nom_drapeau_prefixe_particules)
        self.legender_abscisses()
        self.legender_ordonnees()
        self.legender_barre_couleurs(carte_thermique)

        self.fig.tight_layout()

    def effacer_graphe_3d(self):
        if self.colorbar is not None:
            self.colorbar.remove()
            self.colorbar = None

        self.ax.clear()

    def legender_titre(self, date: datetime, nom: str):
        self.ax.set_title(f"Jour : {date.date()}\n{nom}")

    def legender_abscisses(self):
        self.ax.set_xlabel("Heure")

        formatter = mdates.DateFormatter("%H:%M")
        self.ax.xaxis.set_major_formatter(formatter)

        self.ax.tick_params(axis="x")

    def legender_ordonnees(self):
        self.ax.set_ylabel("Taille des particules (µm)")

        self.ax.yaxis.set_major_locator(mticker.LogLocator(base=10))
        self.ax.yaxis.set_major_formatter(mticker.LogFormatter())

        self.ax.tick_params(axis="y")

        # FIXME : Les ordonnées ne sont pas sur une échelle linéaire.

    def legender_barre_couleurs(self, carte_thermique: AxesImage):

        self.colorbar = self.ax.figure.colorbar(carte_thermique, ax=self.ax)
        self.colorbar.set_label("Teneur")


class GrapheCorrelation(Graphe):
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

        self.ax.set_xlim(0, (1 + self.marge_relative) * concentration_maximum_smps)

    def legender_ordonnees(self, concentration_maximum_cpc):
        self.ax.set_xlabel("ConcentrationCPC (cpc_conc)")

        self.ax.set_ylim(0, (1 + self.marge_relative) * concentration_maximum_cpc)

    def legender_boite(self):
        self.ax.legend(fontsize=8)

    def tracer_grille(self):
        self.ax.grid(True, linestyle="--", alpha=0.5)

    def tracer_graphe_correlation(self, donnees: Donnees, concentrations_maximum: dict[str, float]):
        self.effacer_graphe_correlation()

        self.tracer_donnees(donnees)

        concentration_maximum_smps = concentrations_maximum[donnees.nom_colonne_smps]
        self.legender_abscisses(concentration_maximum_smps)

        concentration_maximum_cpc = concentrations_maximum[donnees.nom_colonne_cpc]
        self.legender_ordonnees(concentration_maximum_cpc)

        self.tracer_grille()
        self.legender_titre()

        self.fig.tight_layout()

    def tracer_donnees(
        self,
        donnees: Donnees,
        taille: int = 0.5,
        marqueur: str = "o",
        legende_boite: str = "",
    ):
        df_colonnes = donnees.obtenir_donnees_valides().obtenir_colonnes_concentrations_non_nulles()

        # FIXME : Utiliser le nom déclaré dans la config plutôt que l'indice de colonne.
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
