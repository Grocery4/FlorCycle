# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile

# Define inlines
class ModeratorProfileInline(admin.StackedInline):
    model = ModeratorProfile
    can_delete = True
    extra = 0
    max_num = 1

class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = True
    extra = 0
    max_num = 1

class PartnerProfileInline(admin.StackedInline):
    model = PartnerProfile
    can_delete = True
    fk_name = 'user'
    extra = 0
    max_num = 1

class PremiumProfileInline(admin.StackedInline):
    model = PremiumProfile
    can_delete = True
    extra = 0
    max_num = 1

# Custom UserAdmin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = [
        ModeratorProfileInline,
        DoctorProfileInline,
        PartnerProfileInline,
        PremiumProfileInline
    ]

    list_display = ("email", "user_type", "is_staff", "is_active")
    ordering = ("email",)
    
    fieldsets = (
        (None, {"fields": ("email", "password", "user_type")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
    )
