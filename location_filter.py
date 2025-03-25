from sqlalchemy import desc

from database import get_db
from models import (
    Book,
    City,
    District,
    DistrictCity,
    ListedBook,
    Province,
    ProvinceDistrict,
    User,
)
from utils import search


def get_provinces():
    """Fetch all provinces from the database."""
    with get_db() as db:
        provinces = db.query(Province).order_by(Province.name).all()
        return {province.name: province.province_id for province in provinces}


def get_districts(province_id=None):
    """Fetch districts, optionally filtered by province."""
    with get_db() as db:
        query = db.query(District).join(ProvinceDistrict).filter(ProvinceDistrict.district_id == District.district_id)
        if province_id:
            query = query.filter(ProvinceDistrict.province_id == province_id)
        districts = query.order_by(District.name).all()
        return {district.name: district.district_id for district in districts}


def get_cities(district_id=None):
    """Fetch cities, optionally filtered by district."""
    with get_db() as db:
        query = db.query(City).join(DistrictCity).filter(DistrictCity.city_id == City.city_id)
        if district_id:
            query = query.filter(DistrictCity.district_id == district_id)
        cities = query.order_by(City.name).all()
        return {city.name: city.city_id for city in cities}


def load_filtered_books(offset, limit=20, search_query=None, province_id=None, district_id=None, city_id=None):
    """
    Load books with location and search filters applied.
    
    Args:
        offset (int): Pagination offset
        limit (int): Number of books to fetch
        search_query (str): Optional search term
        province_id (int): Optional province filter
        district_id (int): Optional district filter
        city_id (int): Optional city filter
    
    Returns:
        list: List of tuples (ListedBook, Book, User, City)
    """
    with get_db() as db:
        query = (
            db.query(ListedBook, Book, User, City)
            .join(Book, ListedBook.book_id == Book.book_id)
            .join(User, ListedBook.user_id == User.user_id)
            .join(City, User.city_id == City.city_id)
            .join(DistrictCity, City.city_id == DistrictCity.city_id)
            .join(District, DistrictCity.district_id == District.district_id)
            .join(ProvinceDistrict, District.district_id == ProvinceDistrict.district_id)
            .join(Province, ProvinceDistrict.province_id == Province.province_id)
        )

        # Apply location filters
        if city_id:
            query = query.filter(User.city_id == city_id)
        elif district_id:
            query = query.filter(DistrictCity.district_id == district_id)
        elif province_id:
            query = query.filter(ProvinceDistrict.province_id == province_id)

        # Apply search filter if provided
        if search_query:
            matched_book_ids = search(search_query)
            query = query.filter(ListedBook.book_id.in_(matched_book_ids))
        else:
            query = query.order_by(desc(ListedBook.listed_date))

        books = query.offset(offset).limit(limit).all()
        return books


def get_user_location(user_id):
    """Get the user's province, district, and city IDs based on their user_id."""
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None, None, None
        city_id = user.city_id
        district_city = db.query(DistrictCity).filter(DistrictCity.city_id == city_id).first()
        district_id = district_city.district_id if district_city else None
        province_district = db.query(ProvinceDistrict).filter(ProvinceDistrict.district_id == district_id).first()
        province_id = province_district.province_id if province_district else None
        return province_id, district_id, city_id