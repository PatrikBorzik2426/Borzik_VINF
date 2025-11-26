import json
from math import sqrt
from functions import index_body, bcolors, read_csv_objects, index_preprocessing

ALL_OBJECTS = set()
INDEX_SET = dict()
DOCUMENT_MAGNITUDES = dict()
    
def read_index_set():
    global DOCUMENT_MAGNITUDES
    
    try:
        with open("index_set.json", "r", encoding="utf-8") as f:
            index_list = json.load(f)
            for item in index_list:
                index = index_body(
                    token=item["token"],
                    doc_freq=item["doc_freq"],
                    postings=item["postings"]
                )
                index.idf = item.get("idf", 0.0)
                index.idf_smooth = item.get("idf_smooth", 0.0)
                
                INDEX_SET[index.token] = index
                
        print(f"Loaded index set with {len(INDEX_SET)} entries from index_set.json")
    except FileNotFoundError:
        print("index_set.json not found. Starting with an empty index set.")
    
    # Load precomputed document magnitudes
    try:
        with open("document_magnitudes.json", "r", encoding="utf-8") as f:
            DOCUMENT_MAGNITUDES = json.load(f)
        print(f"Loaded document magnitudes for {len(DOCUMENT_MAGNITUDES)} documents")
    except FileNotFoundError:
        print("document_magnitudes.json not found. Cosine similarity will not be available.")
        
def count_best_objects(mentioned_tokens, or_switch = True, weighted = True):
    object_scores = dict()
    
    if or_switch:
        for token in mentioned_tokens:
            if token in INDEX_SET:
                index_entry = INDEX_SET[token]
                for doc_id, term_freq in index_entry.postings.items():
                    if doc_id not in object_scores:
                        object_scores[doc_id] = 0
                    object_scores[doc_id] +=  term_freq if weighted else 1  * index_entry.idf_smooth
    else:
        
        doc_sets = []
        for token in mentioned_tokens:
            if token in INDEX_SET:
                index_entry = INDEX_SET[token]
                doc_sets.append(set(index_entry.postings.keys()))
            else:
                doc_sets.append(set())
        
        if doc_sets:
            common_docs = set.intersection(*doc_sets)
            for doc_id in common_docs:
                object_scores[doc_id] = 0
                for token in mentioned_tokens:
                    index_entry = INDEX_SET[token]
                    term_freq = index_entry.postings.get(doc_id, 0)
                    object_scores[doc_id] +=  term_freq if weighted else 1  * index_entry.idf_smooth
                
    # Sort objects by score in descending order
    sorted_objects = sorted(object_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_objects[:10]  # Return top 10 objects

def count_best_objects_cosine(mentioned_tokens, or_switch=True):

    if not DOCUMENT_MAGNITUDES:
        print("Warning: Document magnitudes not loaded. Cannot compute cosine similarity.")
        return []
    
    object_scores = dict()
    query_vector = dict()  # Store query TF-IDF values
    
    # Build query vector with TF-IDF weights
    for token in mentioned_tokens:
        if token in INDEX_SET:
            index_entry = INDEX_SET[token]
            # Simple term frequency for query (could be 1 or count of token in query)
            query_tf = mentioned_tokens.count(token)
            query_vector[token] = query_tf * index_entry.idf_smooth
    
    # Compute query magnitude
    query_magnitude = sqrt(sum(weight ** 2 for weight in query_vector.values()))
    
    if query_magnitude == 0:
        return []
    
    # Compute cosine similarity for each document
    if or_switch:
        # OR query: consider all documents that contain any query term
        candidate_docs = set()
        for token in mentioned_tokens:
            if token in INDEX_SET:
                candidate_docs.update(INDEX_SET[token].postings.keys())
        
        for doc_id in candidate_docs:
            dot_product = 0.0
            
            for token, query_weight in query_vector.items():
                if token in INDEX_SET:
                    index_entry = INDEX_SET[token]
                    if doc_id in index_entry.postings:
                        weighted_tf = index_entry.postings[doc_id]
                        doc_tfidf = weighted_tf * index_entry.idf_smooth
                        dot_product += query_weight * doc_tfidf
            
            doc_magnitude = DOCUMENT_MAGNITUDES.get(doc_id, 0.0)
            
            if doc_magnitude > 0:
                cosine_sim = dot_product / (query_magnitude * doc_magnitude)
                object_scores[doc_id] = cosine_sim
    
    else:
        # AND query: only documents containing all query terms
        doc_sets = []
        for token in mentioned_tokens:
            if token in INDEX_SET:
                doc_sets.append(set(INDEX_SET[token].postings.keys()))
            else:
                doc_sets.append(set())
        
        if doc_sets:
            common_docs = set.intersection(*doc_sets)
            
            for doc_id in common_docs:
                dot_product = 0.0
                
                for token, query_weight in query_vector.items():
                    if token in INDEX_SET:
                        index_entry = INDEX_SET[token]
                        if doc_id in index_entry.postings:
                            weighted_tf = index_entry.postings[doc_id]  # This is a float, not a list
                            doc_tfidf = weighted_tf * index_entry.idf_smooth
                            dot_product += query_weight * doc_tfidf
                
                doc_magnitude = DOCUMENT_MAGNITUDES.get(doc_id, 0.0)
                
                if doc_magnitude > 0:
                    cosine_sim = dot_product / (query_magnitude * doc_magnitude)
                    object_scores[doc_id] = cosine_sim
    
    # Sort by cosine similarity (descending)
    sorted_objects = sorted(object_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_objects[:10]

read_index_set()
ALL_OBJECTS = read_csv_objects()
input_value = ""

while input_value != "exit":
    
    input_value = input(f"\n{bcolors.WARNING}Enter your query: {bcolors.ENDC}")
    preprocess_query = index_preprocessing(str(input_value), True) 

    print("\n")

    # TF-IDF scoring
    best_objects_and = count_best_objects(preprocess_query, or_switch=False)
    best_objects_or = count_best_objects(preprocess_query, or_switch=True)
    
    # Cosine similarity scoring
    best_objects_cosine_and = count_best_objects_cosine(preprocess_query, or_switch=False)
    best_objects_cosine_or = count_best_objects_cosine(preprocess_query, or_switch=True)
    
    print(f"{bcolors.OKBLUE}TF-IDF AND results:{bcolors.ENDC}")
    for obj_id, score in best_objects_and:
        print(f"Object ID: {obj_id}, Score: {score:.4f}, Game: {bcolors.OKBLUE} {ALL_OBJECTS[int(obj_id)]['full_name']} {bcolors.ENDC}, Released: {ALL_OBJECTS[int(obj_id)]['datePublished']}, URL: {ALL_OBJECTS[int(obj_id)]['url']}")

    print(f"\n{bcolors.OKGREEN}TF-IDF OR results:{bcolors.ENDC}")
    for obj_id, score in best_objects_or:
        print(f"Object ID: {obj_id}, Score: {score:.4f}, Game: {bcolors.OKGREEN} {ALL_OBJECTS[int(obj_id)]['full_name']} {bcolors.ENDC}, Released: {ALL_OBJECTS[int(obj_id)]['datePublished']}, URL: {ALL_OBJECTS[int(obj_id)]['url']}")
    
    print(f"\n{bcolors.HEADER}COSINE AND results:{bcolors.ENDC}")
    for obj_id, score in best_objects_cosine_and:
        print(f"Object ID: {obj_id}, Cosine: {score:.4f}, Game: {bcolors.HEADER} {ALL_OBJECTS[int(obj_id)]['full_name']} {bcolors.ENDC}, Released: {ALL_OBJECTS[int(obj_id)]['datePublished']}, URL: {ALL_OBJECTS[int(obj_id)]['url']}")
    
    print(f"\n{bcolors.FAIL}COSINE OR results:{bcolors.ENDC}")
    for obj_id, score in best_objects_cosine_or:
        print(f"Object ID: {obj_id}, Cosine: {score:.4f}, Game: {bcolors.FAIL} {ALL_OBJECTS[int(obj_id)]['full_name']} {bcolors.ENDC}, Released: {ALL_OBJECTS[int(obj_id)]['datePublished']}, URL: {ALL_OBJECTS[int(obj_id)]['url']}")