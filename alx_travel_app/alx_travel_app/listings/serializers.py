from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ListingSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'address', 'city', 'country',
            'price_per_night', 'max_guests', 'bedrooms', 'bathrooms',
            'property_type', 'amenities', 'is_available', 'host',
            'average_rating', 'review_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['host', 'created_at', 'updated_at']

class BookingSerializer(serializers.ModelSerializer):
    guest = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(), 
        source='listing',
        write_only=True
    )
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_id', 'guest', 'check_in', 'check_out',
            'total_price', 'guests_count', 'status', 'special_requests',
            'duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['guest', 'total_price', 'created_at', 'updated_at']
    
    def get_duration(self, obj):
        return (obj.check_out - obj.check_in).days
    
    def validate(self, data):
        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError("Check-out date must be after check-in date")
        
        if data['guests_count'] > data['listing'].max_guests:
            raise serializers.ValidationError(
                f"Number of guests exceeds maximum allowed ({data['listing'].max_guests})"
            )
        
        return data

class ReviewSerializer(serializers.ModelSerializer):
    guest = UserSerializer(read_only=True)
    booking_id = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(),
        source='booking',
        write_only=True
    )
    
    class Meta:
        model = Review
        fields = [
            'id', 'booking', 'booking_id', 'guest', 'listing', 'rating',
            'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['guest', 'listing', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value