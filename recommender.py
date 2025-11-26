# recommender.py
import pandas as pd
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from joblib import dump, load

MODEL_PATH = os.path.join(os.path.dirname(__file__), "dt_model.joblib")
DATA_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")

class Recommender:
    def __init__(self):
        self.model = None
        self.le_map = {}  # store label encoders for categorical features
        if os.path.exists(MODEL_PATH):
            self.model = load(MODEL_PATH)
            # load encoders (we store them as a small dict file? For simplicity, we'll retrain encoders on dataset)
            self._fit_encoders()
        else:
            self.train_model()

    def _fit_encoders(self):
        # Fit encoders on dataset (must match training)
        df = pd.read_csv(DATA_PATH)
        for col in ["type", "weather", "travel_type", "budget_level"]:
            le = LabelEncoder()
            le.fit(df[col].astype(str))
            self.le_map[col] = le

    def train_model(self):
        df = pd.read_csv(DATA_PATH)
        # Features: type, avg_cost, distance_km, open_hour, weather, travel_type, budget_level
        X = df[["type", "avg_cost", "distance_km", "open_hour", "weather", "travel_type", "budget_level"]].copy()
        y = df["name"]  # predict spot name directly (classification)

        # encode categorical columns
        for col in ["type", "weather", "travel_type", "budget_level"]:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            self.le_map[col] = le

        self.model = DecisionTreeClassifier(max_depth=6, random_state=1)
        self.model.fit(X, y)
        dump(self.model, MODEL_PATH)

    def _encode_input(self, input_dict):
        # input_dict should have keys matching features
        enc = {}
        for col in ["type", "weather", "travel_type", "budget_level"]:
            le = self.le_map.get(col)
            if le:
                # if unseen value, try append (transform will error); we handle unknowns by mapping to nearest existing
                val = str(input_dict.get(col, "unknown"))
                if val in le.classes_:
                    enc[col] = int(le.transform([val])[0])
                else:
                    # fallback to mode (0)
                    enc[col] = 0
            else:
                enc[col] = 0
        enc["avg_cost"] = float(input_dict.get("avg_cost", 0))
        enc["distance_km"] = float(input_dict.get("distance_km", 0))
        enc["open_hour"] = int(input_dict.get("open_hour", 12))
        return [enc["type"], enc["avg_cost"], enc["distance_km"], enc["open_hour"], enc["weather"], enc["travel_type"], enc["budget_level"]]

    def recommend(self, context, top_k=5):
        """
        context: dict containing keys:
           - type (e.g., "museum", "park", "temple")
           - avg_cost (float)
           - distance_km (float)
           - open_hour (int -> current hour in 24h)
           - weather (e.g., "sunny", "rainy")
           - travel_type (e.g., "solo","family","adventure")
           - budget_level (e.g., "low","medium","high")
        """
        if self.model is None:
            self.train_model()
        sample = self._encode_input(context)
        # sklearn decision tree predict_proba requires classifier with classes; we will get single prediction:
        pred = self.model.predict([sample])
        # For prototype, return the top match and also similar rows from dataset
        df = pd.read_csv(DATA_PATH)
        # simple similarity: score by matching categorical fields and closeness of cost/distance
        def score_row(row):
            s = 0
            s += 2 if str(row["type"]) == context.get("type") else 0
            s += 2 if str(row["weather"]) == context.get("weather") else 0
            s += 1 if str(row["travel_type"]) == context.get("travel_type") else 0
            # cost closeness
            s -= abs(float(row["avg_cost"]) - float(context.get("avg_cost", 0)))/50.0
            # distance closeness
            s -= abs(float(row["distance_km"]) - float(context.get("distance_km", 0)))/5.0
            # closeness to open hour
            s -= abs(int(row["open_hour"]) - int(context.get("open_hour", 12)))/6.0
            return s

        df["score"] = df.apply(score_row, axis=1)
        df_sorted = df.sort_values("score", ascending=False)
        results = df_sorted.head(top_k)[["name","type","avg_cost","distance_km","open_hour","weather","short_description"]].to_dict(orient="records")
        return results
