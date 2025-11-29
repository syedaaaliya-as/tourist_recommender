import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

class Recommender:

    def __init__(self):
        self.df = pd.read_csv(DATA_PATH, encoding="latin1", on_bad_lines="skip")
        self.df.columns = [c.strip().lower() for c in self.df.columns]

        self.df["avg_cost"] = (
            self.df["avg_cost"].astype(str)
            .str.replace("â\x82¹", "")
            .str.replace("₹", "")
            .str.replace(",", "")
            .str.strip()
        )
        self.df["avg_cost"] = pd.to_numeric(self.df["avg_cost"], errors="coerce")

        self.df["lat"] = pd.to_numeric(self.df["lat"], errors="coerce")
        self.df["lng"] = pd.to_numeric(self.df["lng"], errors="coerce")
        self.df["open_hour"] = pd.to_numeric(self.df["open_hour"], errors="coerce")

        self.df.dropna(subset=["lat", "lng"], inplace=True)

    def recommend(self, context, top_k=5):
        df = self.df.copy()

        if context.get("country"):
            df = df[df["country"].str.lower() == context["country"].lower()]
        if context.get("state"):
            df = df[df["state"].str.lower() == context["state"].lower()]
        if context.get("city"):
            df = df[df["city"].str.lower() == context["city"].lower()]
        if context.get("type"):
            df = df[df["type"].str.lower() == context["type"].lower()]

        if df.empty:
            return []

        user_lat = context.get("user_lat")
        user_lng = context.get("user_lng")

        if user_lat and user_lng:
            df["real_distance"] = df.apply(
                lambda r: haversine(float(user_lat), float(user_lng),
                                    float(r["lat"]), float(r["lng"])), axis=1)
        else:
            df["real_distance"] = 99999

        df["score"] = (
            -(df["avg_cost"] - float(context.get("avg_cost", 0))).abs() * 0.05 +
            -(df["real_distance"]) * 0.2
        )

        df = df.sort_values("score", ascending=False)

        cols = ["name", "type", "avg_cost", "real_distance", "short_description",
                "country", "state", "city", "lat", "lng"]
        return df.head(top_k)[cols].to_dict(orient="records")
