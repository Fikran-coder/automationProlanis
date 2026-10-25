import pandas as pd

df6 = pd.read_csv("file/phs_batch_6.csv")
print("Original batch 6 rows:", len(df6))

# Split: first 28 rows to batch 6, last 2 rows to batch test
batch_6_28 = df6.iloc[:28]
batch_test = df6.iloc[28:]

print("New batch 6 rows:", len(batch_6_28))
print("Batch test rows:", len(batch_test))

batch_6_28.to_csv("file/phs_batch_6.csv", index=False)
batch_test.to_csv("file/phs_batch_test.csv", index=False)

print("Saved file/phs_batch_6.csv (28 rows)")
print("Saved file/phs_batch_test.csv (2 rows)")
