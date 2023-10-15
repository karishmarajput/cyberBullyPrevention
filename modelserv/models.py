from fastapi import FastAPI
from pydantic import BaseModel
import warnings
warnings.filterwarnings('ignore')
from models import Bert_Aggression_Identification_Model
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
from torch_snippets import *
from torchmetrics import ConfusionMatrix, F1Score
from pytorch_pretrained_bert import BertModel
from pytorch_pretrained_bert import BertTokenizer
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