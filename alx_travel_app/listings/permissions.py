from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.host == request.user

class IsBookingOwnerOrHost(permissions.BasePermission):
    """
    Custom permission to allow booking owners (guests) and listing hosts
    to view and modify bookings.
    """
    def has_object_permission(self, request, view, obj):
        # Users can always see their own bookings or bookings for their listings
        if request.method in permissions.SAFE_METHODS:
            return obj.guest == request.user or obj.listing.host == request.user
        
        # For write operations, more specific rules apply
        # Guests can cancel their own bookings
        # Hosts can confirm bookings
        return obj.guest == request.user or obj.listing.host == request.user