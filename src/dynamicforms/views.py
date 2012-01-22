from django.views.generic.base import  TemplateView
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from models import FormConfiguration
from django.forms.widgets import RadioSelect
from django.template.defaultfilters import slugify
from core.views import WrapperView, WrapperListingView, WrapperDetailView, data_to_pickle, pickle_to_data
from django.core.urlresolvers import reverse
from forms import MyForm,InitialConfigurationForm
from django.utils.datastructures import SortedDict
from form_settings import *
import operator

class DynamicFormView():
    """
    This class can be used to create dynamic forms based on dictionary passed
    """
    
    def handle_request( self ):
        raise NotImplementedError( self.handle_request )

    def get_text_field( self, label,mandatory ):
        return forms.CharField( max_length = 35, required = mandatory, label = label )
        
    def get_integer_field( self, label,mandatory ):
        return forms.IntegerField( required = mandatory, label = label )
        
    def get_choice_field( self, label, option,mandatory ):
        return forms.ChoiceField( widget = forms.Select(), choices = [item.split( ":" ) for item in option.split( ";" )] )
        
    def get_radio_field( self, label, option,mandatory ):
        return forms.ChoiceField( widget = RadioSelect, choices = [item.split( ":" ) for item in option.split( ";" )] )
        
    def get_checkbox( self, label, option,mandatory ):
        return forms.ChoiceField( widget = forms.Select(), choices = [item.split( ":" ) for item in option.split( ";" )] )
        
    def get_decimal_field( self, label, option,mandatory ):
        return forms.ChoiceField( widget = forms.Select(), choices = [item.split( ":" ) for item in option.split( ";" )] )
        

    def get_dynamic_form( self, dict ):
        """
        for eg- get_dynamic_form() called with argument dict={u't1': {'priority': u'1', 'field_type': 'textfield', 'mandatory': 1}}
        This will return a form with a t1 labelled textfield which is mandatory and row priority is 1
        """
        
        form = MyForm()
        for label, field_data in dict.items():
            print field_data
            if field_data['field_type'] == 'textfield':
                form.fields[label] = self.get_text_field( label,field_data['mandatory'] )
            if field_data['field_type'] == 'integerfield':
                form.fields[label] = self.get_integer_field( label,field_data['mandatory'] )
            if field_data['field_type'] == 'choicefield':
                form.fields[label] = self.get_choice_field( label, field_data['options'],field_data['mandatory'] )
            if field_data['field_type'] == 'radio':
                form.fields[label] = self.get_radio_field( label, field_data['options'],field_data['mandatory'] )
            if field_data['field_type'] == 'checkbox':
                form.fields[label] = self.get_checkbox( label, field_data['options'],field_data['mandatory'] )
            if field_data['field_type'] == 'textbox':
                form.fields[label] = self.get_textbox( label,field_data['mandatory'] )
            if field_data['field_type'] == 'decimalfield':
                form.fields[label] = self.get_decimal_field( label, field_data['options'],field_data['mandatory'] )
            form.fields[label].priority = field_data['priority']
        return form
    
    def get_configured_form( self, form, type, form_object, attrs_dict={} ):
        """
        This function will return form with form fields and custom fields
        pass argument attrs_dict={'class':{'label1':'class1'},'onclick':{'label2':'f1'}} for adding extra attributes to field
        """
        field_list = pickle_to_data( form_object.fields )
        dict = {}
        for k, v in form.fields.iteritems():
            if k in field_list['fields'][FORM_WORKFLOW[type]['label']]:
                v.required = field_list['fields'][FORM_WORKFLOW[type]['label']][k]
                v.priority=field_list['fields'][FORM_WORKFLOW[type]['label']][k]['priority']
                dict.update( {k:v} )
        form.fields = dict
        dynamic_form = DynamicFormView().get_dynamic_form( field_list['extra_data'][FORM_WORKFLOW[type]['label']] )
        form.fields.update( dynamic_form.fields )
        form=self.add_form_attrs(form,attrs_dict)
        form=self.add_priority(form)
        return form
    
    def add_form_attrs(self,form,attrs_dict):
        """ use this method to add extra attributes such as class,onclick to each field """
        for label,field in form.fields.items():
            for attr,dict in attrs_dict.items():
                if dict.get(label):
                    field.widget.attrs={str(attr):dict[label]}
        return form
     
    def add_priority(self,form):
        field_dict=SortedDict()
        priority_list=[(v.priority,(k,v)) for k,v in form.fields.items()]
        priority_list.sort(key=operator.itemgetter(0))
        form.fields=SortedDict([field[1] for field in priority_list])
        return form

class ConfigureForm( WrapperView ):
    """
    This class gives you dynamic form configuration admin
    makes use of FORM_WORKFLOW where forms, form labels, and order is addded
    """
    global FORM_WORKFLOW, DEFAULT_FORM_DATA

    def handle_request( self ):
        self.type = self.kwargs['type']
        self.slug = self.kwargs['slug']
        prior_list=FORM_WORKFLOW.keys()
        prior_list.sort()
        if prior_list.index(self.type)+1 != prior_list.__len__():
                self.next = prior_list.index(str(self.type))+2
        else:self.next='preview'
        if self.request.method == 'POST':
            self.get_post_form( self.type )
            return self.post_form()
        self.get_form( self.type )
        self.form_name=FORM_WORKFLOW[self.type]['label']
        self.breadcrumbs=[(key,value['label']) for key,value in FORM_WORKFLOW.items()]
        self.group_list=FORM_WORKFLOW[self.type]['groups']
        return self.configure_form()
        
    def get_form( self, type ):
        self.default_form = FORM_WORKFLOW[type]['form']()

    def get_post_form( self, type ):
        self.default_form = FORM_WORKFLOW[type]['form']( self.request.POST )
    
    def preview_form( self ):
        return render_to_response( "formpreview.html", self.__dict__, context_instance = RequestContext( self.request ) )
        
    def configure_form( self ):
        form_object = FormConfiguration.objects.get( slug = self.slug )
        field_data = pickle_to_data( form_object.fields )
        form_fields = field_data['fields'][FORM_WORKFLOW[self.type]['label']]
        self.selected_fields=form_fields.keys()
        self.extra_fields = field_data['extra_data'][FORM_WORKFLOW[self.type]['label']]
        self.mandatory_fields = [x if y.get('mandatory','0') == '1' else '0' for x, y in form_fields.items() ]
        [self.default_form.fields[x].__setattr__('priority',y['priority']) for x, y in form_fields.items()]
        [self.default_form.fields[x].__setattr__('group',y['group']) for x, y in form_fields.items()]
        return render_to_response( self.template, self.__dict__, context_instance = RequestContext( self.request ) )
        
    def post_form( self ):

            form_object = FormConfiguration.objects.get( slug = self.slug )
            field_dict = pickle_to_data( form_object.fields )
            args_dict = self.request.POST
            field_dict['fields'][FORM_WORKFLOW[self.type]['label']] = self.add_option_fields( self.request.POST.getlist( 'options' ) )
            field_dict = self.get_extra_fields( field_dict )
            if self.request.POST.get( 'delete_fields' ):
                for label in self.request.POST.getlist( 'delete_fields' ):
                    field_dict = self.delete_extra_fields( label, field_dict )
            form_object.fields = data_to_pickle( field_dict )
            form_object.save()
            return HttpResponseRedirect( reverse( 'configureform', args = [self.slug, self.next] ) )
    
    def delete_extra_fields( self, label, dict ):
        dict['extra_data'][FORM_WORKFLOW[self.type]['label']].pop(label)
        return dict
    
    def get_extra_fields( self, dict ):
        #adds configurable fields
        args_dict = self.request.POST
        textcount = int( args_dict.get( 'textfield_set-TOTAL_FORMS', '0' ) )
        radiocount = int( args_dict.get( 'radio_set-TOTAL_FORMS', '0' ) )
        checkboxcount = int( args_dict.get( 'checkbox_set-TOTAL_FORMS', '0' ) )
        textboxcount = int( args_dict.get( 'textbox_set-TOTAL_FORMS', '0' ) )
        choicecount = int( args_dict.get( 'choicefield_set-TOTAL_FORMS', '0' ) )
        intcount = int( args_dict.get( 'intfield_set-TOTAL_FORMS', '0' ) )
        decimalcount = int( args_dict.get( 'decimalfield_set-TOTAL_FORMS', '0' ) )
        for i in range( 0, textcount ):
            dict = self.add_textfield( dict, i )
        for i in range( 0, choicecount ):
            dict = self.add_choicefield( dict, i )
        for i in range( 0, intcount ):
            dict = self.add_integerfield( dict, i )
        for i in range( 0, textboxcount ):
            dict = self.add_textbox( dict, i )
        for i in range( 0, radiocount ):
            dict = self.add_radio( dict, i )
        for i in range( 0, checkboxcount ):
            dict = self.add_checkbox( dict, i )
        for i in range( 0, decimalcount ):
            dict = self.add_decimal_field( dict, i )
        return dict
    
    def add_option_fields_info( self, field_list ):
        # for mandatory fields
        pass
    
    def add_textfield( self, dict, i, **kwargs ):
        if self.request.POST.get('textfield_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['textfield_set-' + str( i )+'-name']:{'label':self.request.POST['textfield_set-' + str( i )+'-label'],'mandatory':self.request.POST.get('textfield_set-'+str(i)+'-mandatory'), 'priority':self.request.POST.get( 'textfield_set-' + str( i ) + '-priority', '0' ), 'field_type':'textfield', }} )
        return dict

    def add_choicefield( self, dict, i, **kwargs ):
        if self.request.POST.get('choicefield_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['choicefield_set-' + str( i )+'-name']:{'label':self.request.POST['choicefield_set-' + str( i )+'-label'],'mandatory':self.request.POST.get( 'choicefield_set-'+str(i)+'-mandatory', '0' ), 'priority':self.        request.POST.get( 'choicefield_set-' + str( i ) + '-priority', '0' ), 'field_type':'choicefield', 'options':self.request.POST['choicefield_set-'+str(i)+'-option'], }} )
        return dict
    
    def add_integerfield( self, dict, i, **kwargs ):
        if self.request.POST.get('intfield_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['intfield_set-' + str( i )+'-name']:{'label':self.request.POST['intfield_set-' + str( i )+'-label'],'mandatory':self.request.POST.get( 'intfield_set-'+str(i)+'-mandatory', '0' ), 'priority':self.        request.POST.get( 'intfield_set-' + str( i ) + '-priority', '0' ), 'field_type':'integerfield', }} )
        return dict

    def add_textbox( self, dict, i, **kwargs ):    
        if self.request.POST.get('textbox_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['textbox_set-' + str( i )+'-name']:{'label':self.request.POST['textbox_set-' + str( i )+'-label'],'mandatory':self.request.POST.get( 'textbox_set-'+str(i)+'-mandatory', '0' ), 'priority':self.        request.POST.get( 'textbox_set-' + str( i ) + '-priority', '0' ), 'field_type':'textbox', }} )
        return dict
    
    def add_radio( self, dict, i, **kwargs ):
        if self.request.POST.get('radio_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['radio_set-' + str( i )+'-name']:{'label':self.request.POST['radio_set-' + str( i )+'-label'],'mandatory':self.request.POST.get( 'radio_set-'+str(i)+'-mandatory', '0' ), 'priority':self.        request.POST.get( 'radio_set-' + str( i ) + '-priority', '0' ), 'field_type':'radio', 'options':self.request.POST['radio_set-'+str(i)+'-option'], }} )
        return dict
    
    def add_checkbox( self, dict, i, **kwargs ):
        if self.request.POST.get('checkbox_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['checkbox_set-' + str( i )+'-name']:{'label':self.request.POST['checkbox_set-' + str( i )+'-name'],'mandatory':self.request.POST.get( 'checkbox_set-'+str(i)+'-mandatory', '0' ), 'priority':self.        request.POST.get( 'checkbox_set-' + str( i ) + '-priority', '0' ), 'field_type':'checkbox', }} )
        return dict
    
    def add_decimal_field( self, dict, i, **kwargs ):
        if self.request.POST.get('floatfield_set-' + str( i )+'-name') != '':
                dict['extra_data'][FORM_WORKFLOW[self.type]['label']].update( {self.request.POST['floatfield_set-' + str( i )+'-name']:{'label':self.request.POST['floatfield_set-' + str( i )+'-label'],'mandatory':self.request.POST.get( 'floatfield_set-'+str(i)+'-mandatory', '0' ), 'priority':self.        request.POST.get( 'floatfield_set-' + str( i ) + '-priority', '0' ), 'field_type':'decimalfield', }} )
        return dict

    def add_option_fields( self, field_list ):
        dict = {}
        for field in field_list:
            if field in self.request.POST.getlist( 'mandatory' ):
                dict.update( {field:{'mandatory':'1','group':self.request.POST.get(field+'_group','NA'),'priority':self.request.POST.get(field+'_priority','0')}} )
            else:
                dict.update( {field:{'mandatory':'0','group':self.request.POST.get(field+'_group','NA'),'priority':self.request.POST.get(field+'_priority','0')}} )
        return dict


class FormPreview( WrapperView ):
    """
    gives you rough privew form
    """
    def handle_request( self ):
        global DEFAULT_FORM_DATA
        self.slug = self.kwargs['slug']
        form_object = FormConfiguration.objects.get( slug = self.slug )
        dynamic_obj = DynamicFormView()
        self.form_list=[]
        for key,value in FORM_WORKFLOW.items():
            self.__setattr__('form'+str(key), dynamic_obj.get_configured_form( value['form'](), key, form_object ))
            self.form_list.append(self.__getattribute__('form'+str(key)))
        return render_to_response( self.template, self.__dict__, context_instance = RequestContext( self.request ) )

    
class InitialConfiguration( WrapperView ):
    def handle_request( self ):
        self.template=self.kwargs['template']
        self.form = InitialConfigurationForm()
        if self.request.method == 'POST':
            args_dict = self.request.POST
            args_dict._mutable = True
            args_dict['slug'], args_dict['fields'] = slugify( args_dict['name'] ), data_to_pickle( DEFAULT_FORM_DATA )
            self.form = InitialConfigurationForm( args_dict )
            if self.form.is_valid():
                self.form.save()
                return HttpResponseRedirect( reverse( 'configureform', args = [args_dict['slug'], '1'] ) )
        return render_to_response( self.template, self.__dict__, context_instance = RequestContext( self.request ) )
                
class BuildForm( WrapperView ):
    def handle_request( self ):
        if self.kwargs.get( 'template' ):
            self.template = self.kwargs.get( 'template' )
        return self.__getattribute__( self.kwargs['method'] )()
    
    def build_form( self ):
        self.form = InitialApplicationForm()
        self.test = InstituteCourse.objects.all()
        if self.request.method == 'POST':
                self.request.POST._mutable=True
                courses_list=self.request.POST.pop('course')
                self.form = InitialApplicationForm( self.request.POST )
                self.form.data._mutable=True
                if self.form.is_valid():
                    obj=self.form.save()
                    for course in courses_list:
                                obj.courses.add(InstituteCourse.objects.get(id=course))
                    return HttpResponseRedirect( "/afms/" )

        return render_to_response( self.template, self.__dict__, context_instance = RequestContext( self.request ) )
        
    def edit_form( self ):
        slug=self.kwargs['slug']
        self.form=EditApplicationForm( instance=ApplicationForm.objects.get(slug=slug) )
        if self.request.method == 'POST':
                self.form=EditApplicationForm( self.request.POST,instance=ApplicationForm.objects.get(slug=self.kwargs['slug']) )
                if self.form.is_valid():
                       self.form.save()
                       return HttpResponseRedirect('/form/listing/')
        
        return render_to_response( self.template, self.__dict__, context_instance = RequestContext( self.request ) )
        
    def ajax_courses(self):
        self.course_list=InstituteCourse.objects.filter(institute__id=self.request.GET['institute'],program__id=self.request.GET['program'])
        return render_to_response( self.template, self.__dict__, context_instance = RequestContext( self.request ) )
        
class TemplateListing( WrapperListingView ):
    def extra_data( self ):
                self.template = "djangoform/template_listing.html"

class FormListing( WrapperListingView ):
    def extra_data( self ):
                self.template ="djangoform/listing.html"
                