import logging
import tkinter as tk


from datetime import datetime
from enum import Enum
from matplotlib.backend_bases import Event
from matplotlib.text import Annotation
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askfloat
from pathlib import Path

from donnees import Donnees
from graphes import Graphe2D, GrapheSMPS, GrapheCPC, Graphe3D, GrapheCorrelation
from historique import Action
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

        self.chemin_repertoire_parent = Path(__file__).resolve().parent.parent

        self.configuration_utilisateur: ConfigurationUtilisateur = ConfigurationUtilisateur(
            self.chemin_repertoire_parent / "configuration_utilisateur.yaml"
        )
        self.configuration_programme: ConfigurationProgramme = ConfigurationProgramme(
            self.chemin_repertoire_parent / "configuration_programme.yaml"
        )

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
        self.graphe_2d_smps: GrapheSMPS = GrapheSMPS()
        self.graphe_2d_cpc: GrapheCPC = GrapheCPC()
        self.graphe_2d_recapitulatif: GrapheSMPS = GrapheSMPS()

        self.date_minimum: datetime = None
        self.date_debut: datetime = None
        self.date_fin: datetime = None
        self.date_maximum: datetime = None

        self.xlim_original = None
        self.ylim_original = None

        # Graphe 3D

        self.graphe_3d: Graphe3D = Graphe3D(self.configuration_programme.echelle_logarithmique_taille_particules)
        self.graphe_3d_recapitulatif: Graphe3D = Graphe3D(
            self.configuration_programme.echelle_logarithmique_taille_particules
        )
        # Pour garder une échelle constante de couleur du graphe 3D, on garde en mémoire la valeur maximum.
        self.teneur_maximum = None

        # Graphe de corrélation.

        self.graphe_correlation_onglet_correlation: GrapheCorrelation = GrapheCorrelation()
        self.graphe_correlation_recapitulatif: GrapheCorrelation = GrapheCorrelation()

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
                    (
                        "Enregistrer sous",
                        None,
                        lambda: self.enregistrer_fichier(
                            self.MethodeEnregistrement.SAUVEGARDER_COURANT,
                            self.configuration_utilisateur.chemin_sauvegarde,
                        ),
                    ),
                    None,
                    (
                        "Exporter données finales",
                        None,
                        lambda: self.enregistrer_fichier(
                            self.MethodeEnregistrement.EXPORTER_FINAL,
                            self.configuration_utilisateur.chemin_export_final,
                        ),
                    ),
                    (
                        "Exporter drapeaux",
                        None,
                        lambda: self.enregistrer_fichier(
                            self.MethodeEnregistrement.EXPORTER_DRAPEAUX,
                            self.configuration_utilisateur.chemin_export_drapeaux,
                        ),
                    ),
                    None,
                    ("Quitter", None, self.quitter_programme),
                ],
            ),
            (
                "Actions",
                [
                    (
                        "Invalider toutes les données",
                        None,
                        lambda: self.agir_donnees(Action.SUPPRIMER, self.ZoneAction.TOUTES),
                    ),
                    (
                        "Invalider les données du jour",
                        None,
                        lambda: self.agir_donnees(Action.SUPPRIMER, self.ZoneAction.FENETRE),
                    ),
                    None,
                    (
                        "Restaurer toutes les données",
                        None,
                        lambda: self.agir_donnees(Action.RESTAURER, self.ZoneAction.TOUTES),
                    ),
                    (
                        "Restaurer les données du jour",
                        None,
                        lambda: self.agir_donnees(Action.RESTAURER, self.ZoneAction.FENETRE),
                    ),
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
            ("Zoomer", self.zoomer),
            ("Dezoomer", self.dezoomer),
        ]

        self.barre_outils_jour = BarreOutils(self.application, self.description_barre_outils_jour)
        self.barre_outils_jour.construire_barre_outils()
        self.barre_outils_jour.construire_etiquette()
        self.mettre_a_jour_etiquette_barre_outils_jour()

        # Barre des outils de validation.

        self.description_barre_outils_validation: DescriptionBarreOutils = [
            ("Supprimer plage", self.supprimer_plage),
            ("Restaurer plage", self.restaurer_plage),
            None,
            ("Annuler", self.annuler),
            ("Rétablir", self.retablir),
            None,
            ("Facteur", self.demander_facteur),
            None,
            ("Recalculer graphes", self.initialiser_graphes_onglets),
        ]

        self.barre_outils_validation = BarreOutils(self.application, self.description_barre_outils_validation)
        self.barre_outils_validation.construire_barre_outils()
        self.barre_outils_validation.construire_etiquette()
        self.mettre_a_jour_etiquette_barre_outils_validation()

        # Barre des onglets.

        self.description_barre_onglets: DescriptionBarreOnglets = [
            (
                "Particules",
                [self.graphe_2d_smps, self.graphe_2d_cpc],
            ),
            (
                "Graphe 3D",
                [self.graphe_3d],
            ),
            (
                "Corrélation",
                [self.graphe_correlation_onglet_correlation],
            ),
            (
                "Historique",
                [],
            ),
            (
                "Récapitulatif",
                [self.graphe_2d_recapitulatif, self.graphe_3d_recapitulatif, self.graphe_correlation_recapitulatif],
            ),
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
        self.interactions.initialiser_rectangle_selector(self.graphe_2d_smps.ax)
        self.barre_onglets.obtenir_toile(self.graphe_2d_smps).mpl_connect(
            "button_press_event", self.repondre_apres_clic_souris
        )
        self.barre_onglets.obtenir_toile(self.graphe_2d_smps).mpl_connect("motion_notify_event", self.info_point)

        # Gestion de l'actualisation de l'onglet actif uniquement.

        self.barre_onglets.barre_onglets.bind(
            "<<NotebookTabChanged>>", lambda evenement: self.actualiser_graphes_onglet_actif()
        )

        # Raccourcis clavier.

        # Le lien entre le raccourci clavier et sa fonction appelée par Tkinter est sensible à la casse de la touche.
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
        # chemin_relatif_initial = self.configuration_utilisateur.chemin_donnees

        # Chemin absolu vers le dossier de données, calculé par rapport à l'emplacement
        # de main.py pour éviter tout bug si le programme est lancé depuis un autre répertoire.
        chemin_relatif_initial = self.chemin_repertoire_parent / self.configuration_utilisateur.chemin_chargement

        chemin_absolu_chargement = filedialog.askopenfilename(
            initialdir=chemin_relatif_initial,
            filetypes=[("CSV files", "*.csv"), ("All", "*.*")],
        )

        if not chemin_absolu_chargement:
            return

        # Si un fichier est déjà chargé, on demande confirmation avant de le remplacer
        if not self.donnees.est_vide() and not messagebox.askyesno(
            "Confirmer", "Un fichier est déjà chargé. Voulez-vous le fermer et charger un nouveau fichier ?"
        ):
            return

        self.remettre_variables_par_defaut()

        succes = self.donnees.charger_fichier_csv(chemin_absolu_chargement)

        if not succes:
            messagebox.showwarning("Attention", "Fichier au mauvais format.")
            return

        self.teneur_maximum = self.donnees.obtenir_particules().obtenir_valeur_maximum()

        self.concentrations_maximum[self.configuration_utilisateur.drapeau_smps] = (
            self.donnees.obtenir_colonne_concentration_smps().obtenir_valeur_maximum()
        )

        self.concentrations_maximum[self.configuration_utilisateur.drapeau_cpc] = (
            self.donnees.obtenir_colonne_concentration_cpc().obtenir_valeur_maximum()
        )

        if self.donnees.est_vide():
            return

        self.interactions.rectangle_selector.set_active(True)  # active le rectangle quand un fichier charger

        self.date_minimum = self.donnees.obtenir_minuit_premiere_date()
        self.date_debut = self.donnees.obtenir_minuit_premiere_date()
        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)
        self.date_maximum = self.donnees.obtenir_minuit_derniere_date()

        self.initialiser_graphes_onglets()

        self.mettre_a_jour_etiquette_barre_outils_jour()
        self.mettre_a_jour_etiquette_barre_outils_validation()

    # Barre des menus déroulants.

    class MethodeEnregistrement(Enum):
        SAUVEGARDER_COURANT = (1, "Sauvegarder le projet")
        EXPORTER_FINAL = (2, "Exporter les données filtrées")
        EXPORTER_DRAPEAUX = (3, "Exporter les drapeaux")

        def __init__(self, value, etiquette):
            self._value_ = value
            self.etiquette = etiquette

    def enregistrer_fichier(self, methode_enregistrement: MethodeEnregistrement, chemin_par_defaut: str):
        if self.donnees.est_vide():
            messagebox.showwarning("Attention", "Aucune donnée à sauvegarder.")
            return

        # sauvegarde du fichier filtre (lignes valides uniquement)
        chemin_absolu_sauvegarde = filedialog.asksaveasfilename(
            title=methode_enregistrement.etiquette,
            initialdir=chemin_par_defaut,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not chemin_absolu_sauvegarde:
            return

        if methode_enregistrement is self.MethodeEnregistrement.SAUVEGARDER_COURANT:
            self.donnees.enregistrer_fichier_csv(chemin_absolu_sauvegarde)

        elif methode_enregistrement is self.MethodeEnregistrement.EXPORTER_FINAL:
            self.donnees.exporter_fichier_final_csv(chemin_absolu_sauvegarde)

        elif methode_enregistrement is self.MethodeEnregistrement.EXPORTER_DRAPEAUX:
            self.donnees.exporter_fichier_drapeaux_csv(chemin_absolu_sauvegarde)

        # messagebox.showinfo("Succès", f"{methode_enregistrement.etiquette} :\n{chemin_absolu_sauvegarde}")

    def fermer_fichier(self):
        if self.donnees.est_vide():
            return

        if not messagebox.askyesno("Confirmer", "Fermer sans enregistrer ?"):
            return

        self.remettre_variables_par_defaut()

    def remettre_variables_par_defaut(self):
        self.donnees.fermer_fichier_csv()
        self.date_minimum = None
        self.date_debut = None
        self.date_fin = None
        self.date_maximum = None
        self.mettre_a_jour_etiquette_barre_outils_jour()
        self.mettre_a_jour_etiquette_barre_outils_validation()
        self.teneur_maximum = None
        self.concentrations_maximum: dict[str, float] = {
            self.configuration_utilisateur.drapeau_smps: None,
            self.configuration_utilisateur.drapeau_cpc: None,
        }
        self.infobulle = None

        self.xlim_original = None
        self.ylim_original = None
        self.interactions.rectangle_selector.set_active(False)  # pas de fichier pas de selction de rectangle

        self.initialiser_graphes_onglets()

        self.mettre_a_jour_historique()

    def quitter_programme(self):
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter ?"):
            self.application.quit()
            self.application.destroy()

    # Actions.

    class ZoneAction(Enum):
        TOUTES = 1
        FENETRE = 2

    def agir_donnees(self, action: Action, zone_action: ZoneAction):
        if self.donnees.est_vide():
            return

        selection = self.donnees.supprimer_concentration_smps_non_definie()

        if action is Action.SUPPRIMER:
            selection = selection.obtenir_donnees_valides()
        elif action is Action.RESTAURER:
            selection = selection.obtenir_donnees_invalides()

        if zone_action is self.ZoneAction.FENETRE:
            selection = selection.obtenir_dates(self.date_debut, self.date_fin)

        selection = selection.obtenir_colonne_dates().obtenir_dataframe()

        if action is Action.SUPPRIMER:
            self.donnees.invalider_dates(selection)
        elif action is Action.RESTAURER:
            self.donnees.restaurer_dates(selection)

        self.actualiser_graphes_onglet_actif()

        self.mettre_a_jour_historique()

    # Barre des outils du jour.

    def sauter_au_premier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_premiere_date()
        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)

        self.actualiser_graphes_onglet_actif()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def sauter_au_jour_suivant(self):
        if self.donnees.est_vide() or self.date_debut >= self.donnees.obtenir_derniere_date():
            return

        self.date_debut = self.temps_suivant.ajouter_pas_heures(self.date_debut)
        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)

        self.actualiser_graphes_onglet_actif()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def sauter_au_jour_precedent(self):
        if self.donnees.est_vide() or self.date_debut <= self.donnees.obtenir_premiere_date():
            return

        self.date_debut = self.temps_suivant.soustraire_pas_heures(self.date_debut)
        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)

        self.actualiser_graphes_onglet_actif()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def sauter_au_dernier_jour(self):
        if self.donnees.est_vide():
            return

        self.date_debut = self.donnees.obtenir_derniere_date()
        self.date_fin = self.temps_graphe.ajouter_pas_heures_moins_une_seconde(self.date_debut)

        self.actualiser_graphes_onglet_actif()

        self.mettre_a_jour_etiquette_barre_outils_jour()

    def zoomer(self):
        if not self.interactions.est_valide_rectangle:
            messagebox.showinfo("Info", "Aucun rectangle sélectionné.\n Cliquez d'abord sur 'Sélectionner plage' ")
            return

        # Sauvegarde les limites du graphe après le trace(pour dezzommer et avoir le meme graphe quavant)
        if self.xlim_original is None:
            self.xlim_original = self.graphe_2d_smps.ax.get_xlim()
        if self.ylim_original is None:
            self.ylim_original = self.graphe_2d_smps.ax.get_ylim()

        # delegue le zoome a interaction
        rafraichir = self.interactions.zoomer_rectangle(self.graphe_2d_smps.ax)

        if rafraichir:
            self.mettre_a_jour_trace_graphe_2d(self.graphe_2d_smps)

    def dezoomer(self):
        if self.xlim_original is None or self.ylim_original is None:
            return

        # remet les nouvelle limite
        self.graphe_2d_smps.ax.set_xlim(self.xlim_original)
        self.graphe_2d_smps.ax.set_ylim(self.ylim_original)

        self.xlim_original = None
        self.ylim_original = None

        self.mettre_a_jour_trace_graphe_2d(self.graphe_2d_smps)

    def mettre_a_jour_etiquette_barre_outils_jour(self):
        if self.donnees.est_vide() or self.date_debut is None:
            self.barre_outils_jour.modifier_etiquette("")
            return

        self.barre_outils_jour.modifier_etiquette(f"Jour affiché : {self.date_debut.strftime("%Y-%m-%d")}")

    # Barre des outils de validation.

    def mode_plage(self, mode: str):
        # aucun rectangle dessiner on infore l'utilisateur

        if not self.interactions.est_valide_rectangle:
            messagebox.showinfo(
                "Info",
                "Aucun rectangle sélectionné.\n Il faut dessiner un rectangle sur le graphe.",
            )
            return

        # selon le mode  on supprime ou restaure
        if mode is Action.SUPPRIMER:
            rafraichir = self.interactions.supprimer_plage_rectangle(self.donnees, self.date_debut, self.date_fin)
        elif mode is Action.RESTAURER:
            rafraichir = self.interactions.restaurer_plage_rectangle(self.donnees, self.date_debut, self.date_fin)

        # si des points modifier on redessine le graphe
        if rafraichir:
            self.actualiser_graphes_onglet_actif()
            self.mettre_a_jour_historique()

    def supprimer_plage(self):
        self.mode_plage(Action.SUPPRIMER)

    def restaurer_plage(self):
        self.mode_plage(Action.RESTAURER)

    def annuler(self):
        self.donnees.annuler_action()
        self.actualiser_graphes_onglet_actif()
        self.mettre_a_jour_historique()

    def retablir(self):
        self.donnees.retablir_action()
        self.actualiser_graphes_onglet_actif()
        self.mettre_a_jour_historique()

    def demander_facteur(self):
        facteur = askfloat("Facteur", "Multiplier par :")

        if facteur is None or self.donnees.est_vide():
            return

        self.donnees.multiplier_concentration(facteur)
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_smps] *= facteur
        self.concentrations_maximum[self.configuration_utilisateur.drapeau_cpc] *= facteur

        self.actualiser_graphes_onglet_actif()

    def initialiser_graphes_onglets(self):
        self.tracer_graphe_2d(
            self.graphe_2d_smps, self.date_debut, self.date_fin, self.configuration_utilisateur.drapeau_smps
        )
        self.tracer_graphe_2d(
            self.graphe_2d_cpc, self.date_debut, self.date_fin, self.configuration_utilisateur.drapeau_cpc
        )

        self.tracer_graphe_3d(self.graphe_3d, self.date_debut, self.date_fin)

        self.tracer_graphe_correlation(self.graphe_correlation_onglet_correlation)

        self.tracer_graphe_2d(
            self.graphe_2d_recapitulatif,
            self.date_minimum,
            self.date_maximum,
            self.configuration_utilisateur.drapeau_smps,
        )
        self.tracer_graphe_3d(self.graphe_3d_recapitulatif, self.date_minimum, self.date_maximum)
        self.tracer_graphe_correlation(self.graphe_correlation_recapitulatif)

    def actualiser_graphes_onglet_actif(self):
        indice_onglet_actif = self.barre_onglets.barre_onglets.index("current")
        nom_onglet = self.description_barre_onglets[indice_onglet_actif][0]

        match nom_onglet:
            case "Particules":
                self.tracer_graphe_2d(
                    self.graphe_2d_smps, self.date_debut, self.date_fin, self.configuration_utilisateur.drapeau_smps
                )
                self.tracer_graphe_2d(
                    self.graphe_2d_cpc, self.date_debut, self.date_fin, self.configuration_utilisateur.drapeau_cpc
                )

            case "Graphe 3D":
                self.tracer_graphe_3d(self.graphe_3d, self.date_debut, self.date_fin)

    def mettre_a_jour_etiquette_barre_outils_validation(self):
        if self.donnees.est_vide() or self.date_debut is None:
            self.barre_outils_validation.modifier_etiquette("Aucune donnée chargée.")
            return

        self.barre_outils_validation.modifier_etiquette(
            "Dessinez un rectangle sur le graphe, puis cliquez sur 'Supprimer plage'."
        )

    # Onglets.

    def mettre_a_jour_trace_graphe_2d(self, graphe_2d: Graphe2D):
        self.barre_onglets.obtenir_toile(graphe_2d).draw()

    def mettre_a_jour_trace_graphe_2d_differee(self, graphe_2d: Graphe2D):
        self.barre_onglets.obtenir_toile(graphe_2d).draw_idle()

    def mettre_a_jour_trace_graphe_3d(self, graphe_3d: Graphe3D):
        self.barre_onglets.obtenir_toile(graphe_3d).draw()

    def mettre_a_jour_trace_graphe_correlation(self, graphe_correlation: GrapheCorrelation):
        self.barre_onglets.obtenir_toile(graphe_correlation).draw()

    def tracer_graphe_2d(
        self, graphe_2d: Graphe2D, date_debut: datetime, date_fin: datetime, nom_colonne_concentration: str
    ):
        if self.donnees.est_vide() or date_debut is None or date_fin is None:
            graphe_2d.effacer_graphe_2d()
            self.mettre_a_jour_trace_graphe_2d(graphe_2d)
            return

        self.interactions.reinitialiser_rectangle()

        graphe_2d.tracer_graphe_2d(
            self.donnees,
            date_debut,
            date_fin,
            self.concentrations_maximum[nom_colonne_concentration],
        )  # dessine les points

        self.infobulle = self.graphe_2d_smps.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="orange", alpha=0.9),
            visible=False,
        )

        self.mettre_a_jour_trace_graphe_2d(graphe_2d)

    def tracer_graphe_3d(self, graphe_3d: Graphe3D, date_debut: datetime, date_fin: datetime):
        if self.donnees.est_vide() or date_debut is None or date_fin is None:
            graphe_3d.effacer_graphe_3d()
            self.mettre_a_jour_trace_graphe_3d(graphe_3d)
            return

        graphe_3d.tracer_graphe_3d(self.donnees, date_debut, date_fin, self.teneur_maximum)

        self.mettre_a_jour_trace_graphe_3d(graphe_3d)

    def tracer_graphe_correlation(self, graphe_correlation: GrapheCorrelation):
        if (
            self.donnees.est_vide()
            or self.donnees.est_tout_invalide()
            or self.date_debut is None
            or self.date_fin is None
        ):
            graphe_correlation.effacer_graphe_correlation()
            self.mettre_a_jour_trace_graphe_correlation(graphe_correlation)
            return

        graphe_correlation.tracer_graphe_correlation(self.donnees, self.concentrations_maximum)

        self.mettre_a_jour_trace_graphe_correlation(graphe_correlation)

    def mettre_a_jour_historique(self):
        historique = "Historique des modifications\n\n"
        historique += self.donnees.historique.obtenir_journal()
        self.barre_onglets.modifier_texte("Historique", historique)

    # Interactions.

    # Bug corrige : rectangledessine + relache sur un point,l'infobulle reste affichée
    def info_point(self, evenement: Event):
        # quand rectangle actif , priorite
        if self.interactions.est_en_mouvement_rectangle:
            return

        doit_rafraichir = self.interactions.info_point(
            evenement,
            self.donnees,
            self.graphe_2d_smps.ax,
            self.date_debut,
            self.date_fin,
            self.infobulle,
        )

        if doit_rafraichir:
            self.mettre_a_jour_trace_graphe_2d_differee(self.graphe_2d_smps)

    # Bug corriger : après avoir dessine un rectangle, un clic gauche pour l annuler
    def repondre_apres_clic_souris(self, evenement: Event):
        if (
            self.interactions.rectangle_selector is not None
            and self.interactions.est_en_mouvement_rectangle
            and evenement.button == 1
        ):
            # evenement.button != 3 : le clic droit passe toujours, meme si rectangle dessine
            self.interactions.reinitialiser_rectangle()  # remettre rectangle_actif a false si clique gauche(1)
            return

        doit_rafraichir = self.interactions.repondre_apres_clic_souris(
            evenement,
            self.donnees,
            self.graphe_2d_smps.ax,
            self.date_debut,
            self.date_fin,
        )

        if doit_rafraichir:
            self.actualiser_graphes_onglet_actif()
            self.mettre_a_jour_historique()

    # Raccourcis clavier.

    def construire_raccourcis_clavier(self):
        for raccourci, fonction_appelee in self.description_raccourcis_clavier:
            self.application.bind(raccourci, fonction_appelee)
