import csv
import sys
import pandas as pd

from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

TEST_SIZE = 0.4

def main():
    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python train_model.py data")

    evidence, labels = load_data(sys.argv[1])

    # Convert evidence to a Pandas DataFrame
    X = pd.DataFrame(evidence)
    y = labels

    # Brawler name are currently strings, tell catboost where these are so that it can handle them
    cat_features_indices = [2, 5, 8, 11, 14, 17]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE
    )

    model = CatBoostClassifier(
        iterations=200,
        learning_rate=0.1,
        depth=6,
        verbose=10
    )

    model.fit(X_train, y_train, cat_features=cat_features_indices)

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
            evidence.append([
                int(row[0]),  # P1 wins
                int(row[1]),  # P1 prestige
                row[2],       # P1 brawler

                int(row[3]),  # P2 wins
                int(row[4]),  # P2 prestige
                row[5],       # P2 brawler

                int(row[6]),  # P3 wins
                int(row[7]),  # P3 prestige
                row[8],       # P3 brawler

                int(row[9]),  # P4 wins
                int(row[10]), # P4 prestige
                row[11],      # P4 brawler

                int(row[12]), # P5 wins
                int(row[13]), # P5 prestige
                row[14],      # P5 brawler

                int(row[15]), # P6 wins
                int(row[16]), # P6 prestige
                row[17],      # P6 brawler
            ])
            labels.append([row[-1]])
    
    return (evidence, labels)
    
if __name__ == "__main__":
    main()