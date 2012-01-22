from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from views import ConfigureForm, InitialConfiguration, FormPreview, TemplateListing
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns( '',
        
    
    url( r'^create/$', InitialConfiguration,{'template':'dynamicforms/initial.html'}, name = 'initialform' ),
    
    url( r'^(?P<slug>[-\w]+)/preview/$', FormPreview,{'template':'dynamicforms/preview.html'}, name = 'configureform' ),
    
    url( r'^(?P<slug>[-\w]+)/(?P<type>[-\w]+)/$', ConfigureForm,{'template':'dynamicforms/formconfig.html'}, name = 'configureform' ),
    
    url( r'^template-listing/$', TemplateListing,{'template':'dynamicforms/template_listing.html','app':'djangoform','model_name':'FormConfiguration'}, name = 'template_listing' ),
    
    
    )