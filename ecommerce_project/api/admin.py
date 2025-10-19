from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, Product, Category, Review, Customer, Vendor


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with role selection"""
    role = forms.ChoiceField(
        choices=User.USER_ROLES,
        required=True,
        help_text="Select the user role. Profile will be created automatically."
    )
    
    # Customer-specific fields (optional)
    loyalty_points = forms.IntegerField(
        initial=0,
        required=False,
        help_text="Initial loyalty points for customer (default: 0)"
    )
    preferred_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select preferred categories for customer"
    )
    
    # Vendor-specific fields (optional)
    company_name = forms.CharField(
        max_length=200,
        required=False,
        help_text="Required only for vendors"
    )
    company_website = forms.URLField(
        required=False,
        help_text="Optional vendor website"
    )
    company_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional vendor address"
    )
    verified = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Mark vendor as verified"
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role', 
                  'password1', 'password2')
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company_name = cleaned_data.get('company_name')
        
        # Validate that vendors have company name
        if role == 'vendor' and not company_name:
            raise forms.ValidationError({
                'company_name': 'Company name is required for vendors.'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        user.role = role
        
        # Set staff permissions for admins
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        
        if commit:
            user.save()
            
            # Create role-specific profile
            if role == 'customer':
                Customer.objects.create(
                    user=user,
                    loyalty_points=self.cleaned_data.get('loyalty_points', 0)
                )
                # Add preferred categories
                customer = user.customer_profile
                preferred_categories = self.cleaned_data.get('preferred_categories')
                if preferred_categories:
                    customer.preferred_categories.set(preferred_categories)
                    
            elif role == 'vendor':
                Vendor.objects.create(
                    user=user,
                    company_name=self.cleaned_data.get('company_name', ''),
                    company_website=self.cleaned_data.get('company_website', ''),
                    company_address=self.cleaned_data.get('company_address', ''),
                    verified=self.cleaned_data.get('verified', False)
                )
        
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff', 'created_at')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    add_form = CustomUserCreationForm

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
            'fields': ('email', 'first_name', 'last_name', 'phone', 'role', 
                       'password1', 'password2'),
        }),
        ('Customer Information (Only for Customers)', {
            'classes': ('collapse',),
            'fields': ('loyalty_points', 'preferred_categories'),
            'description': 'Fill these fields only if creating a customer account'
        }),
        ('Vendor Information (Only for Vendors)', {
            'classes': ('collapse',),
            'fields': ('company_name', 'company_website', 'company_address', 'verified'),
            'description': 'Fill these fields only if creating a vendor account. Company name is required for vendors.'
        }),
    )
    
    def has_add_permission(self, request):
        """Allow admins to create users"""
        return request.user.is_superuser or request.user.is_staff


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'get_user_name', 'loyalty_points', 'get_user_role', 'get_user_date_joined')
    list_filter = ('user__role', 'user__is_active', 'user__created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    filter_horizontal = ('preferred_categories',)
    readonly_fields = ('user',)
    
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Customer Details', {'fields': ('loyalty_points', 'preferred_categories')}),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = 'Full Name'
    get_user_name.admin_order_field = 'user__first_name'
    
    def get_user_role(self, obj):
        return obj.user.role
    get_user_role.short_description = 'Role'
    get_user_role.admin_order_field = 'user__role'
    
    def get_user_date_joined(self, obj):
        return obj.user.created_at
    get_user_date_joined.short_description = 'Date Joined'
    get_user_date_joined.admin_order_field = 'user__created_at'
    
    def has_add_permission(self, request):
        """Customers should be created via registration endpoint"""
        return False


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'get_user_email', 'get_user_name', 'verified', 'get_user_role', 'get_user_date_joined')
    list_filter = ('verified', 'user__role', 'user__is_active', 'user__created_at')
    search_fields = ('company_name', 'user__email', 'user__first_name', 'user__last_name')
    list_editable = ('verified',)
    readonly_fields = ('user',)
    
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Company Info', {'fields': ('company_name', 'company_website', 'company_address')}),
        ('Verification', {'fields': ('verified',)}),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()
    get_user_name.short_description = 'Full Name'
    get_user_name.admin_order_field = 'user__first_name'
    
    def get_user_role(self, obj):
        return obj.user.role
    get_user_role.short_description = 'Role'
    get_user_role.admin_order_field = 'user__role'
    
    def get_user_date_joined(self, obj):
        return obj.user.created_at
    get_user_date_joined.short_description = 'Date Joined'
    get_user_date_joined.admin_order_field = 'user__created_at'
    
    def has_add_permission(self, request):
        """Vendors should be created via registration endpoint"""
        return False


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

