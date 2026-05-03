import os
import yaml
import logging


class Configuration:

    def __init__(self, chemin_configuration: str):
        self.logger = logging.getLogger()

        self.fichier_configuration = self.charger_configuration(chemin_configuration)

    def charger_configuration(self, chemin_configuration):
        if not os.path.exists(chemin_configuration):
            self.logger.warning(f"Fichier de configuration {chemin_configuration} introuvable.")
            return {}

        with open(chemin_configuration, "r", encoding="utf-8") as fichier:
            return yaml.safe_load(fichier) or {}


class ConfigurationUtilisateur(Configuration):

    def __init__(self, chemin_configuration: str):
        super().__init__(chemin_configuration)

        repertoires = self.fichier_configuration.get("repertoires", {})

        self.chemin_donnees = repertoires.get("chemin_donnees", "")
        self.chemin_resultats = repertoires.get("chemin_resultats", "")
        self.chemin_drapeaux = repertoires.get("chemin_drapeaux", "")

        noms_colonnes = self.fichier_configuration.get("noms_colonnes", {})

        self.drapeau_pollution = noms_colonnes.get("drapeau_pollution", "")
        self.drapeau_sauvegarde = noms_colonnes.get("drapeau_sauvegarde", "")
        self.drapeau_smps = noms_colonnes.get("drapeau_smps", "")
        self.drapeau_cpc = noms_colonnes.get("drapeau_cpc", "")
        self.drapeau_prefixe_particules = noms_colonnes.get("drapeau_prefixe_particules", "")


class ConfigurationProgramme(Configuration):

    def __init__(self, chemin_configuration):
        super().__init__(chemin_configuration)

        fenetre = self.fichier_configuration.get("fenetre", {})

        self.titre_fenetre = fenetre.get("titre_fenetre", "")
        self.largeur_fenetre = fenetre.get("largeur_fenetre", 1280)
        self.hauteur_fenetre = fenetre.get("hauteur_fenetre", 720)

        temps = self.fichier_configuration.get("temps", {})

        self.pas_heures = temps.get("pas_heures", 24)
