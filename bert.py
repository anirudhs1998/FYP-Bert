import pickle
import neuralcoref
import spacy

nlp = spacy.load('en_core_web_sm')
neuralcoref.add_to_pipe(nlp)

with open('cnn_dataset.pkl', 'rb') as f:
    data = pickle.load(f)

story_count = len(data)

for j in range(story_count):
    #convert list of sentences to paragraph
    combined_story = '. '.join(data[j]['story'])
    doc = nlp(combined_story)._.coref_resolved
    doc = nlp(doc)
    data[j]['story'] = [c.string.strip() for c in doc.sents if 600 > len(c.string.strip()) > 40]
    
#print(resolved_story[0]['story'])
start = "[CLS] "
end = " [SEP]"
f = open("error.txt","a")

# Add [CLS] and [SEP] token at start and end of each sentence
for j in range(story_count):
    
    sentence_count = len(data[j]['story'])
    
    if sentence_count != 0:
        for i in range(sentence_count):
            data[j]['story'][i] = start + data[j]['story'][i]+ end
    else:
        f.write("error: " + str(j) + "\n")
        
f.close() 

from sklearn.cluster import KMeans
from typing import List
import numpy as np
from numpy import ndarray
import torch
from transformers import BertTokenizer, BertModel, BertConfig
import logging
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Load pre-trained model (weights)
model = BertModel.from_pretrained('bert-base-uncased', output_hidden_states=True)

# Put the model in "evaluation" mode, meaning feed-forward operation.
model.eval()

def extract_embeddings(sentence) -> ndarray:
    # Tokenize our sentence with the BERT tokenizer.
    tokenized_text = tokenizer.tokenize(sentence)

    # Map the token strings to their vocabulary indeces.
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)

    # Print out the tokens.
    #print (tokenized_text)

    # Display the words with their indices.
    #for tup in zip(tokenized_text, indexed_tokens):
    #    print('{:<12} {:>6,}'.format(tup[0], tup[1]))
        
    segments_ids = [1] * len(tokenized_text)

    # Convert inputs to PyTorch tensors
    tokens_tensor = torch.tensor([indexed_tokens])
    segments_tensors = torch.tensor([segments_ids])

    with torch.no_grad():
        outputs = model(tokens_tensor)

    #Sequence of hidden-states at the last layer of the model.
    #torch.FloatTensor of shape (batch_size, sequence_length, hidden_size)
    last_hidden_states = outputs[0]

    #Last layer hidden-state of the first token of the sequence (classification token) further processed by a Linear layer and a Tanh activation function. 
    #This output is usually not a good summary of the semantic content of the input, It is better with averaging or pooling the sequence of hidden-states for the whole input sequence.
    #torch.FloatTensor: of shape (batch_size, hidden_size)
    pooler_output = outputs[1]

    #Hidden-states of the model at the output of each layer plus the initial embedding outputs.
    #torch.FloatTensor (one for the output of the embeddings + one for the output of each layer) of shape (batch_size, sequence_length, hidden_size)
    hidden_states = outputs[2]

    embedding_output = hidden_states[0]
    attention_hidden_states = hidden_states[1:]

    pooled = hidden_states[-2].mean(dim=1)

    return pooled

def create_matrix(content) -> ndarray:
    return np.asarray([
        np.squeeze(extract_embeddings(t).data.numpy())
        for t in content
    ])

def run_clusters(content, ratio=0.2, algorithm='kmeans') -> List[str]:
    features = create_matrix(content)
    hidden_args = cluster_features(features, ratio)
    return [content[j] for j in hidden_args]

def cluster_features(features, ratio: float = 0.2) -> List[int]:
        """
        Clusters sentences based on the ratio
        :param ratio: Ratio to use for clustering
        :return: Sentences index that qualify for summary
        """

        k = 1 if ratio * len(features) < 1 else int(len(features) * ratio)
        model = get_model(k).fit(features)
        centroids = get_centroids(model)
        cluster_args = find_closest_args(centroids, features)
        sorted_values = sorted(cluster_args.values())
        return sorted_values

def get_model(k: int):
        """
        Retrieve clustering model
        :param k: amount of clusters
        :return: Clustering model
        """
        return KMeans(n_clusters=k, random_state=12345)

def get_centroids(model):
    """
    Retrieve centroids of model
    :param model: Clustering model
    :return: Centroids
    """
    return model.cluster_centers_

def find_closest_args(centroids: np.ndarray, features):
    """
    Find the closest arguments to centroid
    :param centroids: Centroids to find closest
    :return: Closest arguments
    """

    centroid_min = 1e10
    cur_arg = -1
    args = {}
    used_idx = []

    for j, centroid in enumerate(centroids):

        for i, feature in enumerate(features):
            value = np.linalg.norm(feature - centroid)

            if value < centroid_min and i not in used_idx:
                cur_arg = i
                centroid_min = value

        used_idx.append(cur_arg)
        args[j] = cur_arg
        centroid_min = 1e10
        cur_arg = -1

    return args

sentences_summary = run_clusters(data[0]['story'],0.2,'kmeans')
summary = ' '.join(sentences_summary)
print(summary)