# collaborative_filter.py
import bcrypt
import pandas as pd
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
            LIMIT 100
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
    if overlap_users.empty:
        print(f"No similar users found for user {user_id}. Returning only target user's ratings.")
        return None
    
    # Extract the list of similar user IDs, including the target user
    similar_user_ids = tuple(overlap_users['user_id'].tolist() + [user_id])
    
    # Create a database engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # SQL query to fetch all ratings from similar users and the target user
        query = """
            SELECT user_id, book_id, rating, rated_date
            FROM user_book_ratings
            WHERE user_id IN %s
            ORDER BY user_id, book_id
        """
        
        # Execute query with parameters
        all_ratings = pd.read_sql(
            query,
            engine,
            params=(similar_user_ids,)
        )
        
        # If no ratings found (unlikely), return empty DataFrame
        if all_ratings.empty:
            print(f"No ratings found for similar users or target user {user_id}")
            return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date'])
        
        print(f"Found {len(all_ratings)} ratings from {len(similar_user_ids)} users (including target user {user_id})")
        return all_ratings
        
    except Exception as e:
        print(f"Error fetching ratings for recommendations: {str(e)}")
        return pd.DataFrame(columns=['user_id', 'book_id', 'rating'])
    
    finally:
        # Dispose of the engine connection
        engine.dispose()

def get_recommendations(user_id: int):
    user_liked_books = get_user_liked_books(user_id)
    overlap_users = get_overlap_users(user_id, user_liked_books)
    all_similar_book_ratings = get_similar_user_liked_books(user_id, overlap_users)
    return all_similar_book_ratings

if __name__ == "__main__":
    # Test the function
    target_user_id = 2
    recommendations = get_recommendations(target_user_id)
    print(f"\nAll ratings from similar users and target user {target_user_id}:")
    print(recommendations.tail(100))