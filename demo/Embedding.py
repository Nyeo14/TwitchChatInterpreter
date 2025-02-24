#!/usr/bin/python
# -*- coding: utf-8 -*-
# this is the template learner, do not change this file but make copies and name them accordingly


# import all you need
import os 
from Utilities import * 
from Tokenizer_kit import * 
import json 
import gensim.models
import re 

import warnings 
warnings.filterwarnings(action='ignore')

# default parameters for training model
w2v_prms = {'min_count':20, 
            'size': 300, 
            'window': 7, 
            'iter': 5} 

# ======================================= objects and methods =======================================

# process data from json file
def Process_vod(data): 
    ''' This function takes a data object from json file, process it into a list of chats 
        chats are ignored if they are outside specified start and end time''' 
        
    _,chat_array,t_stamps,_ = Twitch_Comment_to_data(data['comments'], chat_window=1) 
    assert len(chat_array) == len(t_stamps) 
    return (chat_array, t_stamps)
   

# ignore streamer's greeting at the beginning
def Prompt_for_start_time(max_v:int) -> float: 
    ''' prompt for start time with a specified maximum, message is fixed, float is returned'''
    while(True):
        start_time = prompt_for_int('Enter a time (in seconds) when greeting ends, -1 for more info: ', min_v=-1, max_v=max_v) 

        if start_time==-1: 
            print(short_line)
            print('This is for excluding the beginning of the vod where people come in and greet') 
            print('No default value, you can enter any value as long as it is within vod limit') 
        else: 
            break 
    start_time = float(start_time) 
    return start_time 
        
    
# ignore streamer's goodbye at the end  
def Prompt_for_end_duration(max_v:int) -> float: 
    ''' prompt for an duration of ending, message is fixed, float is returned''' 
    while(True):    
        ending_duration = prompt_for_int('Enter expected ending duration (in seconds), -1 for more info: ', min_v=-1, max_v=max_v) 
        
        if ending_duration==-1: 
            print(short_line)
            print('This number is how long you expect ending and saying goodbye in the stream will be') 
            print('No default, you can enter any value as long as it is within vod limit') 
        else: 
            break 
    return float(ending_duration)


# cut greeting and goodbye
def Cut_ends(chat_array:np.array, t_stamps:np.array, start_time:float, end_time:float) -> list: 
    ''' This function cut ends of a chat list based on start time and end time''' 
    to_return = list() 
    for i in range(len(t_stamps)): 
        if start_time<t_stamps[i] and t_stamps[i]<end_time: 
            to_return.append(str(chat_array[i])) 
            
    return to_return 


# split a chat list into blocks and concatenate each block into a long string
def Thread_chats(chat_list:list, block_size=100) -> list: 
    ''' This function thread together chat messages, every block of chat is threaded into one sentence
        returns a list of threaded sentences'''
    to_return = list() 
    i=0
    while (i < len(chat_list)): 
        i+=block_size 
        sentence = chat_list[i-block_size:i] 
        sentence = Concatenate_str_list(str_list=sentence, splitter=' ') 
        to_return.append(sentence) 
        
    return to_return


# returns the vector of a passed word, does error checking
def Vector_of(word_vector, word:str) -> np.ndarray: 
    ''' This function go fetch the vector of passed word in word vector, 
        returns None if error happen''' 
    try: 
        to_return = word_vector[word] 
        return to_return 
    except: 
        return None 


# return cos similarity of two words in float
def Similarity_to_float(word_vector, w1:str, w2:str) -> float: 
    ''' This function returns the similarity of two words in passed vector, 
        if error happen, returns None''' 
    try: 
        to_return = word_vector.similarity(w1,w2) 
        return float(to_return) 
    except: 
        return None 


# return top_k most similar words to passed word
def Most_similar_to(word_vector, word:str, top_k:int) -> str: 
    ''' This function takes a word string, word vector object, and an int of how many to print out 
        returns a reader-friendly string to be printed out, or a special string when word is not in vocab''' 
    to_return = (short_line + os.linesep)
    to_return += f"{top_k} most similar words of [{word}] are: " + os.linesep  
    try: 
        for w,v in word_vector.most_similar(word, topn=top_k): 
            to_return += f">>[{w}]: {v} {os.linesep}" 
    except KeyError: 
        return f"Word [{word}] not in vocabulary" 
    
    return to_return


# compare two words and return result in formated string
def Compare_two_words(word_vector, w1:str, w2:str) -> str: 
    ''' Takes a word vector object and compute cosine similarity, return result as a str to print, 
        special string is returned if word not in vocab''' 
    try: 
        to_return = (short_line + os.linesep)
        to_return += (f"[{w1}]:[{w2}] has similarity {word_vector.similarity(w1, w2)}") 
        return to_return 
    except KeyError: 
        return "One of the words is not in vocab" 


# one mother method to check a passed w2v model
def Check_trained_model(word_vector:gensim.models.KeyedVectors): 
    ''' This is for main to call when user want to check a trained model''' 
    while(True): 
        print(short_line) 
        print(f"Vocabulary size is: [{len(word_vector.vocab)}]")
        print('Enter either one word to find most similar or two to find similarity, enter 0 to exit')
        sentence = prompt_for_str('Enter here: ') 
        if sentence=='0': 
            break 
        tokens = Embedding_tokenize(sentence=sentence) 
        
        if len(tokens)==1: 
            top_k = prompt_for_int('How many similar words do you want to see?: ', min_v=1) 
            ans = prompt_for_str("Do you want to see the vector? (y/n): ", options={'y','n'}) 
            word = tokens[0] 
            if ans=='y': print(Vector_of(word_vector=word_vector, word=word))
            print(Most_similar_to(word_vector=word_vector, word=word, top_k=top_k)) 
        elif len(tokens)==2: 
            w1 = tokens[0] 
            w2 = tokens[1] 
            print(Compare_two_words(word_vector=word_vector, w1=w1, w2=w2)) 
        else: 
            print("Tokens in your sentences are: ") 
            print(tokens) 
            print("number of tokens is not valid") 
            continue
    return 


# prompt for model parameters before training
def Prompt_for_training_params() -> dict: 
    ''' This model prompt for training parameters of word2vec, 
        if user decided to use default, returned value is None''' 
    while(True): 
        ans = prompt_for_str('Do you want to use deault params? (y/n/i) i for info: ', options={'y','n','i'}) 
        if ans=='i': 
            print(short_line)
            print(f"training a embedding requires these params:")
            print(f"[min count] for words, which is  lowest frequency to not ignore") 
            print(f"[size], which is the size of the vector") 
            print(f"[window], which is how many words count as context") 
            print(f"[iter], which is how many times the model go through the data") 
            print(f"Default params are: {os.linesep} {w2v_prms}")
            continue 
        elif ans=='y': 
            return None 
        elif ans=='n': 
            break 
        
    to_return = dict() 
    for param in w2v_prms.keys(): 
        ans = prompt_for_int(f"Enter your choice of [{param}] in int here: ", min_v=1) 
        to_return.update( {str(param):int(ans)} ) 
    return to_return 


# train a new w2v model on a big corpus once
def Train_new_model_once(params=w2v_prms) -> gensim.models.KeyedVectors: 
    ''' This model will prompt user to enter a collection of files first,
        and then train a word2vec model at once on the generated chat''' 
    print('Training new word2vec object...') 
    corpus = list() 
    while(True): 
        print(short_line)
        print("Enter json file path (WITH .json, enter 'fin' to finish training)")
        file_path = prompt_for_file('Enter here: ', exit_conds={'fin'}) 
        if file_path=='fin': 
            if len(corpus)==0: 
                print(f"at least one file has to be entered") 
                continue
            print(f"Finished entering")
            break 
        try:
            with open(file_path, encoding='utf-8') as f: 
                data = json.load(f) 
            chat_array, t_stamps = Process_vod(data=data)  
        except: 
            print('file entered not valid') 
            continue
        
        end_time = t_stamps[-1] 
        start_time = Prompt_for_start_time(max_v=int(end_time)) 
        ending_duration = Prompt_for_end_duration(max_v=end_time) 
        end_time -= ending_duration 
        if end_time <= start_time: 
            print('Time interval invalid, enter info again') 
            continue 
        
        raw_chats = Cut_ends(chat_array=chat_array, t_stamps=t_stamps, start_time=start_time, end_time=end_time) 
        raw_chats = Thread_chats(chat_list=raw_chats) 
        length = len(raw_chats) 
        prev_percent = 0
        for i,sentence in enumerate(raw_chats): 
            percent = int(10*i/length) 
            if percent>prev_percent: 
                print(f"Tokenizing chats, {percent*10}% done...") 
                prev_percent=percent
            corpus.append(Embedding_tokenize(sentence=sentence)) 
        continue 
    
    print('Training...') 
    model = gensim.models.Word2Vec(sentences=corpus, 
                                   min_count=params['min_count'], 
                                   size=params['size'], 
                                   window=params['window'], 
                                   iter=params['iter']) 
    print(f"Finished training, to check model, save file and check it after") 
    return model.wv 


# train a new m2v model on a collection of data sequentially
def Train_new_model_sequential(params=w2v_prms) -> gensim.models.KeyedVectors: 
    ''' This is for main to call when user want to train a new model sequentially on json files
        returns the keyed vector object as trained result''' 
    first_run=True  
    model = gensim.models.Word2Vec(min_count=params['min_count'], 
                                   size=params['size'], 
                                   window=params['window'], 
                                   iter=params['iter']) 
    print('Training new word2vec object...')
    while(True): 
        print(short_line)
        if not first_run:
            print('Keep training')
        print("Enter json file path (WITH .json, enter 'fin' to finish training, 'check' to check current model)")
        file_path = prompt_for_file('Enter here: ', exit_conds={'fin','check'}) 
        if file_path=='fin': 
            print(f"Finished training")
            break 
        elif file_path=='check': 
            print(long_line)
            if first_run: # error when no file is entered
                print(f"You have to enter at least one file to check") 
                continue
            Check_trained_model(word_vector=model.wv) 
            continue
        try:
            with open(file_path, encoding='utf-8') as f: 
                data = json.load(f) 
            chat_array, t_stamps = Process_vod(data=data)  
        except: 
            print('file entered not valid') 
            continue
        
        end_time = t_stamps[-1] 
        start_time = Prompt_for_start_time(max_v=int(end_time)) 
        ending_duration = Prompt_for_end_duration(max_v=end_time) 
        end_time -= ending_duration 
        if end_time <= start_time: 
            print('Time interval invalid, enter info again') 
            continue 
        
        raw_chats = Cut_ends(chat_array=chat_array, t_stamps=t_stamps, start_time=start_time, end_time=end_time) 
        raw_chats = Thread_chats(chat_list=raw_chats) 
        chats_to_train = list() 
        prev_percent = 0 
        length=len(raw_chats)
        for i,sentence in enumerate(raw_chats): 
            percent = int(10*i/length) 
            if percent>prev_percent: 
                print(f"Tokenizing chats, {percent*10}% done...") 
                prev_percent=percent
            chats_to_train.append(Embedding_tokenize(sentence=sentence)) 
            
        print(f"Training...") 
        
        if(first_run): 
            model.build_vocab(chats_to_train) 
            first_run=False 
        else: 
            model.build_vocab(chats_to_train, update=True) 
            
        model.train(chats_to_train, total_examples=len(chats_to_train), epochs=model.epochs) 
        print(f"Finished training")
        continue
    
    return model.wv 


# save the w2v model
def Save_wv(word_vector): 
    ''' This function takes a keyed word vector and store is with a series of prompts'''
    kv_path = prompt_for_save_file(dir_path='word_vectors', f_format='.kv') 
    print(f"Saving file as {kv_path}")
    word_vector.save(kv_path) 
    print('File saved') 
    return 


# load in a w2v file
def Load_wv(file_path=None) -> gensim.models.KeyedVectors: 
    ''' This function is called by main to prompt for a keyed vector file 
        which is loaded and returned ''' 
    if file_path!=None: 
        to_return = gensim.models.KeyedVectors.load(file_path) 
        assert type(to_return)==gensim.models.KeyedVectors 
        return to_return 
    while(True): 
        file_path = prompt_for_file(f"Enter .kv file path (WITH .kv): ") 
        try:
            to_return = gensim.models.KeyedVectors.load(file_path) 
            assert type(to_return)==gensim.models.KeyedVectors
            break
        except: 
            print(f"error occurred while loading file {file_path}") 
            continue 
    return to_return 



# ====================================== end of objects and methods ====================================


def main(): 
    while(True): 
        print(long_line)
        print(f"Train new model sequentially ('trainS')? Or train at once ('trainO')? Or check existing model ('check')? Or exit ('exit')?") 
        ans = prompt_for_str(f"Enter here: ", options={'trainS', 'trainO','check','exit'}) 
        if ans=='trainS': 
            new_prms = Prompt_for_training_params() 
            if new_prms!=None: 
                w2v_prms.update(new_prms) 
            word_vector = Train_new_model_sequential() 
            Save_wv(word_vector=word_vector) 
            continue 
        elif ans=='trainO': 
            new_prms = Prompt_for_training_params() 
            if new_prms!=None: 
                w2v_prms.update(new_prms)
            word_vector=Train_new_model_once() 
            Save_wv(word_vector=word_vector) 
            continue
        elif ans=='check': 
            word_vector = Load_wv() 
            Check_trained_model(word_vector=word_vector) 
            continue 
        elif ans=='exit': 
            break 
        
    return 


# ====================================== user prompts =============================================== 


if __name__ == '__main__': 
    main() 
    exit(0) 