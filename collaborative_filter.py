# collaborative_filter.py
import bcrypt
import pandas as pd
from sqlalchemy import create_engine

from models import DATABASE_URL


def get_user_liked_books(user_id: int):
    """
    Generate a DataFrame of a user's most recently rated books.
    
    Args:
        user_id (int): The ID of the user to generate recommendations for
        
    Returns:
        pd.DataFrame: DataFrame containing user's recently rated books
        ['user_id', 'book_id', 'rating', 'rated_date']
    """
    # Create a database engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # SQL query with %s placeholder for psycopg2
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
            params=(user_id,)  # Note the comma to make it a tuple
        )
        
        # If no ratings found, return empty DataFrame with expected columns
        if user_liked_books.empty:
            return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date'])
        
        print(f"Found {len(user_liked_books)} liked books for user {user_id}")
        
        return user_liked_books
        
    except Exception as e:
        print(f"Error generating sparse DataFrame: {str(e)}")
        return pd.DataFrame(columns=['user_id', 'book_id', 'rating', 'rated_date'])
    
    finally:
        # Dispose of the engine connection
        engine.dispose()

def get_overlap_users(user_id: int,user_liked_books, min_overlap_percentage: float = 0.20):
    """
    Generate a DataFrame of users who have rated the same books as the target user,
    with frequency of overlapping books exceeding a minimum percentage of the target user's rated books.
    
    Args:
        user_id (int): The ID of the target user
        min_overlap_percentage (float): Minimum overlap percentage threshold (default 0.20 or 20%)
        
    Returns:
        pd.DataFrame: DataFrame with columns 'user_id', 'frequency', and 'overlap_percentage'
        ['user_id', 'frequency', 'overlap_percentage']
    """
    
    if user_liked_books.empty:
        return pd.DataFrame(columns=['user_id', 'frequency', 'overlap_percentage'])
    
    # Calculate the total number of books the target user has rated (max 100)
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

def get_recommendations(user_id:int):
    """
    returns pandas df
    ['user_id', 'frequency', 'overlap_percentage']
    """
    user_liked_books = get_user_liked_books(user_id)
    overlap_users = get_overlap_users(user_id, user_liked_books)
    return overlap_users

if __name__ == "__main__":
    # Test the function
    print(get_recommendations(4).head(20))