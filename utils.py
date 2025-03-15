import re

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def search(query):
    vectorizer = pd.read_pickle("pkl_files/vectorizer_searchengine.pkl")
    titles = pd.read_pickle("pkl_files/book_titles.pkl")
    processed_query = re.sub("[^a-zA-Z0-9 ]", "", query.lower())
    query_vect = vectorizer.transform([processed_query])
    tfidf = vectorizer.fit_transform(titles["mod_title"])
    similarity_vect = cosine_similarity(query_vect, tfidf).flatten()
    indices = np.argpartition(similarity_vect, -10)[-10:]
    top_book_titles = titles.iloc[indices]
    return top_book_titles["book_id"].values #use a suitable return type