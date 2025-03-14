# collaborative_filter.py
import bcrypt
import pandas as pd
from scipy.sparse import coo_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine

from models import DATABASE_URL


def get_user_liked_books(user_id: int):
    """
    Generate a DataFrame of all books rated by a user, ordered by most recent.
    
    Args:
        user_id (int): The ID of the user to fetch rated books for
        
    Returns:
        pd.DataFrame: DataFrame with columns ['user_id', 'book_id', 'rating', 'rated_date']
    """
    # Create a database engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # SQL query to fetch all rated books
        query = """
            SELECT user_id, book_id, rating, rated_date
            FROM user_book_ratings
            WHERE user_id = %s
            ORDER BY rated_date DESC
        """
        
        # Execute query with parameter as a tuple
        user_liked_books = pd.read_sql(
            query,
            engine,
            params=(user_id,)
        )
        
        # If no ratings found, return empty DataFrame with expected columns
        if user_liked_books.empty:
            print(f"No liked books found for user {user_id}")
            return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date'])
        
        print(f"Found {len(user_liked_books)} liked books for user {user_id}")
        return user_liked_books
        
    except Exception as e:
        print(f"Error fetching user liked books: {str(e)}")
        return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date'])
    
    finally:
        # Dispose of the engine connection
        engine.dispose()


def get_overlap_users(user_id: int, user_liked_books: pd.DataFrame, min_overlap_percentage: float = 0.20):
    """
    Generate a DataFrame of users with overlapping books exceeding a minimum percentage of the target user's rated books.
    
    Args:
        user_id (int): The ID of the target user
        user_liked_books (pd.DataFrame): DataFrame of the target user's rated books
        min_overlap_percentage (float): Minimum overlap percentage threshold (default 0.20 or 20%)
        
    Returns:
        pd.DataFrame: DataFrame with columns ['user_id', 'frequency', 'overlap_percentage']
    """
    if user_liked_books.empty:
        return pd.DataFrame(columns=['user_id', 'frequency', 'overlap_percentage'])
    
    # Calculate the total number of books the target user has rated
    total_user_books = len(user_liked_books)
    
    # Extract the book_ids of the target user's liked books
    liked_book_ids = tuple(user_liked_books['book_id'].tolist())
    
    # Create a database engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # SQL query to find users who rated the same books, excluding the target user
        query = """
            SELECT user_id, COUNT(book_id) as frequency
            FROM user_book_ratings
            WHERE book_id IN %s
            AND user_id != %s
            GROUP BY user_id
            HAVING COUNT(book_id) >= %s
            ORDER BY frequency DESC
        """
        
        # Calculate minimum frequency threshold based on percentage
        min_frequency = total_user_books * min_overlap_percentage
        
        # Execute query with parameters
        overlap_users = pd.read_sql(
            query,
            engine,
            params=(liked_book_ids, user_id, min_frequency)
        )
        
        # If no overlapping users found, return empty DataFrame
        if overlap_users.empty:
            return pd.DataFrame(columns=['user_id', 'frequency', 'overlap_percentage'])
        
        # Add overlap percentage column
        overlap_users['overlap_percentage'] = (overlap_users['frequency'] / total_user_books) * 100
        
        return overlap_users
        
    except Exception as e:
        print(f"Error generating overlap users DataFrame: {str(e)}")
        return pd.DataFrame(columns=['user_id', 'frequency', 'overlap_percentage'])
    
    finally:
        # Dispose of the engine connection
        engine.dispose()


def get_similar_user_liked_books(user_id: int, overlap_users: pd.DataFrame):
    """
    Generate a DataFrame of all books rated by similar users and the target user, with user and book indices.
    
    Args:
        user_id (int): The ID of the target user
        overlap_users (pd.DataFrame): DataFrame of similar users ['user_id', 'frequency', 'overlap_percentage']
        
    Returns:
        pd.DataFrame: DataFrame with columns ['user_id', 'book_id', 'rating', 'rated_date', 'user_index', 'book_index']
    """
    if overlap_users.empty:
        print(f"No similar users found for user {user_id}. Fetching only target user's ratings.")
        all_ratings = get_user_liked_books(user_id)
    else:
        similar_user_ids = tuple(overlap_users['user_id'].tolist() + [user_id])
        engine = create_engine(DATABASE_URL)
        
        try:
            query = """
                SELECT user_id, book_id, rating, rated_date
                FROM user_book_ratings
                WHERE user_id IN %s
                ORDER BY user_id, book_id
            """
            all_ratings = pd.read_sql(query, engine, params=(similar_user_ids,))
        except Exception as e:
            print(f"Error fetching ratings for similar users: {str(e)}")
            return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date', 'user_index', 'book_index'])
        finally:
            engine.dispose()
    
    if all_ratings.empty:
        print(f"No ratings found for similar users or target user {user_id}")
        return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date', 'user_index', 'book_index'])
    
    # Assign unique indices starting from 0 for users and books
    unique_users = all_ratings['user_id'].unique()
    unique_books = all_ratings['book_id'].unique()
    
    user_index_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
    book_index_map = {book_id: idx for idx, book_id in enumerate(unique_books)}
    
    all_ratings['user_index'] = all_ratings['user_id'].map(user_index_map)
    all_ratings['book_index'] = all_ratings['book_id'].map(book_index_map)

    # Find the index of the target user_id
    user_index = all_ratings[all_ratings['user_id'] == user_id]['user_index'].values[0]
    
    print(f"Found {len(all_ratings)} ratings from {len(unique_users)} users (including target user {user_id})")
    return user_index, all_ratings


def generate_sparse_matrix(all_ratings: pd.DataFrame):
    # Create a sparse matrix in COO format using user_index, book_index, and ratings
    ratings_mat = coo_matrix(
        (all_ratings['rating'],
         (all_ratings['user_index'], all_ratings['book_index']))
    )
    # Convert to CSR format for efficient row operations
    ratings_mat = ratings_mat.tocsr()

    print(f"Generated sparse matrix of shape {ratings_mat.shape}")
    return ratings_mat


def add_book_metadata(book_recs: pd.DataFrame):
    """
    Add metadata (rating_count, mod_title) from the books table to the book recommendations DataFrame.
    
    Args:
        book_recs (pd.DataFrame): DataFrame with columns ['book_id', 'count', 'mean']
        
    Returns:
        pd.DataFrame: DataFrame with columns ['book_id', 'count', 'mean', 'rating_count', 'mod_title']
    """
    if book_recs.empty:
        return pd.DataFrame(columns=['book_id', 'count', 'mean', 'rating_count', 'mod_title'])

    # Fetch rating_count and mod_title from the books table
    engine = create_engine(DATABASE_URL)
    try:
        # Query to get rating_count and mod_title for all books in book_recs
        book_ids = tuple(book_recs['book_id'].tolist())
        query = """
            SELECT book_id, rating_count, mod_title
            FROM books
            WHERE book_id IN %s
        """
        book_counts = pd.read_sql(query, engine, params=(book_ids,))
    except Exception as e:
        print(f"Error fetching rating counts from books table: {str(e)}")
        book_counts = pd.DataFrame(columns=['book_id', 'rating_count', 'mod_title'])
    finally:
        engine.dispose()

    # Merge rating_count and mod_title with book_recs
    book_recs = book_recs.merge(book_counts, on='book_id', how='left')
    # Fill NaN rating_count with 0 if no data exists in books table (unlikely but possible)
    book_recs['rating_count'] = book_recs['rating_count'].fillna(0).astype(int)
    # Fill NaN mod_title with empty string
    book_recs['mod_title'] = book_recs['mod_title'].fillna('')

    return book_recs


def get_recommendations(user_id: int):
    # Fetch the target user's liked books
    user_liked_books = get_user_liked_books(user_id)
    
    # Fetch mod_title for the user's liked books
    engine = create_engine(DATABASE_URL)
    try:
        liked_book_ids = tuple(user_liked_books['book_id'].tolist())
        query = """
            SELECT book_id, mod_title
            FROM books
            WHERE book_id IN %s
        """
        user_liked_books_meta = pd.read_sql(query, engine, params=(liked_book_ids,))
        user_liked_books = user_liked_books.merge(user_liked_books_meta, on='book_id', how='left')
        user_liked_books['mod_title'] = user_liked_books['mod_title'].fillna('')
    except Exception as e:
        print(f"Error fetching mod_title for user liked books: {str(e)}")
        user_liked_books['mod_title'] = ''
    finally:
        engine.dispose()

    # Find users with significant overlap
    overlap_users = get_overlap_users(user_id, user_liked_books)
    # Get ratings from similar users and the target user's index
    user_index, all_similar_book_ratings = get_similar_user_liked_books(user_id, overlap_users)
    # Generate sparse matrix from all ratings
    ratings_mat = generate_sparse_matrix(all_similar_book_ratings)

    # Calculate cosine similarity between the target user and all other users
    similarity = cosine_similarity(ratings_mat[user_index, :], ratings_mat).flatten()

    # Get indices of the 15 most similar users (excluding the target user)
    similar_user_indices = similarity.argsort()[-16:][::-1]  # Get top 16 (including user) and reverse for descending order
    similar_user_indices = similar_user_indices[similar_user_indices != user_index]  # Remove target user
    similar_user_indices = similar_user_indices[:15]  # Keep only top 15

    # Filter ratings to include only those from the most similar users (exclude target user)
    similar_ratings = all_similar_book_ratings[
        (all_similar_book_ratings['user_index'].isin(similar_user_indices)) &
        (all_similar_book_ratings['user_id'] != user_id)
    ].copy()

    # If no ratings remain after filtering, return an empty DataFrame
    if similar_ratings.empty:
        print(f"No ratings from similar users available for recommendations for user {user_id}")
        return pd.DataFrame(columns=['book_id', 'count', 'mean', 'rating_count', 'mod_title', 'adjusted_count', 'score'])

    # Group by book_id and calculate count and mean of ratings from similar users
    book_recs = (
        similar_ratings.groupby('book_id')
        .agg(
            count=('rating', 'count'),  # Number of ratings per book from similar users
            mean=('rating', 'mean')     # Average rating per book from similar users
        )
        .reset_index()
    )

    # Add rating_count and mod_title from books table
    book_recs = add_book_metadata(book_recs)

    # Add adjusted count and score
    book_recs['adjusted_count'] = book_recs['count'] * (book_recs['count'] / book_recs['rating_count'])
    book_recs['score'] = book_recs['mean'] * book_recs['adjusted_count']

    # Remove books that are in the user's liked list (by book_id)
    book_recs = book_recs[~book_recs['book_id'].isin(user_liked_books['book_id'])]

    # Remove books that have the same mod_title as any in user_liked_books
    liked_mod_titles = set(user_liked_books['mod_title'].str.lower())  # Case-insensitive comparison
    book_recs = book_recs[~book_recs['mod_title'].str.lower().isin(liked_mod_titles)]

    # optimzations
    count_thresold = 2
    mean_threshold = 2
    book_recs = book_recs[book_recs['count'] > count_thresold] # At least 3 similar users have rated the book
    book_recs = book_recs[book_recs['mean'] > mean_threshold] # Average rating is at least 3
    book_recs = book_recs.sort_values(by='score', ascending=False)

    print(f"Generated {len(book_recs)} book recommendations for user {user_id}")
    return book_recs


if __name__ == "__main__":
    # Test the function
    target_user_id = 2
    similar_books = get_recommendations(target_user_id)
    print(f"\nTop book recommendations for user {target_user_id}:")
    print(similar_books.head(10))  # Show top 10 recommendations