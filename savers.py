import os
from tkinter import filedialog, messagebox


class SaversMixin:
    # sauvg donne

    def save_csv(self):
        if self.donnees is None:
            messagebox.showwarning("Attention", "Aucune donnee a sauvegarder")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        try:
            self.donnees.to_csv(path, index=False)
            print("Fichier sauvegarde :", os.path.basename(path))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


# à faire: ajout de la sauvegarde separee du fichier filtre et des flags
