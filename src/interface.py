import copy
import logging
import os
import pandas as pd
import tkinter as tk


from datetime import datetime
from matplotlib.backend_bases import Event
from matplotlib.text import Annotation
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askfloat


from donnees import Donnees
from graphes import Graphe2D, Graphe3D, GrapheCorrelation
from interactions import Interactions
from configuration import ConfigurationUtilisateur, ConfigurationProgramme
from menus import (
    DescriptionBarreMenus,
    DescriptionBarreOutils,
    DescriptionBarreOnglets,
    BarreMenus,
    BarreOutils,
    BarreOnglets,
)
from temps import Temps


class Interface:

    def __init__(self):
        self.logger = logging.getLogger()

        self.application = tk.Tk()

        # Importation de la configuration.

        self.configuration_utilisateur: ConfigurationUtilisateur = ConfigurationUtilisateur(
            "configuration_utilisateur.yaml"
        )
        self.configuration_programme: ConfigurationProgramme = ConfigurationProgramme("configuration_programme.yaml")

        # Gestion de la temporalité.

        self.temps = Temps(self.configuration_programme.pas_heures)

        # Données.
        self.donnees = Donnees(self.configuration_utilisateur.drapeau_smps, self.configuration_utilisateur.drapeau_cpc)
        self.donnees_sans_modification = Donnees(
            self.configuration_utilisateur.drapeau_smps, self.configuration_utilisateur.drapeau_cpc
        )
        self.fichier_courant = None
        self.date_debut: datetime = None
        self.date_fin: datetime = None

        # Interactions.
        self.interactions = Interactions()
        self.infobulle: Annotation = None

        # Graphes.
        self.graphe_2d: Graphe2D = Graphe2D()
        self.xlim_original = None
        self.ylim_original = None

        self.graphe_3d: Graphe3D = Graphe3D()

        self.graphe_correlation: GrapheCorrelation = GrapheCorrelation()

        self.teneur_maximum = None  # Remarque : Pour garder une échelle constante de couleur du graphe 3D, on garde en mémoire la valeur maximum.
        self.concentrations_maximum: dict[str, float] = {
            self.configuration_utilisateur.drapeau_smps: None,
            self.configuration_utilisateur.drapeau_cpc: None,
        }

        # Construction de l'application.

        self.application.title(self.configuration_programme.titre_fenetre)
        self.application.geometry(
            f"{self.configuration_programme.largeur_fenetre}x{self.configuration_programme.hauteur_fenetre}"
        )
        self.application.resizable(True, True)

        self.description_barre_menus: DescriptionBarreMenus = [
            (
                "Fichier",
                [
                    ("Charger un fichier", None, self.charger_fichier),
                    ("Fermer sans enregistrer", None, self.fermer_fichier),
                    None,
                    ("Enregistrer sous", None, self.sauvegarder_fichier),
                    None,
                    ("Quitter", None, self.quitter_programme),
                ],
            ),
            (
                "Actions",
                [
                    ("Invalider toutes les données", None, None),
                    ("Invalider les données du jour", None, None),
                    None,
                    ("Annuler", "Ctrl+Z", self.annuler),
                    ("Rétablir", "Ctrl+Shift+Z", self.retablir),
                    None,
                    ("Appliquer un facteur de correction", None, None),
                ],
            ),
            (
                "Navigation",
                [
                    ("Sauter au premier jour", None, self.sauter_au_premier_jour),
                    ("Sauter au dernier jour", None, self.sauter_au_dernier_jour),
                    None,
                    ("Sauter au jour précédent", None, self.sauter_au_jour_precedent),
                    ("Sauter au jour suivant", None, self.sauter_au_jour_suivant),
                ],
            ),
        ]

        self.barre_menus = BarreMenus(self.application, self.description_barre_menus)
        self.barre_menus.construire_barre_menus()

        self.description_barre_outils_jour: DescriptionBarreOutils = [
            ("|◀ Premier", self.sauter_au_premier_jour),
            ("◀ Précédent", self.sauter_au_jour_precedent),
            ("Suivant ▶", self.sauter_au_jour_suivant),
            ("Dernier ▶|", self.sauter_au_dernier_jour),
            None,
            ("smps↔cpc", self.changer_colonne_concentration),
            None,
            ("Zoomer", self.zoomer),
            ("Dezoomer", self.dezoomer),
        ]

        self.barre_outils_jour = BarreOutils(self.application, self.description_barre_outils_jour)
        self.barre_outils_jour.construire_barre_outils()
        self.barre_outils_jour.construire_etiquette()

        self.description_barre_outils_validation: DescriptionBarreOutils = [
            ("Sélectionner plage", self.activer_selection_rectangle),
            ("Supprimer plage", self.supprimer_plage),
            None,
            ("Annuler", self.annuler),
            ("Rétablir", self.retablir),
            None,
            ("Facteur", self.demander_facteur),
        ]

        self.barre_outils_validation = BarreOutils(self.application, self.description_barre_outils_validation)
        self.barre_outils_validation.construire_barre_outils()
        self.barre_outils_validation.construire_etiquette()

        self.description_barre_onglets: DescriptionBarreOnglets = [
            ("Particules", [self.graphe_2d, self.graphe_correlation]),
            ("Graphe 3D", [self.graphe_3d]),
            ("Corrélation", [self.graphe_correlation]),
            ("Historique", []),
        ]

        self.barre_onglets: BarreOnglets = BarreOnglets(self.application, self.description_barre_onglets)
        self.barre_onglets.construire_barre_onglets()
        self.barre_onglets.construire_onglets()

        self.interactions.initialiser_rectangle_selector(self.graphe_2d.ax)
        self.barre_onglets.obtenir_toile("Particules", 0).mpl_connect(
            "button_press_event", self.repondre_apres_clic_souris
        )
        self.barre_onglets.obtenir_toile("Particules", 0).mpl_connect("motion_notify_event", self.info_point)

        self.mettre_a_jour_historique()

        # Remarque : Le lien entre le raccorci clavier et sa fonction appelée par Tkinter est sensible à la casse de la touche.
        self.description_raccourcis_clavier = [
            ("<Control-z>", lambda evenement: self.annuler()),
            ("<Control-Z>", lambda evenement: self.annuler()),
            ("<Control-Shift-z>", lambda evenement: self.retablir()),
            ("<Control-Shift-Z>", lambda evenement: self.retablir()),
        ]

        self.construire_raccourcis_clavier()

    def mettre_a_jour_historique(self):
        historique = "Historique des modifications\n\n"
        historique += self.donnees.historique.obtenir_journal()
        self.barre_onglets.definir_texte("Historique", historique)

    def info_point(self, evenement: Event):
        # quand rectangle actif , priorite
        if self.interactions.rectangle_selector is not None and self.interactions.rectangle_selector.active:
            return

        doit_rafraichir = self.interactions.info_point(
            evenement,
            self.donnees,
            self.graphe_2d.ax,
            self.date_debut,
            self.date_fin,
            self.infobulle,
        )

        if doit_rafraichir:
            self.barre_onglets.obtenir_toile("Particules", 0).draw_idle()

    def repondre_apres_clic_souris(self, evenement: Event):
        if self.interactions.rectangle_selector is not None and self.interactions.rectangle_selector.active:
            return

        doit_rafraichir = self.interactions.repondre_apres_clic_souris(
            evenement,
            self.donnees,
            self.graphe_2d.ax,
            self.date_debut,
            self.date_fin,
        )

        if doit_rafraichir:
            self.tracer_graphe_2d()
            self.tracer_graphe_3d()
            self.tracer_graphe_correlation()
            self.mettre_a_jour_historique()

    def annuler(self):
        self.donnees.annuler_invalidation_date()
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()
        self.tracer_graphe_correlation()
        self.mettre_a_jour_historique()

    def retablir(self):
        self.donnees.retablir_invalidation_date()
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()
        self.tracer_graphe_correlation()
        self.mettre_a_jour_historique()

    def activer_selection_rectangle(self):

        if self.donnees.est_vide():
            messagebox.showwarning("Attention !!!", "Aucune donnée chargée")
            return

        self.interactions.activer_mode_rectangle()
        self.barre_outils_validation.modifier_etiquette(
            "Dessinez un rectangle sur le graphe, puis cliquez sur 'Supprimer plage'."
        )

    def supprimer_plage(self):
        if not self.interactions.rectangle_actif:
            messagebox.showinfo(
                "Info",
                "Aucun rectangle sélectionné.\n Cliquez d'abord sur 'Sélectionner plage' et dessinez un rectangle sur le graphe. ",
            )
            return

        rafraichir = self.interactions.supprimer_plage_rectangle(self.donnees)

        if rafraichir:
            self.tracer_graphe_2d()
            self.tracer_graphe_3d()
            self.tracer_graphe_correlation()
            self.mettre_a_jour_historique()

    # affichage

    def afficher_jour_barre_outils(self):
        if self.donnees.est_vide() or self.date_debut is None:
            return

        self.barre_outils_jour.modifier_etiquette(f"Jour affiché : {self.date_debut.strftime("%Y-%m-%d")}")

    def afficher_aucun_fichier_charge_barre_outils(self):
        if self.donnees.est_vide() or self.date_debut is None:
            return

        self.barre_outils_jour.modifier_etiquette(text="Aucun fichier chargé.")

    def charger_fichier(self):
        chemin_relatif_initial = self.configuration_utilisateur.chemin_donnees

        # FIXME : Le chemin initial est relatif, bug potentiel si le répertoire de données inscrit dans le fichier config.yaml n'est pas dans le même dossier que le programme.

        chemin_absolu_chargement = filedialog.askopenfilename(
            initialdir=chemin_relatif_initial,
            filetypes=[("CSV files", "*.csv"), ("All", "*.*")],
        )

        if not chemin_absolu_chargement:
            return

        self.donnees.charger_fichier_csv(chemin_absolu_chargement)

        self.teneur_maximum = self.donnees.obtenir_particules().obtenir_valeur_maximum()

        self.concentrations_maximum[self.configuration_utilisateur.drapeau_smps] = (
            self.donnees.obtenir_colonne_concentration().obtenir_valeur_maximum()
        )

        self.donnees.echanger_nom_colonne_concentration()
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_cpc] = (
            self.donnees.obtenir_colonne_concentration().obtenir_valeur_maximum()
        )

        self.donnees.echanger_nom_colonne_concentration()

        if not self.donnees.est_vide():
            self.date_debut = self.donnees.obtenir_minuit_premiere_date()
            self.date_fin = self.temps.ajouter_23_heures_59_minutes_et_59_secondes(self.date_debut)
            self.tracer_graphe_2d()
            self.tracer_graphe_3d()
            self.tracer_graphe_correlation()
            self.afficher_jour_barre_outils()

        self.donnees_sans_modification = copy.deepcopy(self.donnees)

        # FIXME : Vérifier de la nécessité de la variable donnees_sans_modification.

    def fermer_fichier(self):
        if self.donnees.est_vide():
            return

        if not messagebox.askyesno("Confirmer", "Fermer sans enregistrer ?"):
            return

        self.donnees.fermer_fichier_csv()
        self.date_debut = None
        self.date_fin = None
        self.afficher_aucun_fichier_charge_barre_outils()
        self.teneur_maximum = None
        self.concentrations_maximum: dict[str, float] = {
            self.configuration_utilisateur.drapeau_smps: None,
            self.configuration_utilisateur.drapeau_cpc: None,
        }

        self.xlim_original = None
        self.ylim_original = None

        self.tracer_graphe_2d()
        self.tracer_graphe_3d()
        self.tracer_graphe_correlation()
        self.mettre_a_jour_historique()

    def sauvegarder_fichier(self):
        dossier_resultats = self.configuration_utilisateur.chemin_resultats
        dossier_flags = self.configuration_utilisateur.chemin_drapeaux

        if self.donnees.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        # on cree les dossiers s'ils n'existent pas
        os.makedirs(dossier_resultats, exist_ok=True)
        os.makedirs(dossier_flags, exist_ok=True)

        # sauvegarde du fichier filtre (lignes valides uniquement)
        chemin_absolu_donnees_filtrees = filedialog.asksaveasfilename(
            title="Sauvegarder les données filtrées",
            initialdir=dossier_resultats,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        # sauvegarde du fichier des flags (lignes invalidees)
        chemin_absolu_flags = filedialog.asksaveasfilename(
            title="Sauvegarder le fichier des flags",
            initialdir=dossier_flags,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not chemin_absolu_donnees_filtrees or not chemin_absolu_flags:
            return

        self.donnees.sauvegarder_fichier_csv(chemin_absolu_donnees_filtrees, chemin_absolu_flags)

    def quitter_programme(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.application.destroy()

    def mettre_a_jour_trace_graphe_2d(self):
        self.barre_onglets.obtenir_toile("Particules", 0).draw()

    def mettre_a_jour_trace_graphe_3d(self):
        self.barre_onglets.obtenir_toile("Graphe 3D").draw()

    def mettre_a_jour_trace_graphe_correlation(self):
        self.barre_onglets.obtenir_toile("Particules", 1).draw()
        self.barre_onglets.obtenir_toile("Corrélation").draw()

    def tracer_graphe_2d(self):
        if self.donnees.est_vide() or self.date_debut is None or self.date_fin is None:
            self.graphe_2d.effacer_graphe_2d()
            self.mettre_a_jour_trace_graphe_2d()
            return

        self.interactions.reinitialiser_rectangle()
        self.date_fin = self.temps.ajouter_23_heures_59_minutes_et_59_secondes(self.date_debut)

        self.graphe_2d.tracer_graphe_2d(
            self.donnees,
            self.date_debut,
            self.date_fin,
            self.concentrations_maximum[self.donnees.nom_colonne_concentration_courante],
        )

        # Sauvegarde les limites du graphe après le trace(pour dezzommer et avoir le meme graphe quavant)
        self.xlim_original = self.graphe_2d.ax.get_xlim()
        self.ylim_original = self.graphe_2d.ax.get_ylim()

        # Initialisation de l'infobulle.
        # FIXME : Vérifier si l'initialisation de l'infobulle se fait au bon endroit.
        self.infobulle: Annotation = self.graphe_2d.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="orange", alpha=0.9),
            visible=False,
        )

        self.mettre_a_jour_trace_graphe_2d()

    def tracer_graphe_3d(self):
        if self.donnees.est_vide() or self.date_debut is None or self.date_fin is None:
            self.graphe_3d.effacer_graphe_3d()
            self.mettre_a_jour_trace_graphe_3d()
            return

        self.date_fin = self.temps.ajouter_23_heures_59_minutes_et_59_secondes(self.date_debut)

        self.graphe_3d.tracer_graphe_3d(self.donnees, self.date_debut, self.date_fin, self.teneur_maximum)

        self.mettre_a_jour_trace_graphe_3d()

    def tracer_graphe_correlation(self):
        if (
            self.donnees.est_vide()
            or self.donnees.est_tout_invalide()
            or self.date_debut is None
            or self.date_fin is None
        ):
            self.graphe_correlation.effacer_graphe_correlation()
            self.mettre_a_jour_trace_graphe_correlation()
            return

        self.graphe_correlation.tracer_graphe_correlation(self.donnees, self.concentrations_maximum)

        self.mettre_a_jour_trace_graphe_correlation()

    def sauter_au_jour_suivant(self):
        if self.donnees.est_vide() or self.date_debut >= self.donnees.obtenir_derniere_date():
            return

        self.date_debut = self.temps.ajouter_24_heures(self.date_debut)
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.afficher_jour_barre_outils()

    def sauter_au_jour_precedent(self):
        if self.donnees.est_vide() or self.date_debut <= self.donnees.obtenir_premiere_date():
            return

        self.date_debut = self.temps.soustraire_24_heures(self.date_debut)
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.afficher_jour_barre_outils()

    def sauter_au_premier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_premiere_date()
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.afficher_jour_barre_outils()

    def sauter_au_dernier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_derniere_date()
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.afficher_jour_barre_outils()

    # demande du facteur
    def demander_facteur(self):
        facteur = askfloat("Facteur", "Multiplier par :")

        if facteur is None or self.donnees.est_vide():
            return

        self.donnees.multiplier_concentration(facteur)
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_smps] *= facteur
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_cpc] *= facteur

        self.tracer_graphe_2d()
        self.tracer_graphe_correlation()

    def changer_colonne_concentration(self):
        self.donnees.echanger_nom_colonne_concentration()

        self.tracer_graphe_2d()

    def construire_raccourcis_clavier(self):
        for raccourci, fonction_appelee in self.description_raccourcis_clavier:
            self.application.bind(raccourci, fonction_appelee)

    def construire_interface(self):
        self.application.mainloop()

    def zoomer(self):
        if not self.interactions.rectangle_actif:
            messagebox.showinfo("Info", "Aucun rectangle sélectionné.\n Cliquez d'abord sur 'Sélectionner plage' ")
            return

        # delegue le zoome a interaction
        rafraichir = self.interactions.zoomer_rectangle(self.graphe_2d.ax)

        if rafraichir:
            # redessine le grpahe pour que le zomme se fasse
            self.barre_onglets.obtenir_toile("Particules", 0).draw()

    def dezoomer(self):
        if self.xlim_original is None or self.ylim_original is None:
            return

        # remet les nouvelle limite
        self.graphe_2d.ax.set_xlim(self.xlim_original)
        self.graphe_2d.ax.set_ylim(self.ylim_original)
        self.barre_onglets.obtenir_toile("Particules", 0).draw()
