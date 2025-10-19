from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, Product, Category, Review, Customer, Vendor


class CustomerCreationForm(UserCreationForm):
    """Form for creating customer users with customer profile"""
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'address', 
                  'city', 'country', 'postal_code', 'bio', 'birth_date')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add helpful text
        self.fields['email'].help_text = 'Customer email address'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        
        if commit:
            user.save()
            # Create customer profile
            Customer.objects.create(user=user)
        
        return user


class VendorCreationForm(UserCreationForm):
    """Form for creating vendor users with vendor profile"""
    
    # Vendor-specific fields
    company_name = forms.CharField(
        max_length=200,
        required=True,
        help_text="Company or business name"
    )
    company_website = forms.URLField(
        required=False,
        help_text="Company website URL (optional)"
    )
    company_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Company business address (optional)"
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'address', 
                  'city', 'country', 'postal_code', 'bio', 'birth_date')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].help_text = 'Vendor email address'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'vendor'
        
        if commit:
            user.save()
            # Create vendor profile
            Vendor.objects.create(
                user=user,
                company_name=self.cleaned_data.get('company_name'),
                company_website=self.cleaned_data.get('company_website', ''),
                company_address=self.cleaned_data.get('company_address', '')
            )
        
        return user


class AdminCreationForm(UserCreationForm):
    """Form for creating admin users"""
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].help_text = 'Administrator email address'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        
        if commit:
            user.save()
            # Admin doesn't need a separate profile
        
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin view for all users - read-only, displays all user types"""
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff', 'created_at')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'birth_date', 'avatar', 'bio')}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    def has_add_permission(self, request):
        """Prevent direct user creation - use specific customer/vendor/admin forms"""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Make role readonly after creation"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('role',)
        return self.readonly_fields


class CustomerUserAdmin(BaseUserAdmin):
    """Admin view specifically for creating and managing customer users"""
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'created_at', 'get_loyalty_points')
    list_filter = ('is_verified', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    add_form = CustomerCreationForm
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'birth_date', 'avatar', 'bio')}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Status', {'fields': ('is_verified', 'is_active')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        ('Customer Account Information', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
            'description': 'Create a new customer account. A customer profile will be created automatically.'
        }),
        ('Additional Information (Optional)', {
            'classes': ('wide', 'collapse'),
            'fields': ('address', 'city', 'country', 'postal_code', 'bio', 'birth_date'),
        }),
    )
    
    def get_queryset(self, request):
        """Only show customer users"""
        qs = super().get_queryset(request)
        return qs.filter(role='customer')
    
    def get_loyalty_points(self, obj):
        """Get customer loyalty points"""
        try:
            return obj.customer_profile.loyalty_points
        except:
            return 'N/A'
    get_loyalty_points.short_description = 'Loyalty Points'


class VendorUserAdmin(BaseUserAdmin):
    """Admin view specifically for creating and managing vendor users"""
    list_display = ('email', 'first_name', 'last_name', 'get_company_name', 'get_verified_status', 'created_at')
    list_filter = ('is_verified', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'vendor_profile__company_name')
    ordering = ('-created_at',)
    
    add_form = VendorCreationForm
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'birth_date', 'avatar', 'bio')}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Status', {'fields': ('is_verified', 'is_active')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        ('Vendor Account Information', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
            'description': 'Create a new vendor account. A vendor profile will be created automatically.'
        }),
        ('Company Information', {
            'classes': ('wide',),
            'fields': ('company_name', 'company_website', 'company_address'),
            'description': 'Company details for the vendor. Company name is required.'
        }),
        ('Additional Information (Optional)', {
            'classes': ('wide', 'collapse'),
            'fields': ('address', 'city', 'country', 'postal_code', 'bio', 'birth_date'),
        }),
    )
    
    def get_queryset(self, request):
        """Only show vendor users"""
        qs = super().get_queryset(request)
        return qs.filter(role='vendor')
    
    def get_company_name(self, obj):
        """Get vendor company name"""
        try:
            return obj.vendor_profile.company_name
        except:
            return 'N/A'
    get_company_name.short_description = 'Company Name'
    
    def get_verified_status(self, obj):
        """Get vendor verification status"""
        try:
            return '✓ Verified' if obj.vendor_profile.verified else '✗ Not Verified'
        except:
            return 'N/A'
    get_verified_status.short_description = 'Verification Status'


class AdminUserAdmin(BaseUserAdmin):
    """Admin view specifically for creating and managing admin users"""
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    add_form = AdminCreationForm
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        ('Admin Account Information', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
            'description': 'Create a new administrator account with full system access.'
        }),
    )
    
    def get_queryset(self, request):
        """Only show admin users"""
        qs = super().get_queryset(request)
        return qs.filter(role='admin')


# Create proxy models for cleaner admin interface
class CustomerUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Customer User'
        verbose_name_plural = 'Customer Users'

class VendorUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Vendor User'
        verbose_name_plural = 'Vendor Users'

class AdminUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'


# Register proxy models with their specific admin classes
admin.site.register(CustomerUser, CustomerUserAdmin)
admin.site.register(VendorUser, VendorUserAdmin)
admin.site.register(AdminUser, AdminUserAdmin)



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'price', 'stock', 'status', 'price_category', 'product_owner', 'is_featured', 'rating', 'created_at')
    list_filter = ('status', 'is_featured', 'category', 'created_at')
    search_fields = ('name', 'description', 'owner__email')
    list_per_page = 10
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('status', 'is_featured')
    ordering = ('-created_at',)

    def product_owner(self, obj):
        return obj.owner.get_full_name()
    product_owner.short_description = 'Owner Name'

    @admin.display(ordering='price', description='Price Category')
    def price_category(self, obj):
        if obj.price < 0:
            return "Invalid Price"
        elif obj.discount_price and obj.discount_price < 500:
            return "Cheap"
        elif obj.price < 500:
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
    ordering = ('name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

