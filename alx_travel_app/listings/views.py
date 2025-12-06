from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer
from .permissions import IsOwnerOrReadOnly, IsBookingOwnerOrHost

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Listings.
    
    Endpoints:
    GET /api/listings/ - List all listings
    POST /api/listings/ - Create a new listing
    GET /api/listings/{id}/ - Retrieve a specific listing
    PUT /api/listings/{id}/ - Update a listing
    PATCH /api/listings/{id}/ - Partial update of a listing
    DELETE /api/listings/{id}/ - Delete a listing
    GET /api/listings/{id}/bookings/ - Get all bookings for a listing
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'city', 'country', 'is_available']
    search_fields = ['title', 'description', 'city', 'country']
    ordering_fields = ['price_per_night', 'created_at', 'updated_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by price range if provided
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price_per_night__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_per_night__lte=max_price)
        
        # Filter by number of guests if provided
        min_guests = self.request.query_params.get('min_guests')
        if min_guests:
            queryset = queryset.filter(max_guests__gte=min_guests)
        
        return queryset
    
    def perform_create(self, serializer):
        # Set the host to the current user when creating a listing
        serializer.save(host=self.request.user)
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Get all bookings for a specific listing"""
        listing = self.get_object()
        bookings = listing.bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_dates(self, request, pk=None):
        """Get available dates for a listing"""
        listing = self.get_object()
        
        # Get all bookings that block dates
        bookings = listing.bookings.filter(
            status__in=['confirmed', 'pending']
        )
        
        # Return dates that are already booked
        booked_dates = []
        for booking in bookings:
            # Generate list of dates between check_in and check_out
            # (excluding check_out date)
            current_date = booking.check_in
            while current_date < booking.check_out:
                booked_dates.append(current_date.isoformat())
                current_date += datetime.timedelta(days=1)
        
        return Response({
            'listing_id': listing.id,
            'booked_dates': booked_dates,
            'message': 'These dates are already booked'
        })

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Bookings.
    
    Endpoints:
    GET /api/bookings/ - List all bookings
    POST /api/bookings/ - Create a new booking
    GET /api/bookings/{id}/ - Retrieve a specific booking
    PUT /api/bookings/{id}/ - Update a booking
    PATCH /api/bookings/{id}/ - Partial update of a booking
    DELETE /api/bookings/{id}/ - Delete a booking
    POST /api/bookings/{id}/cancel/ - Cancel a booking
    POST /api/bookings/{id}/confirm/ - Confirm a booking (host only)
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingOwnerOrHost]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'listing', 'guest']
    ordering_fields = ['check_in', 'check_out', 'created_at', 'total_price']
    
    def get_queryset(self):
        user = self.request.user
        
        # Hosts can see all bookings for their listings
        # Guests can only see their own bookings
        if user.is_staff:
            return super().get_queryset()
        
        # Filter bookings where user is guest or host of the listing
        return Booking.objects.filter(
            Q(guest=user) | Q(listing__host=user)
        )
    
    def perform_create(self, serializer):
        # Set the guest to the current user when creating a booking
        serializer.save(guest=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if booking.status == 'cancelled':
            return Response(
                {'error': 'Booking is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only guest or host can cancel
        if request.user not in [booking.guest, booking.listing.host]:
            return Response(
                {'error': 'You do not have permission to cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking (host only)"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': f'Booking is already {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only host can confirm
        if request.user != booking.listing.host:
            return Response(
                {'error': 'Only the host can confirm bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'confirmed'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings for the current user"""
        user = request.user
        today = timezone.now().date()
        
        # Get upcoming bookings where user is guest or host
        bookings = Booking.objects.filter(
            Q(guest=user) | Q(listing__host=user),
            check_out__gte=today,
            status__in=['confirmed', 'pending']
        ).order_by('check_in')
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)