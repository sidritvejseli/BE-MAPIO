import numpy as np
import matplotlib.dates as mdates
import matplotlib.colors as plc
import matplotlib.pyplot as plt
import tkinter as tk
import pandas as pd

import matplotlib.pyplot as plt


class Graphe2D:
    def __init__(self):
        self.fig, self.ax = plt.subplots()

    def plot_day(self, df, day):
        df_day = df[df["datetime"].dt.date == day]

        self.ax.clear()
        self.ax.scatter(df_day["datetime"], df_day["smps_concTotal"])
        self.ax.set_title(f"Jour : {day}")
        self.ax.tick_params(axis='x', rotation=45)

        self.ax.scatter(
            df_day["datetime"],
            df_day["smps_concTotal"],
            s=1,
            alpha=0.7,
            color="tab:blue"
        )

        self.ax.grid(True, linestyle="--")
        self.fig.autofmt_xdate()
        