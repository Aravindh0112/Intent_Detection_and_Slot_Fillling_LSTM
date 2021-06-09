# -*- coding: utf-8 -*-
"""LSTM_ATIS_Intent.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wLKlr8GtpnzNib45pixNkBMJbiTtohOE
"""

pip freeze > requirements.txt

import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.lancaster import LancasterStemmer
import nltk
import re
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM, Bidirectional, Embedding, Dropout
from keras.callbacks import ModelCheckpoint

def load_dataset(filename):
  df = pd.read_csv(filename, encoding = "latin1", names = ["Intent", "Sentence"])
  #df.head(10)
  print(df.head(10))
  intent = df["Intent"]
  unique_intent = list(set(intent))
  sentences = list(df["Sentence"])
  
  return (intent, unique_intent, sentences)

intent, unique_intent, sentences = load_dataset("atis_intents_train.csv")

print(sentences[:5])

"""***PREPROCESSING***"""

nltk.download("stopwords")
nltk.download("punkt")

stemmer = LancasterStemmer()

def cleaning(sentences):
  words = []
  for s in sentences:
    clean = re.sub(r'[^ a-z A-Z 0-9]', " ", s)
    w = word_tokenize(clean)
    #stemming
    words.append([i.lower() for i in w])
    
  return words

cleaned_words = cleaning(sentences)
print(len(cleaned_words))
print(cleaned_words[:2])

def create_tokenizer(words, filters = '!"#$%&()*+,-./:;<=>?@[\]^_`{|}~'):
  token = Tokenizer(filters = filters)
  token.fit_on_texts(words)
  return token

def max_length(words):
  return(len(max(words, key = len)))

word_tokenizer = create_tokenizer(cleaned_words)
vocab_size = len(word_tokenizer.word_index) + 1
max_length = max_length(cleaned_words)

print("Vocab Size = %d and Maximum length = %d" % (vocab_size, max_length))

def encoding_doc(token, words):
  return(token.texts_to_sequences(words))

encoded_doc = encoding_doc(word_tokenizer, cleaned_words)

def padding_doc(encoded_doc, max_length):
  return(pad_sequences(encoded_doc, maxlen = max_length, padding = "post"))

padded_doc = padding_doc(encoded_doc, max_length)

padded_doc[:5]

print("Shape of padded docs = ",padded_doc.shape)

output_tokenizer = create_tokenizer(unique_intent, filters = '!"#$%&()*+,-/:;<=>?@[\]^`{|}~')

output_tokenizer.word_index

encoded_output = encoding_doc(output_tokenizer, intent)

import numpy as np
encoded_output = np.array(encoded_output).reshape(len(encoded_output), 1)

encoded_output.shape

"""***ONE HOT ENCODING***"""

def one_hot(encode):
  o = OneHotEncoder(sparse = False)
  return(o.fit_transform(encode))

output_one_hot = one_hot(encoded_output)

output_one_hot.shape

from sklearn.model_selection import train_test_split

train_X, val_X, train_Y, val_Y = train_test_split(padded_doc, output_one_hot, shuffle = True, test_size = 0.2)

print("Shape of train_X = %s and train_Y = %s" % (train_X.shape, train_Y.shape))
print("Shape of val_X = %s and val_Y = %s" % (val_X.shape, val_Y.shape))

"""***LSTM MODEL CREATION***"""

def create_model(vocab_size, max_length):
  model = Sequential()
  model.add(Embedding(vocab_size, 128, input_length = max_length, trainable = False))
  model.add(Bidirectional(LSTM(128)))
#   model.add(LSTM(128))
  model.add(Dense(32, activation = "relu"))
  model.add(Dropout(0.5))
  model.add(Dense(8, activation = "softmax"))
  
  return model

model = create_model(vocab_size, max_length)

model.compile(loss = "categorical_crossentropy", optimizer = "adam", metrics = ["accuracy"])
model.summary()

filename = 'model.h5'
checkpoint = ModelCheckpoint(filename, monitor='val_loss', verbose=1, save_best_only=True, mode='min')

hist = model.fit(train_X, train_Y, epochs = 100, batch_size = 32, validation_data = (val_X, val_Y), callbacks = [checkpoint])

model = load_model("model.h5")

def predictions(text):
  clean = re.sub(r'[^ a-z A-Z 0-9]', " ", text)
  test_word = word_tokenize(clean)
  test_word = [w.lower() for w in test_word]
  test_ls = word_tokenizer.texts_to_sequences(test_word)
  #print(test_word)
  #Check for unknown words
  if [] in test_ls:
    test_ls = list(filter(None, test_ls))
    
  test_ls = np.array(test_ls).reshape(1, len(test_ls))
 
  x = padding_doc(test_ls, max_length)
  
  pred = model.predict(x)

  return pred

def get_final_intent(pred, classes):

  predictions = pred[0]
 
  classes = np.array(classes)
  ids = np.argsort(-predictions)
  classes = classes[ids]
  predictions = -np.sort(-predictions)
  score=0
  max=0
  for i in range(pred.shape[1]):
    #print()

    if predictions[i]>max:
      max=predictions[i]
      score=i

  return classes[score],predictions[score]
  
    
    #print("%s has confidence score : %s" % (classes[i], (predictions[i])))
    #print()
  
  #print('Intent : ',classes[score])
  #print('Confidence Score :',predictions[score])
  #print()
  #print()
  #return classes[score]

"""***TRUE-POSITIVE RATE EVALUATION***"""

#TruePositive Rate on testData_ATIS

dfs=pd.read_csv('testDataInCSV.csv')
tp=0
for i in range(0,len(dfs)):
  utterance=dfs._get_value(i,'Sentence')
  pred=predictions(utterance)
  x=get_final_intent(pred,unique_intent)
  label=dfs._get_value(i,'Intent')
  if x==label:
    tp=tp+1

print('Number of True Positives :',tp)
tpr=(tp)/(len(dfs))
print('True Positive Rate:',tpr)

dfs.head(10)

"""***PREDICTING THE INTENT CLASS***"""

query='how much does it cost for a single person to travel from chennai to mumbai'
pred = predictions(query)
class_name,conf_score=get_final_intent(pred, unique_intent)

print(query)
print('Intent : ',class_name)
print('Confidence Score :',conf_score)

query='show me the flights available at the new delhi ariport on thursday'
pred = predictions(query)
class_name,conf_score=get_final_intent(pred, unique_intent)

print(query)
print('Intent : ',class_name)
print('Confidence Score :',conf_score)

query='what is the abbreviation of abn'
pred=predictions(query)
class_name,conf_score=get_final_intent(pred,unique_intent)

print(query)
print('Intent : ',class_name)
print('Confidence Score :',conf_score)

"""***TRAINING AND VALIDATION ACCURACY GRAPH PLOTS***"""

plt.plot(hist.history['accuracy'])
plt.plot(hist.history['val_accuracy'])
plt.title('Training and Validation Accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'valid'], loc='upper left')
plt.show()

"""***TRAINING AND VALIDATION LOSS GRAPH PLOTS***"""

plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.title('Training and Validation Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'valid'], loc='upper left')
plt.show()