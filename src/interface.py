import logging
import os
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

        self.temps_graphe = Temps(self.configuration_programme.pas_heures_graphe)
        self.temps_suivant = Temps(self.configuration_programme.pas_heures_suivant)

        # Gestion des données.

        self.donnees = Donnees(
            self.configuration_utilisateur.drapeau_smps,
            self.configuration_utilisateur.drapeau_cpc,
            self.configuration_utilisateur.drapeau_sauvegarde,
            self.configuration_utilisateur.drapeau_prefixe_particules,
            self.configuration_utilisateur.drapeau_pollution,
        )

        # Graphe 2D.
        self.graphe_2d: Graphe2D = Graphe2D()

        self.date_debut: datetime = None
        self.date_fin: datetime = None

        self.xlim_original = None
        self.ylim_original = None

        # Graphe 3D

        self.graphe_3d: Graphe3D = Graphe3D()

        # Pour garder une échelle constante de couleur du graphe 3D, on garde en mémoire la valeur maximum.
        self.teneur_maximum = None

        # Graphe de corrélation.

        self.graphe_correlation_onglet_particules: GrapheCorrelation = GrapheCorrelation()
        self.graphe_correlation_onglet_correlation: GrapheCorrelation = GrapheCorrelation()

        # Pour garder une échelle constante du graphe de corrélation,
        # on garde en mémoire la valeur maximum des abscisses et des ordonnées.
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

        # Barre des menus déroulants.

        self.description_barre_menus: DescriptionBarreMenus = [
            (
                "Fichier",
                [
                    ("Charger un fichier", None, self.charger_fichier),
                    ("Fermer sans enregistrer", None, self.fermer_fichier),
                    None,
                    ("Enregistrer sous", None, self.sauvegarder_fichier_filtre),
                    ("Enregistrer drapeaux sous", None, self.sauvegarder_fichier_drapeaux),
                    None,
                    ("Quitter", None, self.quitter_programme),
                ],
            ),
            (
                "Actions",
                [
                    ("Invalider toutes les données", None, self.invalider_toutes_donnees),
                    ("Invalider les données du jour", None, self.invalider_donnees_affichees),
                    None,
                    ("Annuler", "Ctrl+Z", self.annuler),
                    ("Rétablir", "Ctrl+Shift+Z", self.retablir),
                    None,
                    ("Appliquer un facteur de correction", None, self.demander_facteur),
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

        # Barre des outils du jour.

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
        self.mettre_a_jour_etiquette_barre_outils_jour()

        # Barre des outils de validation.

        self.description_barre_outils_validation: DescriptionBarreOutils = [
            ("Sélectionner plage", self.selectionner_plage),
            ("Supprimer plage", self.supprimer_plage),
            None,
            ("Annuler", self.annuler),
            ("Rétablir", self.retablir),
            None,
            ("Facteur", self.demander_facteur),
            None,
            ("Actualiser", self.actualiser),
        ]

        self.barre_outils_validation = BarreOutils(self.application, self.description_barre_outils_validation)
        self.barre_outils_validation.construire_barre_outils()
        self.barre_outils_validation.construire_etiquette()
        self.mettre_a_jour_etiquette_barre_outils_validation()

        # Barre des onglets.

        self.description_barre_onglets: DescriptionBarreOnglets = [
            ("Particules", [self.graphe_2d, self.graphe_correlation_onglet_particules]),
            ("Graphe 3D", [self.graphe_3d]),
            ("Corrélation", [self.graphe_correlation_onglet_correlation]),
            ("Historique", []),
        ]

        self.barre_onglets: BarreOnglets = BarreOnglets(self.application, self.description_barre_onglets)
        self.barre_onglets.construire_barre_onglets()

        # Onglets contenus dans la barre des onglets.

        self.barre_onglets.construire_onglets()

        # Initialisation de l'onglet historique.
        self.mettre_a_jour_historique()

        # Gestion des interactions avec les graphes.

        self.interactions = Interactions()

        self.infobulle: Annotation = None
        self.interactions.initialiser_rectangle_selector(self.graphe_2d.ax)
        self.barre_onglets.obtenir_toile("Particules", 0).mpl_connect(
            "button_press_event", self.repondre_apres_clic_souris
        )
        self.barre_onglets.obtenir_toile("Particules", 0).mpl_connect("motion_notify_event", self.info_point)

        # Raccourcis clavier.

        # Le lien entre le raccourci clavier et sa fonction appelée par Tkinter
        # est sensible à la casse de la touche.
        self.description_raccourcis_clavier = [
            ("<Control-z>", lambda evenement: self.annuler()),
            ("<Control-Z>", lambda evenement: self.annuler()),
            ("<Control-Shift-z>", lambda evenement: self.retablir()),
            ("<Control-Shift-Z>", lambda evenement: self.retablir()),
        ]

        self.construire_raccourcis_clavier()

    # Main.

    def construire_interface(self):
        self.application.mainloop()

    # Barre des menus déroulants.

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
            self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)
            self.tracer_graphe_2d()
            self.tracer_graphe_3d()
            self.tracer_graphe_correlation()
            self.mettre_a_jour_etiquette_barre_outils_jour()
            self.mettre_a_jour_etiquette_barre_outils_validation()

    # Barre des menus déroulants.

    def sauvegarder_fichier_filtre(self):
        dossier_resultats = self.configuration_utilisateur.chemin_resultats

        if self.donnees.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        # on cree les dossiers s'ils n'existent pas
        os.makedirs(dossier_resultats, exist_ok=True)

        # sauvegarde du fichier filtre (lignes valides uniquement)
        chemin_absolu_donnees_filtrees = filedialog.asksaveasfilename(
            title="Sauvegarder les données filtrées",
            initialdir=dossier_resultats,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not chemin_absolu_donnees_filtrees:
            return

        self.donnees.sauvegarder_fichier_filtre_csv(chemin_absolu_donnees_filtrees)

    def sauvegarder_fichier_drapeaux(self):
        dossier_flags = self.configuration_utilisateur.chemin_drapeaux

        if self.donnees.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        os.makedirs(dossier_flags, exist_ok=True)

        # sauvegarde du fichier des flags (lignes invalidees)
        chemin_absolu_flags = filedialog.asksaveasfilename(
            title="Sauvegarder le fichier des flags",
            initialdir=dossier_flags,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not chemin_absolu_flags:
            return

        self.donnees.sauvegarder_fichier_drapeaux_csv(chemin_absolu_flags)

    def fermer_fichier(self):
        if self.donnees.est_vide():
            return

        if not messagebox.askyesno("Confirmer", "Fermer sans enregistrer ?"):
            return

        self.donnees.fermer_fichier_csv()
        self.date_debut = None
        self.date_fin = None
        self.mettre_a_jour_etiquette_barre_outils_jour()
        self.mettre_a_jour_etiquette_barre_outils_validation()
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

    def quitter_programme(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.application.quit()
            self.application.destroy()

    # Actions.

    def invalider_toutes_donnees(self):
        # On invalide toutes les données, sauf celles qui ne sont pas définies.
        self.donnees.invalider_dates(
            self.donnees.supprimer_concentration_courante_non_definie().obtenir_colonne_dates().obtenir_dataframe()
        )
        self.tracer_graphe_2d()
        self.mettre_a_jour_historique()

    def invalider_donnees_affichees(self):
        # On invalide les données affichées sur le graphe actuel, sauf celles qui ne sont pas définies.
        self.donnees.invalider_dates(
            self.donnees.supprimer_concentration_courante_non_definie()
            .obtenir_dates(self.date_debut, self.date_fin)
            .obtenir_colonne_dates()
            .obtenir_dataframe()
        )
        self.tracer_graphe_2d()
        self.mettre_a_jour_historique()

    # Barre des outils du jour.

    def sauter_au_premier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_premiere_date()
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def sauter_au_jour_suivant(self):
        if self.donnees.est_vide() or self.date_debut >= self.donnees.obtenir_derniere_date():
            return

        self.date_debut = self.temps_suivant.ajouter_pas_heures(self.date_debut)
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def sauter_au_jour_precedent(self):
        if self.donnees.est_vide() or self.date_debut <= self.donnees.obtenir_premiere_date():
            return

        self.date_debut = self.temps_suivant.soustraire_pas_heures(self.date_debut)
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def sauter_au_dernier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_derniere_date()
        self.tracer_graphe_2d()
        self.tracer_graphe_3d()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def changer_colonne_concentration(self):
        self.donnees.echanger_nom_colonne_concentration()

        self.tracer_graphe_2d()

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

    def mettre_a_jour_etiquette_barre_outils_jour(self):
        if self.donnees.est_vide() or self.date_debut is None:
            self.barre_outils_jour.modifier_etiquette("")
            return

        self.barre_outils_jour.modifier_etiquette(f"Jour affiché : {self.date_debut.strftime("%Y-%m-%d")}")

    # Barre des outils de validation.

    def selectionner_plage(self):
        if self.donnees.est_vide():
            messagebox.showwarning("Attention !", "Aucune donnée à sélectionner.")
            return

        self.interactions.activer_mode_rectangle()
        self.mettre_a_jour_etiquette_barre_outils_validation()

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
            self.mettre_a_jour_historique()

    def annuler(self):
        self.donnees.annuler_invalidation_date()
        self.tracer_graphe_2d()
        self.mettre_a_jour_historique()

    def retablir(self):
        self.donnees.retablir_invalidation_date()
        self.tracer_graphe_2d()
        self.mettre_a_jour_historique()

    def demander_facteur(self):
        facteur = askfloat("Facteur", "Multiplier par :")

        if facteur is None or self.donnees.est_vide():
            return

        self.donnees.multiplier_concentration(facteur)
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_smps] *= facteur
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_cpc] *= facteur

        self.tracer_graphe_2d()
        self.tracer_graphe_correlation()

    def actualiser(self):
        self.tracer_graphe_3d()
        self.tracer_graphe_correlation()

    def mettre_a_jour_etiquette_barre_outils_validation(self):
        if self.donnees.est_vide() or self.date_debut is None:
            self.barre_outils_validation.modifier_etiquette("Aucune donnée chargée.")
            return

        self.barre_outils_validation.modifier_etiquette(
            "Dessinez un rectangle sur le graphe, puis cliquez sur 'Supprimer plage'."
        )

    # Onglets.

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
        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)

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

        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)

        self.graphe_3d.tracer_graphe_3d(self.donnees, self.date_debut, self.date_fin, self.teneur_maximum)

        self.mettre_a_jour_trace_graphe_3d()

    def tracer_graphe_correlation(self):
        if (
            self.donnees.est_vide()
            or self.donnees.est_tout_invalide()
            or self.date_debut is None
            or self.date_fin is None
        ):
            self.graphe_correlation_onglet_particules.effacer_graphe_correlation()
            self.graphe_correlation_onglet_correlation.effacer_graphe_correlation()
            self.mettre_a_jour_trace_graphe_correlation()
            return

        self.graphe_correlation_onglet_particules.tracer_graphe_correlation(self.donnees, self.concentrations_maximum)
        self.graphe_correlation_onglet_correlation.tracer_graphe_correlation(self.donnees, self.concentrations_maximum)
        # FIXME : Le graphe de corrélation est calculé deux fois, une fois pour chaque onglet.

        self.mettre_a_jour_trace_graphe_correlation()

    def mettre_a_jour_historique(self):
        historique = "Historique des modifications\n\n"
        historique += self.donnees.historique.obtenir_journal()
        self.barre_onglets.definir_texte("Historique", historique)

    # Interactions.

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
            self.mettre_a_jour_historique()

    # Raccourcis clavier.

    def construire_raccourcis_clavier(self):
        for raccourci, fonction_appelee in self.description_raccourcis_clavier:
            self.application.bind(raccourci, fonction_appelee)
