import csv
import sys
import pandas as pd

from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from csv_data_writters import FEATURES as FEATURES

TEST_SIZE = 0.4

# Brawler name are currently strings, tell catboost where these are so that it can handle them
PLAYERS_PER_MATCH = 6
CAT_FEATURES_INDICES = [x*len(FEATURES) for x in range(PLAYERS_PER_MATCH)]

def main():
    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python train_model.py data")

    evidence, labels = load_data(sys.argv[1])

    # Convert evidence to a Pandas DataFrame
    X = pd.DataFrame(evidence)
    y = labels

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE
    )

    model = CatBoostClassifier(
        iterations=200,
        learning_rate=0.1,
        depth=6,
        verbose=10
    )

    model.fit(X_train, y_train, cat_features=CAT_FEATURES_INDICES)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"\nModel Evaluation:")
    print(f"Accuracy: {accuracy * 100:.2f}%")

    importances = model.get_feature_importance()
    feature_names = model.feature_names_

    df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    })

    df = df.sort_values(by="importance", ascending=False)

    print(df.to_string(index=False))

    model.save_model("model1.cbm")

def load_data(file_name=None):
    if file_name is None:
        raise ValueError

    with open(file_name) as f:
        reader = csv.reader(f)

        evidence = []
        labels = []

        for row in reader:
            match_evidence = []
            for i in range(PLAYERS_PER_MATCH):
                base = i * len(FEATURES)
                match_evidence.extend([
                    row[base],          # Brawler
                    int(row[base + 1]), # Wins
                    int(row[base + 2]), # Prestige
                    int(row[base + 3])  # Highest ranked elo
                ])
            
            evidence.append(match_evidence)
            labels.append([row[-1]])
    
    return (evidence, labels)
    
if __name__ == "__main__":
    main()