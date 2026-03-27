import os
import pandas as pd

from tkinter import filedialog, messagebox


class LoaderMixin:
    #Charge, recharge ou ferme un fichier CSV SMPS.
    def load_csv(self):
        
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All", "*.*")])
        if not path:
            return
        
        try:
            df = pd.read_csv(path)

            # convertir datetime
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

            # convertir concentration + gere les cases vides
            df["cpc_conc"] = pd.to_numeric(df["cpc_conc"], errors="coerce")

            # convertir (gere les cases vides)
            df["smps_concTotal"] = pd.to_numeric(df["smps_concTotal"], errors="coerce")

            #Convertit les 133 colonnes de bins en nombres , leCSV a toutes ces colonnes vides sur les premiere lignes. 
            bin_cols = [c for c in df.columns if c.startswith("smps_d_")]
            df[bin_cols] = df[bin_cols].apply(pd.to_numeric, errors="coerce")

            #Crée les colonnes de flags si elles nexistent pas dans le CSV
            if "smps_flag" not in df.columns: df["smps_flag"] = 0
            if "pollution_flag" not in df.columns: df["pollution_flag"] = 0

            #Supprime les lignes sans date valide
            df = df.dropna(subset=["datetime"])   # date valide
            df = df[df["pollution_flag"] == 0]    # enlever pollution


            # sauvegarde
            self.df = df
            self.df_original = df.copy()
            self.current_file = path

            print("Fichier chargé :", os.path.basename(path))

        except Exception as e:
            messagebox.showerror("Erreur", str(e))


    def reload_csv(self):   
        if not self.current_file:
            return
        try:
            df = pd.read_csv(self.current_file)
            df["datetime"]       = pd.to_datetime(df["datetime"], errors="coerce")
            df["cpc_conc"]       = pd.to_numeric(df["cpc_conc"], errors="coerce")
            df["smps_concTotal"] = pd.to_numeric(df["smps_concTotal"], errors="coerce")
            bin_cols = [c for c in df.columns if c.startswith("smps_d_")]
            df[bin_cols] = df[bin_cols].apply(pd.to_numeric, errors="coerce")
            df = df.dropna(subset=["datetime"])
            df = df[df["pollution_flag"] == 0]
            self.df = df
            self.df_original = df.copy()
            print("Fichier rechargé :", os.path.basename(self.current_file))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    
    
    def close_file(self):
        self.df = self.df_original = self.current_file = None
        print("Fichier ferme")      
