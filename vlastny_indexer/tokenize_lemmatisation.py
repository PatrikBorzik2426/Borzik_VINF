from math import log, sqrt
from functions import read_data_from_csv, index_body, index_preprocessing, read_csv_objects
import json

ALL_DATA = []  # Changed to list to maintain order
ALL_OBJECTS = []
UNIQUE_TOKENS = set()
INDEX_SET = set()
DOCUMENT_MAGNITUDES = {}  # Store precomputed document vector magnitudes

# Field weights - higher values = more important for search
FIELD_WEIGHTS = {
    'full_name': 3.25,
    'genre': 3.0,
    'keywords': 2.5,
    'publisher': 2.0,
    'description': 1.0,
    'platform': 1.5,
    'datePublished': 2.5,
    'metascore': 0.8
}

def compute_document_magnitudes():
    """
    Precompute the magnitude (L2 norm) of each document vector
    This is used for cosine similarity normalization
    """
    print("Computing document vector magnitudes...")
    
    for doc_id in range(len(ALL_OBJECTS)):
        magnitude_squared = 0.0
        
        # Sum squared TF-IDF values for all terms in document
        for index_entry in INDEX_SET:
            if doc_id in index_entry.postings:
                weighted_tf = index_entry.postings[doc_id]  # This is a float, not a list
                tfidf = weighted_tf * index_entry.idf_smooth
                magnitude_squared += tfidf ** 2
        
        DOCUMENT_MAGNITUDES[str(doc_id)] = sqrt(magnitude_squared)
    
    print(f"Computed magnitudes for {len(DOCUMENT_MAGNITUDES)} documents")

def print_index_set():
    
    for index in INDEX_SET:
        index.compute_idf(len(ALL_DATA))
    
    index_list = [index.to_dict() for index in INDEX_SET]
    
    with open("index_set.json", "w", encoding="utf-8") as f:
        json.dump(index_list, f, ensure_ascii=False, indent=4)
    
    print(f"Saved index set with {len(INDEX_SET)} entries to index_set.json")
    
    # Compute and save document magnitudes for cosine similarity
    compute_document_magnitudes()
    
    with open("document_magnitudes.json", "w", encoding="utf-8") as f:
        json.dump(DOCUMENT_MAGNITUDES, f, ensure_ascii=False, indent=4)
    
    print(f"Saved document magnitudes to document_magnitudes.json")
    
def progress_bar(progress, total):
    percent = 100 * (progress / float(total))
    bar = '█' * int(percent) + '-' * (100 - int(percent))
    print(f"\r|{bar}| {percent:.2f}%", end="\r")
    if progress == total:
        print("Done")

def weighted_field_tokenization():
    
    for doc_index, game_obj in enumerate(ALL_OBJECTS):
        # Process each field separately with its weight
        field_tokens = {}
        
        for field_name, field_weight in FIELD_WEIGHTS.items():
            field_content = game_obj.get(field_name, "")
            
            # Handle different field types
            if isinstance(field_content, list):
                field_content = " ".join(str(item) for item in field_content)
            
            field_content = str(field_content)
            
            if field_content and field_content.strip():
                # Tokenize the field content
                tokens = index_preprocessing(field_content)
                field_tokens[field_name] = tokens
                
                # Add tokens to index with weighted term frequency
                for token in tokens:
                    if token not in UNIQUE_TOKENS:
                        UNIQUE_TOKENS.add(token)
                        # Initialize with weighted frequency
                        weighted_tf = field_weight
                        new_index_row = index_body(token, 0, {})
                        new_index_row.add_posting(doc_index, weighted_tf)
                        INDEX_SET.add(new_index_row)
                    else:
                        # Find existing index row
                        index_row = next((ir for ir in INDEX_SET if ir.token == token), None)
                        if index_row:
                            if doc_index in index_row.postings:
                                # Add weighted frequency to existing posting
                                index_row.postings[doc_index] += field_weight
                            else:
                                # Create new posting with weighted frequency
                                index_row.add_posting(doc_index, field_weight)
        
        # Progress tracking
        if (doc_index + 1) % 1000 == 0 or doc_index == len(ALL_OBJECTS) - 1:
            progress_bar(doc_index + 1, len(ALL_OBJECTS))
    
    print(f"\nIndexed {len(ALL_OBJECTS)} documents with {len(UNIQUE_TOKENS)} unique tokens")


ALL_DATA = read_data_from_csv()  # Keep for compatibility
ALL_OBJECTS = read_csv_objects()  # Get structured objects
print(f"Loaded {len(ALL_OBJECTS)} games")

# Perform weighted tokenization
weighted_field_tokenization()
print_index_set()
