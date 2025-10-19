from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg
from .models import Product, Category, Review, Customer, Vendor
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    ProductSerializer, ProductCreateSerializer,
    CategorySerializer, ReviewSerializer,
    CustomerSerializer, VendorSerializer
)
from .permissions import IsOwnerOrReadOnly, IsOwner

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """User Registration Endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User CRUD operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'email']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products by user"""
        user = self.get_object()
        products = user.products.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product CRUD operations"""
    queryset = Product.objects.select_related('owner', 'category').prefetch_related('reviews')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'owner__email']
    ordering_fields = ['created_at', 'price', 'rating', 'views']
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [IsOwnerOrReadOnly()]

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """Get current user's products"""
        products = Product.objects.filter(owner=request.user)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = Product.objects.filter(is_featured=True, status='published')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, slug=None):
        """Increment product view count"""
        product = self.get_object()
        product.views += 1
        product.save()
        return Response({'views': product.views})

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, slug=None):
        """Get or create product review"""
        product = self.get_object()

        if request.method == 'GET':
            reviews = product.reviews.all()
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            # Update product rating
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
            product.rating = avg_rating or 0
            product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category CRUD operations"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer CRUD operations"""
    queryset = Customer.objects.select_related('user').prefetch_related('preferred_categories')
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['loyalty_points', 'user__created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's customer profile"""
        try:
            customer = Customer.objects.get(user=request.user)
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        """Create customer profile for current user"""
        if hasattr(request.user, 'customer_profile'):
            return Response(
                {'error': 'Customer profile already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user.role != 'customer':
            return Response(
                {'error': 'User must have customer role to create a customer profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customer = Customer.objects.create(user=request.user)
        serializer = self.get_serializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'])
    def update_my_profile(self, request):
        """Update current user's customer profile"""
        try:
            customer = Customer.objects.get(user=request.user)
            serializer = self.get_serializer(customer, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def add_preferred_category(self, request):
        """Add a preferred category"""
        try:
            customer = Customer.objects.get(user=request.user)
            category_id = request.data.get('category_id')
            category = Category.objects.get(id=category_id)
            customer.preferred_categories.add(category)
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


class VendorViewSet(viewsets.ModelViewSet):
    """ViewSet for Vendor CRUD operations"""
    queryset = Vendor.objects.select_related('user')
    serializer_class = VendorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['company_name', 'verified', 'user__created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's vendor profile"""
        try:
            vendor = Vendor.objects.get(user=request.user)
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        except Vendor.DoesNotExist:
            return Response(
                {'error': 'Vendor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        """Create vendor profile for current user"""
        if hasattr(request.user, 'vendor_profile'):
            return Response(
                {'error': 'Vendor profile already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user.role != 'vendor':
            return Response(
                {'error': 'User must have vendor role to create a vendor profile'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'])
    def update_my_profile(self, request):
        """Update current user's vendor profile"""
        try:
            vendor = Vendor.objects.get(user=request.user)
            serializer = self.get_serializer(vendor, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Vendor.DoesNotExist:
            return Response(
                {'error': 'Vendor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def verified(self, request):
        """Get all verified vendors"""
        vendors = Vendor.objects.filter(verified=True)
        serializer = self.get_serializer(vendors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """Verify a vendor (admin only)"""
        vendor = self.get_object()
        vendor.verified = True
        vendor.save()
        return Response({'status': 'Vendor verified successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def unverify(self, request, pk=None):
        """Unverify a vendor (admin only)"""
        vendor = self.get_object()
        vendor.verified = False
        vendor.save()
        return Response({'status': 'Vendor unverified successfully'})

