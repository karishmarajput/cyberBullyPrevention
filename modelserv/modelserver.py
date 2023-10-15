from fastapi import FastAPI
from pydantic import BaseModel
import warnings
warnings.filterwarnings('ignore')
import sys
import numpy as np
import random as rnfv
import pandas as pd
from sklearn.utils.multiclass import unique_labels
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from torch.optim import Adam
from torch.nn.utils import clip_grad_norm_
from torch.utils.data import DataLoader, Dataset
from torchsummary import summary
from torch.nn.utils.rnn import pad_sequence
from torchmetrics import ConfusionMatrix, F1Score
from pytorch_pretrained_bert import BertModel
from pytorch_pretrained_bert import BertTokenizer

batch_size = 8  # Batch size

# Preprocessing
word_max_len = 64

# Model
h1 = 768
h2 = 128
drop_out_rate = 0.2

# Training
epochs = 20  # Train epochs
learning_rate = 3e-6
class_num = 3
class Bert_Aggression_Identification_Model(nn.Module):
    def __init__(self, h1, h2, class_num, drop_out_rate):
        super(Bert_Aggression_Identification_Model, self).__init__()

        self.bert = BertModel.from_pretrained('bert-base-uncased')

        self.dropout = nn.Dropout(drop_out_rate)
        self.linear1 = nn.Linear(h1, h2)
        self.linear2 = nn.Linear(h2, class_num)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax()
    
    def forward(self, tokens, masks):
        _, pooled_output = self.bert(tokens, attention_mask=masks, output_all_encoded_layers=False)
        d = self.dropout(pooled_output)
        x = self.relu(self.linear1(d))
        proba = self.softmax(self.linear2(x))
        
        return proba

model = Bert_Aggression_Identification_Model(h1, h2, class_num, drop_out_rate)
model.load_state_dict(torch.load("model.pt",map_location='cpu'))
def preprocess(text):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)
    tokens = list(map(lambda t: ['[CLS]'] + tokenizer.tokenize(t) + ['[SEP]'], text))
    tokens_ids = pad_sequences(list(map(tokenizer.convert_tokens_to_ids, tokens)), maxlen=word_max_len, truncating="post", padding="post", dtype="int")
    masks = [[float(i > 0) for i in ii] for ii in tokens_ids]
    tokens_ids = torch.Tensor(tokens_ids).to(torch.int64)
    masks = torch.Tensor(masks).to(torch.int64)
    return tokens,tokens_ids,masks

app = FastAPI()
class TextData(BaseModel):
    text : str
@app.post("/classify")
async def classify_text(text_data : TextData):
    print(text_data.text)
    tokens,tokens_ids,masks = preprocess([text_data.text])
    pts = model.forward(tokens_ids,masks)
    numpy_array = pts.detach().numpy()
    CAG = numpy_array[0][0]
    OAG = numpy_array[0][1]
    NAG = numpy_array[0][2]
    arr = np.array([CAG,OAG,NAG])
    return {"is_cyb" : arr.tolist()}