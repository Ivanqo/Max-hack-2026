from django.contrib import admin
from .models import Skill, CareerRole, CareerRoleSkill, StudentSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'university', 'created_at']
    list_filter = ['category', 'university', 'created_at']
    search_fields = ['name', 'university__name']
    ordering = ['category', 'name']

    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'university')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


class CareerRoleSkillInline(admin.TabularInline):
    model = CareerRoleSkill
    extra = 1
    autocomplete_fields = ['skill']
    fields = ['skill', 'required_level', 'weight']


@admin.register(CareerRole)
class CareerRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'university', 'active', 'skill_count', 'created_at']
    list_filter = ['active', 'university', 'created_at']
    search_fields = ['name', 'description', 'university__name']
    ordering = ['university', 'name']
    inlines = [CareerRoleSkillInline]

    fieldsets = (
        (None, {
            'fields': ('university', 'name', 'description', 'active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def skill_count(self, obj):
        return obj.required_skills.count()
    skill_count.short_description = 'Skills Required'


@admin.register(CareerRoleSkill)
class CareerRoleSkillAdmin(admin.ModelAdmin):
    list_display = ['career_role', 'skill', 'required_level', 'weight', 'created_at']
    list_filter = ['required_level', 'career_role__university', 'created_at']
    search_fields = ['career_role__name', 'skill__name']
    autocomplete_fields = ['career_role', 'skill']
    ordering = ['career_role', '-weight']

    fieldsets = (
        (None, {
            'fields': ('career_role', 'skill', 'required_level', 'weight')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ['student', 'skill', 'level', 'verified', 'updated_at']
    list_filter = ['level', 'verified', 'skill__category', 'created_at']
    search_fields = ['student__user__first_name', 'student__user__last_name',
                     'student__user__email', 'skill__name']
    autocomplete_fields = ['student', 'skill']
    ordering = ['student', '-level', 'skill__name']

    fieldsets = (
        (None, {
            'fields': ('student', 'skill', 'level', 'verified')
        }),
        ('Evidence', {
            'fields': ('evidence',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    actions = ['mark_as_verified', 'mark_as_unverified']

    def mark_as_verified(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} student skills marked as verified.')
    mark_as_verified.short_description = 'Mark selected skills as verified'

    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(verified=False)
        self.message_user(request, f'{updated} student skills marked as unverified.')
    mark_as_unverified.short_description = 'Mark selected skills as unverified'
