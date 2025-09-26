import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity


def recommend_cast(titles, movies_path='tmdb_5000_movies.csv',
                   credits_path='tmdb_5000_credits.csv',
                   pickle_path='crew_cast_vectors.pkl',
                   num_recommendations=6):

    # Load or prepare data
    # movies_df, vectorizer, vector_matrix, indices = load_or_prepare(movies_path, credits_path, pickle_path)
    with open(pickle_path, 'rb') as f:
        movies_df, vectorizer, vector_matrix, indices = pickle.load(f)

    combined_scores = None
    for title in titles:
        if title not in indices:
            print(f"'{title}' not found in dataset.")
            continue
        idx = indices[title]
        sim_scores = cosine_similarity(vector_matrix[idx], vector_matrix).flatten()

        if combined_scores is None:
            combined_scores = sim_scores
        else:
            combined_scores += sim_scores

    if combined_scores is None:
        return "No valid titles provided."

    # Exclude input titles
    input_indices = [indices[title] for title in titles if title in indices]
    for i in input_indices:
        combined_scores[i] = -1  # remove self-matches

    top_indices = combined_scores.argsort()[::-1][:num_recommendations]
    return movies_df['original_title'].iloc[top_indices].tolist()

if __name__ == "__main__":
    titles = ['Inception', 'Interstellar']
    print(recommend_cast(titles))
