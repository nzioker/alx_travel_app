from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing, Booking, Review
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Seed the database with sample data for listings, bookings, and reviews'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        Review.objects.all().delete()
        Booking.objects.all().delete()
        Listing.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # Create sample users
        self.stdout.write('Creating sample users...')
        users_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'mike_wilson', 'email': 'mike@example.com', 'first_name': 'Mike', 'last_name': 'Wilson'},
            {'username': 'sarah_jones', 'email': 'sarah@example.com', 'first_name': 'Sarah', 'last_name': 'Jones'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            user.set_password('password123')
            user.save()
            users.append(user)
        
        # Create sample listings
        self.stdout.write('Creating sample listings...')
        listings_data = [
            {
                'title': 'Cozy Apartment in Downtown',
                'description': 'A beautiful cozy apartment located in the heart of downtown with amazing city views.',
                'address': '123 Main Street',
                'city': 'New York',
                'country': 'USA',
                'price_per_night': 120.00,
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'property_type': 'apartment',
                'amenities': 'WiFi, Kitchen, Air Conditioning, TV',
                'host': users[0]
            },
            {
                'title': 'Luxury Villa with Pool',
                'description': 'Stunning luxury villa with private pool and garden. Perfect for family vacations.',
                'address': '456 Beach Road',
                'city': 'Miami',
                'country': 'USA',
                'price_per_night': 350.00,
                'max_guests': 8,
                'bedrooms': 4,
                'bathrooms': 3,
                'property_type': 'villa',
                'amenities': 'Pool, WiFi, Kitchen, Air Conditioning, TV, Garden',
                'host': users[1]
            },
            {
                'title': 'Mountain Cabin Retreat',
                'description': 'Peaceful cabin in the mountains with breathtaking views and hiking trails nearby.',
                'address': '789 Mountain View',
                'city': 'Aspen',
                'country': 'USA',
                'price_per_night': 180.00,
                'max_guests': 6,
                'bedrooms': 3,
                'bathrooms': 2,
                'property_type': 'cabin',
                'amenities': 'Fireplace, WiFi, Kitchen, Hot Tub',
                'host': users[2]
            },
            {
                'title': 'Modern City Condo',
                'description': 'Modern and stylish condo with great amenities and convenient location.',
                'address': '321 Urban Avenue',
                'city': 'San Francisco',
                'country': 'USA',
                'price_per_night': 95.00,
                'max_guests': 2,
                'bedrooms': 1,
                'bathrooms': 1,
                'property_type': 'condo',
                'amenities': 'WiFi, Gym, Pool, Air Conditioning',
                'host': users[3]
            },
            {
                'title': 'Spacious Family House',
                'description': 'Perfect for large families, this house offers plenty of space and a large backyard.',
                'address': '654 Suburban Lane',
                'city': 'Austin',
                'country': 'USA',
                'price_per_night': 220.00,
                'max_guests': 10,
                'bedrooms': 5,
                'bathrooms': 3,
                'property_type': 'house',
                'amenities': 'WiFi, Kitchen, Air Conditioning, TV, Garden, BBQ',
                'host': users[0]
            }
        ]
        
        listings = []
        for listing_data in listings_data:
            listing = Listing.objects.create(**listing_data)
            listings.append(listing)
        
        # Create sample bookings
        self.stdout.write('Creating sample bookings...')
        status_choices = ['confirmed', 'completed', 'pending']
        
        for i in range(15):
            listing = random.choice(listings)
            guest = random.choice(users)
            if guest == listing.host:
                continue  # Skip if guest is the host
            
            check_in = datetime.now().date() + timedelta(days=random.randint(1, 30))
            check_out = check_in + timedelta(days=random.randint(1, 14))
            guests_count = random.randint(1, listing.max_guests)
            duration = (check_out - check_in).days
            total_price = duration * listing.price_per_night
            
            booking = Booking.objects.create(
                listing=listing,
                guest=guest,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                guests_count=guests_count,
                status=random.choice(status_choices)
            )
            
            # Create reviews for completed bookings
            if booking.status == 'completed' and random.random() > 0.3:  # 70% chance of review
                Review.objects.create(
                    booking=booking,
                    guest=guest,
                    listing=listing,
                    rating=random.randint(3, 5),
                    comment=f'Great stay at {listing.title}! The host was wonderful and the place was exactly as described.'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with:\n'
                f'- {User.objects.count()} users\n'
                f'- {Listing.objects.count()} listings\n'
                f'- {Booking.objects.count()} bookings\n'
                f'- {Review.objects.count()} reviews'
            )
        )