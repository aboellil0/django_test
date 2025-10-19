from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Product, Category, Review, Customer, Vendor

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Unified serializer for user registration - creates user and profile based on role"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['customer', 'vendor', 'admin'], default='customer')
    
    # Vendor-specific fields (optional, only used when role='vendor')
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    company_website = serializers.URLField(required=False, allow_blank=True)
    company_address = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'first_name',
                  'last_name', 'phone', 'address', 'city', 'country', 
                  'postal_code', 'bio', 'birth_date', 'role',
                  'company_name', 'company_website', 'company_address')
    
    def validate(self, attrs):
        # Validate password match
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        # Validate vendor-specific fields if role is vendor
        role = attrs.get('role', 'customer')
        if role == 'vendor':
            if not attrs.get('company_name'):
                raise serializers.ValidationError(
                    {"company_name": "Company name is required for vendor registration"}
                )
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        role = validated_data.get('role', 'customer')
        
        # Extract vendor-specific fields
        company_name = validated_data.pop('company_name', None)
        company_website = validated_data.pop('company_website', None)
        company_address = validated_data.pop('company_address', None)
        
        # Create user with specified role
        user = User(**validated_data)
        user.set_password(password)
        
        # Set admin permissions if role is admin
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        
        user.save()
        
        # Create profile based on role
        if role == 'customer':
            Customer.objects.create(user=user)
        elif role == 'vendor':
            Vendor.objects.create(
                user=user,
                company_name=company_name,
                company_website=company_website or '',
                company_address=company_address or ''
            )
        # Admin role doesn't need a separate profile
        
        return user


class UserSerializer(serializers.ModelSerializer):
    total_products = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'address',
                  'city', 'country', 'postal_code', 'role', 'bio', 'avatar',
                  'birth_date', 'is_verified', 'is_active', 'total_products',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_verified')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'user_email', 'rating', 'comment', 'created_at')
        read_only_fields = ('user',)


class ProductSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.ReadOnlyField()
    final_price = serializers.ReadOnlyField()
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('owner', 'slug', 'views', 'created_at', 'updated_at')


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('name', 'description', 'price', 'discount_price', 'stock',
                  'image', 'status', 'category', 'is_featured')


class CustomerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    preferred_categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Customer
        fields = ('id', 'user', 'user_email', 'user_name', 'user_phone', 
                  'loyalty_points', 'preferred_categories')
        read_only_fields = ('user',)
    
    def validate_user(self, value):
        """Ensure user has customer role"""
        if value.role != 'customer':
            raise serializers.ValidationError(
                "User must have 'customer' role to create a customer profile"
            )
        return value


class VendorSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = Vendor
        fields = ('id', 'user', 'user_email', 'user_name', 'user_phone',
                  'company_name', 'company_website', 'company_address', 'verified')
        read_only_fields = ('user', 'verified')
    
    def validate_user(self, value):
        """Ensure user has vendor role"""
        if value.role != 'vendor':
            raise serializers.ValidationError(
                "User must have 'vendor' role to create a vendor profile"
            )
        return value
