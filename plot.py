from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter

from logic import Result


class Plot:
    lines: Optional[pd.DataFrame] = None
    labels: Optional[list[tuple[datetime, str]]] = None

    def __init__(self):
        sns.set_theme()

    def add_results(self, results: list[tuple[str, str, list[Result]]]):
        timestamps = [item.time for result in results for item in result[2]]
        lefts = [item.left for result in results for item in result[2]]
        rights = [item.right for result in results for item in result[2]]
        self.lines = pd.DataFrame({
            "Time": timestamps * 2,
            "Sun": lefts + rights,
            "Side": ["Left"] * len(timestamps) + ["Right"] * len(timestamps),
        })

        # First time and departure name for each entry
        labels = [(result[2][0].time, result[0]) for result in results]
        # Last time and arrival time for last entry
        labels.append((results[-1][2][-1].time, results[-1][1]))
        self.labels = labels

    def show(self):
        ax = sns.lineplot(data=self.lines, x="Time", y="Sun", hue="Side")
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M', tz=ZoneInfo("Europe/Amsterdam")))
        for timestamp, label in self.labels:
            ax.axvline(x=timestamp, color='gray', linestyle='--', linewidth=1)
            ax.text(x=timestamp, y=ax.get_ylim()[1], s=label, rotation=90,
                    verticalalignment='top', fontsize=9)
        plt.show()