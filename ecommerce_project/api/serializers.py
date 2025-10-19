from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Product, Category, Review

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'first_name',
                  'last_name', 'phone', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
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
