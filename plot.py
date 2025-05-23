from datetime import datetime
from pprint import pprint
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter

from logic import SegmentResult, Result


class Plot:
    lines: Optional[pd.DataFrame] = None
    labels: Optional[list[tuple[datetime, str, bool]]] = None

    def __init__(self):
        sns.set_theme()

    def add_results(self, results: list[Result]):
        timestamps = [item.time for result in results for item in result.items]
        lefts = [item.left for result in results for item in result.items]
        rights = [item.right for result in results for item in result.items]
        altitudes = [item.altitude for result in results for item in result.items]
        self.lines = pd.DataFrame({
            "Time": timestamps * 3,
            "Sun": lefts + rights + altitudes,
            "Side": ["Left"] * len(timestamps) + ["Right"] * len(timestamps) + ["Altitude"] * len(timestamps),
        })

        # First time and departure name for each entry
        labels = [(result.items[0].time, result.stop1, result.kop) for result in results]
        # Last time and arrival time for last entry
        labels.append((results[-1].items[-1].time, results[-1].stop2, False))
        self.labels = labels

    def show(self):
        plt.figure(figsize=(12, 6))
        ax = sns.lineplot(data=self.lines, x="Time", y="Sun", hue="Side")
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M', tz=ZoneInfo("Europe/Amsterdam")))
        ax.set_ylim(bottom=0)
        for timestamp, label, kop in self.labels:
            ax.axvline(x=timestamp, color='gray', linestyle='--', linewidth=1)
            ax.text(x=timestamp, y=ax.get_ylim()[1], s=label, rotation=90,
                    verticalalignment='top', fontsize=9, color='red' if kop else 'black')
        plt.show()