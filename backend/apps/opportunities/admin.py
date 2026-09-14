from django.contrib import admin
from .models import Opportunity, OpportunitySkill, SavedOpportunity, MatchResult


class OpportunitySkillInline(admin.TabularInline):
    model = OpportunitySkill
    extra = 1
    fields = ['skill', 'required_level', 'weight']


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'type',
        'university',
        'verified_status',
        'published',
        'deadline',
        'created_at'
    ]
    list_filter = [
        'type',
        'verified_status',
        'published',
        'university',
        'created_at'
    ]
    search_fields = ['title', 'description', 'university', 'requirements']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [OpportunitySkillInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('university', 'type', 'title', 'description')
        }),
        ('Requirements', {
            'fields': ('requirements', 'audience')
        }),
        ('Publishing', {
            'fields': ('deadline', 'source_url', 'verified_status', 'published')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OpportunitySkill)
class OpportunitySkillAdmin(admin.ModelAdmin):
    list_display = ['opportunity', 'skill', 'required_level', 'weight']
    list_filter = ['required_level', 'weight']
    search_fields = ['skill', 'opportunity__title']
    autocomplete_fields = ['opportunity']


@admin.register(SavedOpportunity)
class SavedOpportunityAdmin(admin.ModelAdmin):
    list_display = ['student', 'opportunity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['student__username', 'opportunity__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'opportunity', 'score', 'calculated_at']
    list_filter = ['score', 'calculated_at']
    search_fields = ['student__username', 'opportunity__title']
    readonly_fields = ['calculated_at']
    date_hierarchy = 'calculated_at'

    fieldsets = (
        ('Match Information', {
            'fields': ('student', 'opportunity', 'score')
        }),
        ('Analysis', {
            'fields': ('reasons', 'gaps')
        }),
        ('Metadata', {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        }),
    )
