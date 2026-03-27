from tkinter import simpledialog, messagebox  

class CorrectionsMixin:
    #Annuler 
    def _sauvegarder_annulation(self):
        self.annuler_stack.append(self.df.copy())  # On garde une copie du DataFrame actuel
        if len(self.annuler_stack) > 15:
            self.annuler_stack.pop(0)   # On supprime le plus ancien si plus de 15

    def annuler(self):
        #Annule la dernière action (Ctrl+Z)
        if not self.annuler_stack:  # Si la pile est vide
            print("Rien à annuler")
            return

        self.df = self.annuler_stack.pop()  # On reprend le dernier état sauvegardé
        self.sel_x1 = self.sel_x2 = None
        self.click_n = 0

        print(f"Annulation effectueee  (reste {len(self.annuler_stack)})")
        self._refresh_all()  # Rafraîchit l'affichage

    #Reset
    
    def reset_all(self):
        #Remet les données à l'état original  +demande confirmation
        if not messagebox.askyesno("Confirmer", "Remettre toutes les données a zero ?"):
            return  # Si l'utilisateur dit non, on arrête

        self._sauvegarder_annulation()  # Sauvegarde avant reset
        self.df = self.df_original.copy()  # Remet à l'état original
        self.sel_x1 = self.sel_x2 = None
        self.click_n = 0

        print("Reset complet")
        self._refresh_all()

    # Facteur de correction
    
    def appliquer_correction(self):
        #Multiplie toutes les concentrations par un facteur saisi par l'utilisateur
        facteur = simpledialog.askfloat(
            "Facteur de correction",
            "Multiplier toutes les concentrations par :",
            initialvalue=1.0, minvalue=0.001, maxvalue=100.0
        )
        if facteur is None:  # Si l'utilisateur annule
            return

        self._sauvegarder_annulation()  # Sauvegarde avant modification

        # Colonnes des bins
        colonnes_bins = [c for c in self.df.columns if c.startswith("smps_d_")]
        self.df.loc[:, colonnes_bins]         *= facteur
        self.df.loc[:, "smps_concTotal"] *= facteur

        print(f"Facteur {facteur:.4f} appliqué")
        self._refresh_all()
