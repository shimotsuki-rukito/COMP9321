import pandas as pd
import numpy as np
import sys
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, accuracy_score, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


def read_tsv(file):
    return pd.read_csv(file, delimiter='\t')


def preprocess(df):
    columns_to_drop = ["ATM_Zone", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "ATM_Placement", "ATM_TYPE"]
    df = df.drop(columns_to_drop, axis=1)
    df["Day_Type"] = df["Day_Type"].map({"Working": 0, "Festival": 1})

    numeric_columns = df.select_dtypes(include=[np.number]).columns
    categorical_columns = df.select_dtypes(exclude=[np.number]).columns

    for column in numeric_columns:
        imputer_mean = SimpleImputer(strategy='mean')
        df[column] = imputer_mean.fit_transform(df[[column]])

    for column in categorical_columns:
        imputer_mode = SimpleImputer(strategy='most_frequent')
        df[column] = imputer_mode.fit_transform(df[[column]])

    return df


def predict_revenue(df_train, df_test):
    X = df_train.drop("revenue", axis=1)
    y = df_train["revenue"]

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X, y)

    X_test = df_test.drop("revenue", axis=1)
    X_test = scaler.transform(X_test)
    y_pred = model.predict(X_test)

    return y_pred


def predict_rating(df_train, df_test):
    X = df_train.drop("rating", axis=1)
    y = df_train["rating"]

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    model = LogisticRegression()
    model.fit(X, y)

    X_test = df_test.drop("rating", axis=1)
    X_test = scaler.transform(X_test)
    y_pred = model.predict(X_test)

    return y_pred


def main():
    train_file = sys.argv[1]
    test_file = sys.argv[2]

    df_train = read_tsv(train_file)
    df_test = read_tsv(test_file)

    df_train = preprocess(df_train)
    df_test = preprocess(df_test)

    predicted_revenue = predict_revenue(df_train, df_test)
    predicted_rating = predict_rating(df_train, df_test)

    with open("z5414592.PART1.output.csv", "w") as f:
        f.write("predicted_revenue\n")
        for value in predicted_revenue:
            f.write(f"{int(value)}\n")

    with open("z5414592.PART2.output.csv", "w") as f:
        f.write("predicted_rating\n")
        for value in predicted_rating:
            f.write(f"{int(value)}\n")


if __name__ == "__main__":
    main()
