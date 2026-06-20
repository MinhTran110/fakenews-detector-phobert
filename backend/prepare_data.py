# -*- coding: utf-8 -*-
import pandas as pd
import os

df = pd.read_csv('C:/Users/Administrator/Downloads/full_dataset.csv')

df['text'] = df['title'].fillna('') + ' [SEP] ' + df['content'].fillna('')
df['label'] = df['is_fake'].astype(int)
df = df[['text', 'label']].dropna()

os.makedirs('data/raw', exist_ok=True)
df.to_csv('data/raw/dataset.csv', index=False, encoding='utf-8')

print('Saved:', df.shape)
print(df['label'].value_counts())