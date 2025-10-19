from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Customer, Vendor

User = get_user_model()


@receiver(pre_save, sender=User)
def manage_user_role_change(sender, instance, **kwargs):
    """
    Delete Customer or Vendor profile when user role changes to something else
    """
    if instance.pk:  # Only for existing users
        try:
            old_user = User.objects.get(pk=instance.pk)
            old_role = old_user.role
            new_role = instance.role
            
            # If role changed from customer to something else
            if old_role == 'customer' and new_role != 'customer':
                try:
                    Customer.objects.filter(user=instance).delete()
                    print(f"Customer profile deleted for user {instance.email}")
                except Customer.DoesNotExist:
                    pass
            
            # If role changed from vendor to something else
            if old_role == 'vendor' and new_role != 'vendor':
                try:
                    Vendor.objects.filter(user=instance).delete()
                    print(f"Vendor profile deleted for user {instance.email}")
                except Vendor.DoesNotExist:
                    pass
                    
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def auto_create_profile(sender, instance, created, **kwargs):
    """
    Automatically create Customer or Vendor profile when user is created
    based on their role (optional - uncomment if you want auto-creation)
    """
    # Uncomment below if you want automatic profile creation on user registration
    # if created:
    #     if instance.role == 'customer':
    #         Customer.objects.get_or_create(user=instance)
    #     elif instance.role == 'vendor':
    #         Vendor.objects.get_or_create(
    #             user=instance,
    #             defaults={'company_name': f"{instance.get_full_name()}'s Company"}
    #         )
    pass
