from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet, ProductViewSet, CategoryViewSet, CustomerViewSet, VendorViewSet,
    register_customer, register_vendor, register_admin
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'vendors', VendorViewSet, basename='vendor')

urlpatterns = [
    # JWT Authentication
    path('auth/register/customer/', register_customer, name='register_customer'),
    path('auth/register/vendor/', register_vendor, name='register_vendor'),
    path('auth/register/admin/', register_admin, name='register_admin'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Routes
    path('', include(router.urls)),
]
