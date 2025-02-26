from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'data_publicacao', 'ativo')
    list_filter = ('ativo', 'data_publicacao')
    search_fields = ('titulo', 'empresa', 'descricao')
    ordering = ('-data_publicacao',)
