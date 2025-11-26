import csv
from math import log
import re
from nltk.stem import PorterStemmer

ALL_DATA = set()
ALL_OBJECTS = []

STEMMER = PorterStemmer()

# Source - https://gist.github.com/sebleier/554280
STOP_WORDS = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"}   

# Query stop words - more strict
QUERY_STOP_WORDS = {"i", "me", "my", "myself", "want", "to", "give", "would", "like", "provide", "show", "list", "find", "search", "provide", "game", "games", "title", "titles"}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    OKMAGENTA = '\033[35m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
   

class index_body():
    def __init__(self, token, doc_freq, postings):
        self.token = token
        self.doc_freq = doc_freq
        self.postings = postings
        self.idf = 0.0
        self.idf_smooth = 0.0
    
    def add_posting(self, doc_id, term_freq):
        self.postings[doc_id] = term_freq
        self.doc_freq = len(self.postings)
    
    def to_dict(self):
        return {
            "token": self.token,
            "doc_freq": self.doc_freq,
            "postings": self.postings,
            "idf": self.idf,
            "idf_smooth": self.idf_smooth
        }
    
    def compute_idf(self, total_docs):
        # Inverse document frequency - how rare is a word in documents the high the number the more rare
        if self.doc_freq > 0:
            # Classic logarithmic - may encounter division by 0 (handled)
            self.idf = log(total_docs / self.doc_freq)
            # Adding number one for more consistent results
            self.idf_smooth = log(total_docs / (1 + self.doc_freq)) + 1
        else:
            self.idf = 0.0
            self.idf_smooth = 0.0
            
    def compute_tf_idf(self, doc_id):
        if doc_id in self.postings:
            tf = self.postings[doc_id]
            tf_idf = tf * self.idf_smooth
            self.postings[doc_id].append(tf_idf)
        else:
            pass
    
def read_data_from_csv():
    with open("data_regex2.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            combined_text = " ".join([
                row.get("full_name", ""),
                row.get("description", ""),
                row.get("gamePlatform", ""),
                row.get("genre", ""),
                row.get("keywords", ""),
                row.get("released", ""),
                row.get("publisher", ""),
                row.get("metascore", "")
            ]).strip()
            
            ALL_DATA.add(combined_text)
            
    print(f"Read {len(ALL_DATA)} unique text entries from CSV")
    return ALL_DATA

def read_csv_objects():
    with open("data_regex2.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            ALL_OBJECTS.append(row)
            
    print(f"Read {len(ALL_OBJECTS)} total objects from CSV")
    return ALL_OBJECTS

def index_preprocessing(text, query = False):
    
    # Regex to extract words, convert to lowercase
    tokens = re.findall(r'\b\w+\b', str(text).lower())
    stemmed_tokens = [STEMMER.stem(token) for token in tokens]
    tokens = [token for token in stemmed_tokens if token not in STOP_WORDS]
    
    if query:
        tokens = [token for token in tokens if token not in QUERY_STOP_WORDS]
        print(f"Processed query tokens (after stop word removal): {tokens}")
    
    return tokens