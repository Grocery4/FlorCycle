# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StandardProfile, ModeratorProfile, DoctorProfile, PartnerProfile, PremiumProfile

# Define inlines
class StandardProfileInline(admin.StackedInline):
    model = StandardProfile
    can_delete = False
    fk_name = 'user'
    extra = 0


class ModeratorProfileInline(admin.StackedInline):
    model = ModeratorProfile
    can_delete = False
    fk_name = 'user'
    extra = 0

class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    extra = 0

class PartnerProfileInline(admin.StackedInline):
    model = PartnerProfile
    can_delete = False
    fk_name = 'user'
    extra = 0

class PremiumProfileInline(admin.StackedInline):
    model = PremiumProfile
    can_delete = False
    extra = 0

# Custom UserAdmin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "user_type", "is_staff", "is_active")
    ordering = ("email",)
    
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "user_type"),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        inlines = []
        if obj.user_type == 'STANDARD':
            inlines = [StandardProfileInline(self.model, self.admin_site)]
        if obj.user_type == 'MODERATOR':
            inlines = [ModeratorProfileInline(self.model, self.admin_site)]
        elif obj.user_type == 'DOCTOR':
            inlines = [DoctorProfileInline(self.model, self.admin_site)]
        elif obj.user_type == 'PARTNER':
            inlines = [PartnerProfileInline(self.model, self.admin_site)]
        elif obj.user_type == 'PREMIUM':
            inlines = [PremiumProfileInline(self.model, self.admin_site)]
        return inlines
