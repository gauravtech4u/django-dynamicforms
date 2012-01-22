from django.contrib import admin
from models import FormConfiguration


class FormConfigurationAdmin( admin.ModelAdmin ):
    
    model = FormConfiguration
    list_display = ( 'name', 'created_date', 'modified_date' )
    list_filter = [ 'created_date', 'modified_date' ]
    ordering = ['name']
    search_fields = ['name']
    prepopulated_fields = {"slug": [ 'name' ]}

admin.site.register( FormConfiguration, FormConfigurationAdmin )

