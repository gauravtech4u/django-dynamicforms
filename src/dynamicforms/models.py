from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

class FormConfiguration( models.Model ):
    slug=models.SlugField()
    name=models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType)
    object_id    = models.CharField(max_length=100)
    fields = models.TextField( blank = True, null = True )
    description = models.TextField( blank = True )
    display_flag            =  models.BooleanField(default = True)
    created_date            =  models.DateTimeField(auto_now = True)
    modified_date           =  models.DateTimeField(auto_now_add = True)
    
    objects = models.Manager()
    
    def __unicode__( self ):
        return self.name

    def save( self, slug_field = None ):
        self.slug = slugify( self.name )
        super( FormConfiguration, self ).save()