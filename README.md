# BookXchange 📚

A collaborative platform for sharing physical copies of books with an intelligent recommendation engine. Users can list books they own, discover books from their community, and get personalized recommendations based on their reading preferences.

## Features

### 🏠 **Core Functionality**
- **Book Sharing**: List your physical books for others to discover
- **Smart Search**: Advanced search functionality using TF-IDF vectorization
- **Location-based Filtering**: Find books near you (Province/District/City)
- **Real-time Messaging**: Chat with book owners directly
- **Book Rating System**: Rate books and see community ratings

### 🤖 **Recommendation Engine**
- **Collaborative Filtering**: Get recommendations based on users with similar tastes
- **Trending Books**: Discover what's popular in your community
- **Personalized Suggestions**: AI-powered book recommendations tailored to your preferences

### 📍 **Location Features**
- Hierarchical location filtering (Province → District → City)
- Location-based book discovery
- User location integration

## Screenshots

![Home Page](sceenshots/booxchange_1)
![Book Wall](sceenshots/booxchange_2)
![Book Details](sceenshots/booxchange_3)
## Tech Stack

### **Backend**
- **Python 3.10+**
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **bcrypt**: Password hashing and authentication

### **Frontend**
- **Streamlit**: Web application framework
- **Responsive UI** with multi-column layouts

### **Machine Learning**
- **scikit-learn**: TF-IDF vectorization and cosine similarity
- **pandas & numpy**: Data processing
- **scipy**: Sparse matrix operations for collaborative filtering

### **Key Libraries**
- `streamlit` - Web UI framework
- `sqlalchemy` - Database ORM
- `pandas` - Data manipulation
- `scikit-learn` - ML algorithms
- `bcrypt` - Password security
- `python-dotenv` - Environment configuration

## Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL database
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bookxchange.git
   cd bookxchange
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install streamlit sqlalchemy pandas scikit-learn bcrypt python-dotenv psycopg2-binary numpy scipy
   ```

4. **Setup Database**
   ```bash
   # Create PostgreSQL database
   psql -U postgres
   CREATE DATABASE bookxchange_db;
   \q
   
   # Run the SQL schema
   psql -U postgres -d bookxchange_db -f bookxchange_db.sql
   ```

5. **Configure Environment**
   ```bash
   # Copy the .env file and update with your database credentials
   cp .env.example .env
   # Edit .env with your database settings
   ```

6. **Initialize the Application**
   ```bash
   # Populate database with sample data (optional)
   python populate_db.py
   
   # Generate search index files
   python utils.py
   ```

## Usage

### Running the Application

```bash
streamlit run home.py
```

The application will be available at `http://localhost:8501`

### Key Files

#### **Core Application**
- [`home.py`](home.py) - Main application entry point and navigation
- [`models.py`](models.py) - Database models and schema definitions
- [`database.py`](database.py) - Database connection and initialization
- [`crud.py`](crud.py) - Database operations (Create, Read, Update, Delete)

#### **Features**
- [`utils.py`](utils.py) - Search functionality using TF-IDF
- [`collaborative_filter.py`](collaborative_filter.py) - Recommendation engine
- [`trending.py`](trending.py) - Trending books algorithm
- [`messaging.py`](messaging.py) - User messaging system
- [`location_filter.py`](location_filter.py) - Location-based filtering

#### **Pages**
- [`pages/wall.py`](pages/wall.py) - Main book discovery page
- [`pages/books.py`](pages/books.py) - User's book management
- [`pages/book_details.py`](pages/book_details.py) - Individual book details
- [`pages/recommendations.py`](pages/recommendations.py) - Personalized recommendations
- [`pages/messages.py`](pages/messages.py) - Messaging interface
- [`pages/login.py`](pages/login.py) - User authentication

### User Guide

1. **Registration**: Create an account with your location details
2. **Add Books**: List books you own using ISBN search or manual entry
3. **Discover**: Browse the community wall with location and search filters
4. **Rate**: Rate books you've read to improve recommendations
5. **Message**: Contact book owners directly through the messaging system
6. **Recommendations**: Get personalized book suggestions based on your preferences

## Database Schema

The application uses PostgreSQL with the following main tables:

- **users**: User profiles and authentication
- **books**: Book catalog with metadata
- **user_book_ratings**: User ratings and preferences
- **listed_books**: Books available for sharing
- **messages/conversations**: User communication
- **Location tables**: Province/District/City hierarchy

## API Features

### Search Engine
- TF-IDF based text search using [`search()`](utils.py) function
- Preprocessed book titles for better matching
- Cosine similarity scoring

### Recommendation System
- Collaborative filtering algorithm in [`get_recommendations()`](collaborative_filter.py)
- User similarity calculation using cosine similarity
- Bayesian rating system with database triggers

### Trending Algorithm
Recent activity-based trending in [`get_trending_books()`](trending.py):
- 50% weight on recent ratings
- 30% weight on total rating count  
- 20% weight on average rating

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

---

**BookXchange** - Connecting readers, one book at a time! 📖✨