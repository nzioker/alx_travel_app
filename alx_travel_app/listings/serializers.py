from rest_framework import serializers
from .models import Listing, Booking
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ListingSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    host_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='host',
        write_only=True
    )
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'host', 'host_id', 'title', 'description', 'property_type',
            'price_per_night', 'bedrooms', 'bathrooms', 'max_guests',
            'address', 'city', 'country', 'amenities', 'is_available',
            'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'average_rating']
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return None

class BookingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.filter(is_available=True),
        source='listing',
        write_only=True
    )
    guest = UserSerializer(read_only=True)
    guest_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='guest',
        write_only=True
    )
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_id', 'guest', 'guest_id',
            'check_in', 'check_out', 'number_of_guests', 'total_price',
            'status', 'special_requests', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_price', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validate check-in and check-out dates
        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError(
                "Check-in date must be before check-out date."
            )
        
        # Validate number of guests
        listing = data['listing']
        if data['number_of_guests'] > listing.max_guests:
            raise serializers.ValidationError(
                f"Number of guests cannot exceed {listing.max_guests}."
            )
        
        # Check for booking conflicts
        conflicting_bookings = Booking.objects.filter(
            listing=listing,
            check_out__gt=data['check_in'],
            check_in__lt=data['check_out'],
            status__in=['pending', 'confirmed']
        ).exclude(id=self.instance.id if self.instance else None)
        
        if conflicting_bookings.exists():
            raise serializers.ValidationError(
                "This listing is already booked for the selected dates."
            )
        
        # Calculate total price
        days = (data['check_out'] - data['check_in']).days
        data['total_price'] = days * listing.price_per_night
        
        return data