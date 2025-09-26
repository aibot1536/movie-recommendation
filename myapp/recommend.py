import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- Recommend based on user ratings ---
def recommend_movies(user_ratings, preferred_genres=None, top_n=14, pickle_path="movie_recommender.pkl"):

    # df, feature_matrix, vectorizer, mlb = load_or_preprocess(dataset_path, pickle_path)
    with open(pickle_path, "rb") as f:
        df, feature_matrix, vectorizer, mlb = pickle.load(f)

    # Weighted similarity
    scores = np.zeros(feature_matrix.shape[0])
    for movie, rating in user_ratings.items():
        if movie in df['original_title'].values:
            idx = df.index[df['original_title'] == movie][0]
            sim = cosine_similarity(feature_matrix[idx], feature_matrix).flatten()
            scores += sim * rating

    # Normalize
    if scores.max() > 0:
        scores /= scores.max()

    # Genre boost
    if preferred_genres:
        for genre in preferred_genres:
            if genre in df.columns:
                scores += 0.2 * df[genre].values

    # Sort and exclude rated movies
    ranked_indices = scores.argsort()[::-1]
    recommendations = []
    for idx in ranked_indices:
        title = df.iloc[idx]['original_title']
        if title not in user_ratings and title not in recommendations:
            recommendations.append(title)
        if len(recommendations) >= top_n:
            break
    return recommendations

# --- Recommend similar to a title ---
def recommend_from_title(movie_title, top_n=10, pickle_path="movie_recommender.pkl"):

    # df, feature_matrix, vectorizer, mlb = load_or_preprocess(dataset_path, pickle_path)
    with open(pickle_path, "rb") as f:
        df, feature_matrix, vectorizer, mlb = pickle.load(f)

    if movie_title not in df['original_title'].values:
        return [f"Movie '{movie_title}' not found in dataset."]

    idx = df.index[df['original_title'] == movie_title][0]
    sim_scores = cosine_similarity(feature_matrix[idx], feature_matrix).flatten()

    ranked_indices = sim_scores.argsort()[::-1][1:]  # skip itself
    recommendations = []
    for idx in ranked_indices:
        title = df.iloc[idx]['original_title']
        if title not in recommendations:
            recommendations.append(title)
        if len(recommendations) >= top_n:
            break
    return recommendations

if __name__ == "__main__":
    user_ratings = {"Inception": 5, "The Dark Knight": 4}
    preferred_genres = ["Action", "Adventure"]

    recs = recommend_movies(user_ratings, preferred_genres)
    print("Recommended Movies:", recs)
