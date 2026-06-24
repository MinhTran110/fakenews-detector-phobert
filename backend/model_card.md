---
language: vi

tags:

  - text-classification

  - fake-news-detection

  - phobert

  - Vietnamese

license: mit

pipeline_tag: text-classification
---



\# PhoBERT Fake News Detector (Vietnamese)



Fine-tuned `vinai/phobert-base-v2` cho bài toán phát hiện tin giả tiếng Việt.



\## Kiến trúc



PhoBERT + Multi-Pooling (CLS + Mean + Max) + Dense + Sigmoid (binary classification)



Input text → PhoBERT (12 layers) → Pooling (2304 dim)



→ LayerNorm → Dense(512) → Dense(128) → Linear(1) → Sigmoid



→ P(fake) ∈ (0,1)



\## Kết quả (test set, 1,593 mẫu)



| Metric | Giá trị |

|---|---|

| F1-macro | 0.9754 |

| AUC-ROC | 0.9976 |

| Accuracy | 0.97 |

| Precision (Fake) | 0.95 |

| Recall (Fake) | 0.99 |



\## Cách dùng



```python

from huggingface\_hub import snapshot\_download

snapshot\_download(

&nbsp;   repo\_id="KawahakuBenu/fakenews-phobert-vi",

&nbsp;   local\_dir="checkpoints/best\_model"

)

```



Code đầy đủ (training, API, frontend):

https://github.com/MinhTran110/fakenews-detector-phobert



\## Dataset



10,617 mẫu tin tức tiếng Việt, cân bằng 46% fake / 54% real.



\## Training



\- GPU: Tesla T4 (Google Colab)

\- Epochs: 5 (early stopping tại epoch 4)

\- Optimizer: AdamW, differential LR (BERT 2e-5, head 1e-4)

\- Loss: BCEWithLogitsLoss với pos\_weight tự động

\- Thời gian: ~6 phút



\## Giới hạn



Model được train trên data crawl tự động, có thể có nhiễu nhãn. Kết quả chỉ mang tính tham khảo, không thay thế kiểm chứng từ nguồn uy tín.

