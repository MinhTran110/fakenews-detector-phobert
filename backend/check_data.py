import pandas as pd

df = pd.read_csv('C:/Users/Administrator/Downloads/full_dataset.csv')
print('Shape:', df.shape)
print()
print('Label distribution:')
print(df['is_fake'].value_counts())
print()
n_fake = df['is_fake'].sum()
n_real = len(df) - n_fake
print(f'Fake: {n_fake} ({n_fake/len(df):.1%})')
print(f'Real: {n_real} ({n_real/len(df):.1%})')
print()
print('Null values:')
print(df[['title','content','is_fake']].isnull().sum())
