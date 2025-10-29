from django.contrib import admin

from apps.models import User, Product, Region, District, Category, AdminSetting


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    exclude = 'slug',

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    pass

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(AdminSetting)
class AdminSettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        max_instances = 1
        if self.model.objects.count() >= max_instances:
            return False
        return super().has_add_permission(request)
