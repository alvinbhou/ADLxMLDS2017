import numpy as np
import pandas as pd
import os, sys
import pickle
import json
import functools
import operator
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from sklearn.externals import joblib
from keras.utils import to_categorical
from keras.models import Model
from keras.layers import Input, LSTM, Dense, Permute, Reshape, RepeatVector, Activation
from keras.models import Sequential, load_model, model_from_json
from keras.models import model_from_json


def loadData(MAX_WORDS):
    TRAIN_LABEL_PATH = "MLDS_hw2_data/training_label.json"
    with open(TRAIN_LABEL_PATH) as data_file:    
        y_data = json.load(data_file)
    
    videoId = []
    videoSeq = []
    for y in y_data:
        for idx, cap in enumerate(y['caption']):
            cap = "<bos> " + cap + " <eos>"
            videoId.append(y['id'])
            videoSeq.append(cap)
            
    
    TRAIN_FEATURE_DIR = "./MLDS_hw2_data/training_data/feat/"
    x_data = {}
    for filename in os.listdir(TRAIN_FEATURE_DIR):
        f = np.load(TRAIN_FEATURE_DIR + filename)
        x_data[filename[:-4]] = f
        
    
    tokenizer = Tokenizer(num_words=MAX_WORDS)
    tokenizer.fit_on_texts(videoSeq)
    word_index = tokenizer.word_index   
    
    print ('Convert to index sequences.')
    train_sequences = tokenizer.texts_to_sequences(videoSeq)
    train_sequences = np.array(train_sequences)
   

    train_sequences = pad_sequences(train_sequences, padding='post',truncating='post')
    print(train_sequences.shape)
    max_seq_length = train_sequences.shape[1]
   
    
    
  
    print(train_sequences.shape)
    filesize = len(train_sequences)
    
    encoder_input_data = []
    decoder_input_data = []
    decoder_target_data = []

    X_data = []
    y_data = []
    vCount = 0
    curFilename = videoId[0]
    for idx in  range(0,filesize):
        if(videoId[idx] == curFilename):
            vCount = vCount + 1
            if(vCount > 3):
                continue
        else:
            vCount = 1
            curFilename = videoId[idx]
        encoder_input_data.append(x_data[videoId[idx]])
        y = to_categorical(train_sequences[idx], MAX_WORDS)
        decoder_input_data.append(y[:-1])
        decoder_target_data.append(y[1:])
    encoder_input_data = np.array(encoder_input_data)
    decoder_input_data = np.array(decoder_input_data)
    decoder_target_data = np.array(decoder_target_data)
    return [encoder_input_data, decoder_input_data], decoder_target_data, tokenizer



# load data
# encoder_input_data = None
# decoder_data = None
# tokinzer = None
# with open('data/X_data1500.jlib', 'rb') as file:
#     encoder_input_data = joblib.load(file)
#     print(encoder_input_data.shape)
# with open('data/y_data1500_post.jlib', 'rb') as file:
#     decoder_data = joblib.load(file)
#     print(decoder_data.shape)
# with open('data/tokinzer1500_post', 'rb') as file:
#     tokinzer = joblib.load(file)
#     print(len(tokinzer.word_index))
# decoder_input_data = []
# decoder_target_data = []
# for e in decoder_data:
#     i = e[:-1]
#     o = e[1:]
#     decoder_input_data.append(i)
#     decoder_target_data.append(o)
# decoder_input_data = np.array(decoder_input_data)
# decoder_target_data = np.array(decoder_target_data)


import keras.layers.merge as merge
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers import Flatten
import keras
num_encoder_tokens = 4096
num_decoder_tokens = 2048
latent_dim = 512

[encoder_input_data, decoder_input_data], decoder_target_data, tokenizer = loadData(num_decoder_tokens)
print(encoder_input_data.shape)
print(decoder_input_data.shape)

batch_size = 320
epochs = 100
TIME_STEPS_ENCODER = 80
DECODER_MAX_LENGTH = decoder_input_data.shape[1]

def attention_3d_block(inputs):
    
    # inputs.shape = (batch_size, time_steps, input_dim)
    print(inputs.shape)
    input_dim = int(inputs.shape[2])
    print(input_dim)
    a = Permute((2, 1))(inputs)
    #     a = Reshape((input_dim, TIME_STEPS_ENCODER))(a) # this line is not useful. It's just to know which dimension is what.
    a = Dense(DECODER_MAX_LENGTH, name='softmax_dense')(a)
    #     if SINGLE_ATTENTION_VECTOR:
    #         a = Lambda(lambda x: K.mean(x, axis=1), name='dim_reduction')(a)
    #         a = RepeatVector(input_dim)(a)
    a_probs = Permute((2, 1), name='attention_vec')(a)
    a_probs = Dense(num_decoder_tokens, name='dim2_num_of_decoders', activation='softmax')(a_probs)
    #     output_attention_mul = merge([inputs, a_probs], name='attention_mul', mode='mul')
    return a_probs

# Define an input sequence and process it.
encoder_inputs = Input(shape=(TIME_STEPS_ENCODER, num_encoder_tokens), name="encoder_inputs")
encoder = LSTM(latent_dim, return_state=True,return_sequences=True, name='endcoder_lstm')
encoder_output, state_h, state_c = encoder(encoder_inputs)
# We discard `encoder_outputs` and only keep the states.
encoder_states = [state_h, state_c]
encoder_outputs = [encoder_output, state_h, state_c]


# attention = keras.layers.Permute((2,1))(encoder_output)
# attention = keras.layers.Dense(TIME_STEPS_ENCODER, activation='softmax')(attention)
# attention = keras.layers.Permute((2,1))(attention)
# hidden = keras.layers.Multiply()([encoder_output, attention])
# hidden = keras.layers.Permute((2,1))(hidden)
# hidden = keras.layers.Dense(DECODER_MAX_LENGTH, activation='relu')(hidden)
# hidden = keras.layers.Permute((2,1))(hidden)
# hidden = keras.layers.Dense(num_decoder_tokens, activation='relu')(hidden)

# attention_inputs = Input(shape=(TIME_STEPS_ENCODER, latent_dim))
# at = Permute((2, 1))(attention_inputs)
# at = Dense(TIME_STEPS_ENCODER, activation='softmax',name='dense')(at)
# at = Permute((2, 1), name='attention_vec')(at)
# output_attention_mul = merge([attention_inputs, at], name='attention_mul', mode='mul')
# hidden = keras.layers.Permute((2,1))(output_attention_mul)
# hidden = keras.layers.Dense(DECODER_MAX_LENGTH,activation='relu')(hidden)
# hidden = keras.layers.Permute((2,1))(hidden)
# hidden = keras.layers.Dense(num_decoder_tokens,activation='relu')(hidden)

# attention_model = Model(attention_inputs, hidden, name='attention_model')
# attention_model.summary()


# encoder_output_as_input = Input(shape=(TIME_STEPS_ENCODER, latent_dim))
# attention_result_as_input = Input(shape=(TIME_STEPS_ENCODER, latent_dim))
# hidden = merge([encoder_output_as_input, attention_result_as_input], name='attention_mul', mode='mul')
# hidden = keras.layers.Permute((2,1))(hidden)
# hidden = keras.layers.Dense(DECODER_MAX_LENGTH, activation='relu')(hidden)
# hidden = keras.layers.Permute((2,1))(hidden)
# hidden_output = keras.layers.Dense(num_decoder_tokens, activation='relu')(hidden)
# hidden_model = Model([encoder_output_as_input, attention_result_as_input], hidden_output, name='hidden_layers_model')
# hidden_model.summary()


# Set up the decoder, using `encoder_states` as initial state.
decoder_inputs = Input(shape=(DECODER_MAX_LENGTH, num_decoder_tokens), name= "decoder_inputs")
decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True, name='decoder_lstm')
decoder_outputs, _, _ = decoder_lstm(decoder_inputs,
                                     initial_state=encoder_states)
decoder_dense = Dense(num_decoder_tokens, activation='relu', name='decoder_relu')
decoder_outputs = decoder_dense(decoder_outputs)
# output_attention_mul = keras.layers.Multiply()([decoder_outputs, hidden_output])
# hidden_prob = hidden_model([encoder_output, attention_result])
# result = keras.layers.Multiply()([decoder_outputs, hidden])
# attention_result = attention_model(encoder_output)
# result = merge([decoder_outputs, attention_result], name='output_mul', mode='mul')


# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
model.summary()
# plot_model(model, to_file='model.png', show_shapes=True)


earlystopping = EarlyStopping(monitor='val_loss', patience = 4, verbose=1, mode='min')
# checkpoint = ModelCheckpoint(filepath=  './models/model1_best.h5',
#                             verbose=1,
#                             save_best_only=True,
#                             save_weights_only=False,
#                             monitor='val_loss',
#                                 mode='min')
# Run training
opt = keras.optimizers.adam(lr = 0.0007)

model.compile(metrics=['accuracy'], optimizer=opt, loss='categorical_crossentropy')
try:
    pass
    model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
          batch_size=batch_size,
          epochs=epochs,
          validation_split=0.15,
             callbacks=[earlystopping])
except KeyboardInterrupt:
    print("\nW: interrupt received, stopping")
finally:
    
    pass

path, dirs, files = os.walk("./models/").__next__()
MODEL_NUM = str(int(len(dirs)+1))

directory = os.path.join('models',MODEL_NUM)
if not os.path.exists(directory):
    os.makedirs(directory)

    
encoder_model = Model(encoder_inputs, encoder_states)

decoder_state_input_h = Input(shape=(latent_dim,))
decoder_state_input_c = Input(shape=(latent_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
decoder_outputs, state_h, state_c = decoder_lstm(
    decoder_inputs, initial_state=decoder_states_inputs)
decoder_states = [state_h, state_c]
decoder_outputs = decoder_dense(decoder_outputs)

decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)

encoder_model.summary()
decoder_model.summary()




# decode_sequence(input_seq, encoder_model,decoder_model )
encoder_model.save(os.path.join(directory, 'encoder_model.h5'))
decoder_model.save_weights(os.path.join(directory, 'decoder_model_weights.h5'))
with open(os.path.join(directory,'tokinzer'+ str(num_decoder_tokens) ),'wb') as file:
    joblib.dump(tokenizer, file)
# attention_model.save(os.path.join(directory, 'attention_model.h5'))
# hidden_model.save(os.path.join(directory, 'hidden_model.h5'))

def att_decode_model(num_encoder_tokens, num_decoder_tokens, latent_dim):
    decoder_inputs = Input(shape=(None, num_decoder_tokens))
    decoder_dense = Dense(num_decoder_tokens, activation='softmax')
    decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
    
    decoder_state_input_h = Input(shape=(latent_dim,))
    decoder_state_input_c = Input(shape=(latent_dim,))
    decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
    decoder_outputs, state_h, state_c = decoder_lstm(
        decoder_inputs, initial_state=decoder_states_inputs)
    decoder_states = [state_h, state_c]
    decoder_outputs = decoder_dense(decoder_outputs)
    decoder_model = Model(
        [decoder_inputs] + decoder_states_inputs,
        [decoder_outputs] + decoder_states)
    return decoder_model


def att_decode_sequence(input_seq, encoder_model, decoder_model, att_model, hid_model):
    return_seq, states_h, states_c = encoder_model.predict(input_seq)
    att_prob = att_model.predict(return_seq)
    hid_prob = hid_model.predict([return_seq, att_prob])
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    target_seq[0, 0, tokenizer.word_index['bos']] = 1
    stop_condition = False
    decoded_sentence = []
   
    seq_len = 0
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict(
            [target_seq] + [states_h, states_c])
       
       
        prob = hid_prob[0][seq_len]
        prob = prob.reshape((1,1,1024))
        
#         print(hid_prob.shape)
        
        # Sample a token
        out_prob = prob * output_tokens
        sampled_token_index = np.argmax(out_prob[0, -1, :])
        if sampled_token_index == 0:
            sampled_char = 'pad'
        else:
            sampled_char = list(tokenizer.word_index.keys())[list(tokenizer.word_index.values()).index(sampled_token_index)]
        decoded_sentence.append(sampled_char)

        # Exit condition: either hit max length
        # or find stop character.
        if ( 
           len(decoded_sentence) > 50):
            stop_condition = True
            seq_length = 0

        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, num_decoder_tokens))

        # Update states
        states_value = [h, c]
        seq_len = seq_len + 1

    return decoded_sentence

def decode_model(num_encoder_tokens, num_decoder_tokens, latent_dim):
    decoder_inputs = Input(shape=(None, num_decoder_tokens))
    decoder_dense = Dense(num_decoder_tokens, activation='softmax')
    decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
    
    decoder_state_input_h = Input(shape=(latent_dim,))
    decoder_state_input_c = Input(shape=(latent_dim,))
    decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
    decoder_outputs, state_h, state_c = decoder_lstm(
        decoder_inputs, initial_state=decoder_states_inputs)
    decoder_states = [state_h, state_c]
    decoder_outputs = decoder_dense(decoder_outputs)
    decoder_model = Model(
        [decoder_inputs] + decoder_states_inputs,
        [decoder_outputs] + decoder_states)
    return decoder_model


def decode_sequence(input_seq, encoder_model, decoder_model):
    states_value = encoder_model.predict(input_seq)
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    target_seq[0, 0, tokenizer.word_index['bos']] = 1

    stop_condition = False
    decoded_sentence = []
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict(
            [target_seq] + states_value)

        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        if sampled_token_index == 0:
            sampled_char = ''
        else:
            sampled_char = list(tokenizer.word_index.keys())[list(tokenizer.word_index.values()).index(sampled_token_index)]
        decoded_sentence.append(sampled_char)

        # Exit condition: either hit max length
        # or find stop character.
        if (sampled_char == 'eos' or
           len(decoded_sentence) > 50):
            stop_condition = True

        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, num_decoder_tokens))
        target_seq[0, 0, sampled_token_index] = 1.

        # Update states
        states_value = [h, c]

    return decoded_sentence


def getX_test(path):   
    X_test = []
    X_test_filename = []
    for filename in os.listdir(path):
        f = np.load(os.path.join(path , filename))
        X_test.append(f)
        X_test_filename.append(filename[:-4])
    X_test = np.array(X_test)
    return X_test, X_test_filename




    
path, dirs, files = os.walk("./models/").__next__()
LOAD_MODEL_NUM = str(int(len(dirs)))
print(LOAD_MODEL_NUM)

with open('models/'+LOAD_MODEL_NUM+'/tokinzer' + str(num_decoder_tokens), 'rb') as file:
    tokenizer = joblib.load(file)
    print(len(tokenizer.word_index))

enc_model = load_model('models/'+LOAD_MODEL_NUM+'/encoder_model.h5')
# enc_model.summary()
dec_model = decode_model(num_encoder_tokens, num_decoder_tokens, latent_dim)
dec_model.load_weights('models/'+LOAD_MODEL_NUM+'/decoder_model_weights.h5')
# dec_model.summary()
# att_model = load_model('models/'+LOAD_MODEL_NUM+'/attention_model.h5')
# # att_model.summary()
# hid_model = load_model('models/'+LOAD_MODEL_NUM+'/hidden_model.h5')
# # hid_model.summary()
data_directory = "MLDS_hw2_data"
X_test, X_test_filename = getX_test(os.path.join(data_directory, "testing_data/feat/"))

# specail_vid = ["klteYv1Uv9A_27_33.avi", "5YJaS2Eswg0_22_26.avi", "UbmZAe5u5FI_132_141.avi", "JntMAcTlOF0_50_70.avi", "tJHUH9tpqPg_113_118.avi"]
# dirty
decode_seq = None
p_MAX = -1
def beam_search(decoder_model, target_seq, states_value, prob,  path, lens):
    global p_MAX
    global decode_seq
    node = 2
    output_tokens, h, c = decoder_model.predict(
        [target_seq] + states_value)
    output_tokens = output_tokens.reshape((num_decoder_tokens))
    sampled_token_index = output_tokens.argsort()[-node:][::-1]
    states_value = [h, c]
    for i in range(node):
        if sampled_token_index[i] == 0:
            sampled_char = ''
        else:
            sampled_char = list(tokenizer.word_index.keys())[list(tokenizer.word_index.values()).index(sampled_token_index[i])]
      
        if(sampled_char != 'eos' and lens <= 9):
            p = output_tokens[sampled_token_index[i]]
            prob_new = list(prob)
            prob_new.append(p)
            path_new = list(path)
            path_new.append(sampled_char)
            target_seq = np.zeros((1, 1, num_decoder_tokens))
            target_seq[0, 0, sampled_token_index[i]] = 1.
            beam_search(decoder_model, target_seq, states_value, prob_new, path_new, lens+1)
        else:
            p = output_tokens[sampled_token_index[i]]
            prob_new = list(prob)
            prob_new.append(p)
            p = functools.reduce(operator.mul, prob_new, 1)

            if(p > p_MAX):
                decode_seq = path
                p_MAX = p
    

def decode_sequence2(input_seq, encoder_model, decoder_model):
    states_value = encoder_model.predict(input_seq)
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    target_seq[0, 0, tokenizer.word_index['bos']] = 1
    beam_search(decoder_model, target_seq, states_value,[],[],0)
    return decode_seq

# specail_vid = ["klteYv1Uv9A_27_33.avi", "5YJaS2Eswg0_22_26.avi", "UbmZAe5u5FI_132_141.avi", "JntMAcTlOF0_50_70.avi", "tJHUH9tpqPg_113_118.avi"]

with open("result.csv", 'w') as file:
    for idx, x in enumerate(X_test): 
        # decoded_sentence = att_decode_sequence(x.reshape(-1, 80, 4096), enc_model,dec_model,att_model, hid_model)
        decoded_sentence = decode_sequence2(x.reshape(-1, 80, 4096), enc_model,dec_model)
        decode_str = []
        filter_string = ['bos', 'eos']
        unigram = {}
        bigram = {}
        prepositions = [ 'of']
        last_string = ""
        for idx2, c in enumerate(decoded_sentence):
            if c in unigram:
                unigram[c] += 1
            else:
                unigram[c] = 1
        
            
            # if(decoded_sentence[idx2-1] == c and idx2 > 0 and c != 'a'):
            #     continue

            if(c != 'a' and unigram[c]>= 3):
                continue
            # if(c in prepositions and unigram[c] >=3):
            #     continue
            if(c == 'a' and unigram[c] >=4):
                continue
            
            
            if c in filter_string:
                continue
            if len(c) > 0:
                decode_str.append(c)
            if idx2 > 0:
                last_string = c
        print(X_test_filename[idx]+'>', ' '.join(decode_str))
        file.write(X_test_filename[idx]+',')
        for d in decode_str:
            file.write(d + ' ')
        file.write('\n')
        
        # init p max
        p_MAX = -1
