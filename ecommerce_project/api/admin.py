from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, Category, Review


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff', 'created_at')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'birth_date', 'avatar', 'bio')}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Permissions',
         {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'price', 'stock', 'status', 'hoba', 'product_owner' , 'is_featured', 'rating', 'created_at')
    list_filter = ('status', 'is_featured', 'category', 'created_at')
    search_fields = ('name', 'description', 'owner__email')
    list_per_page = 10
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('status', 'is_featured')
    ordering = ('-created_at',)

    def product_owner(self, obj):
        return obj.owner.get_full_name()

    @admin.display(ordering='price', description='Price Category')
    def hoba(self, Product):
        if Product.price < 0:
            return "Invalid Price"
        elif Product.discount_price < 500:
            return "Cheap"
        else:
            return "Expensive"
        
        

    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'description', 'owner', 'category')}),
        ('Pricing', {'fields': ('price', 'discount_price', 'stock')}),
        ('Media', {'fields': ('image',)}),
        ('Status', {'fields': ('status', 'is_featured')}),
        ('Stats', {'fields': ('rating', 'views')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')

