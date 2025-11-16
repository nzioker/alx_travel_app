# ALX Travel App - Backend Components

This project implements the essential backend components for a travel booking platform using Django and Django REST Framework.

## Features

- **Database Models**: Listing, Booking, and Review models with proper relationships
- **API Serializers**: Convert model instances to JSON for API responses
- **Database Seeding**: Management command to populate database with sample data

## Models

### Listing
- Properties available for booking
- Fields: title, description, address, price_per_night, amenities, etc.
- Relationships: One-to-many with User (host)

### Booking
- Reservation records
- Fields: check_in, check_out, total_price, status, etc.
- Relationships: Many-to-one with Listing and User (guest)

### Review
- Guest reviews for listings
- Fields: rating, comment, etc.
- Relationships: One-to-one with Booking, Many-to-one with Listing and User

## Setup Instructions

1. **Duplicate the project**:
   ```bash
   cp -r alx_travel_app alx_travel_app_0x00