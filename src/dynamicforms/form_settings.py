from myapp.forms import MyForm1, MyForm2
from dynamicforms.forms import MyForm

FORM_WORKFLOW = {
                '1':{'form':MyForm1,'label':'My Form 1','groups':['A','B']},
                '2':{'form':MyForm2,'label':'My Form 2','groups':['C','D']},         
}

DEFAULT_FORM_DATA = {'fields':{}, 'extra_data':{}}
DEFAULT_FORM_DATA['fields'].update(dict([(FORM_WORKFLOW[prior]['label'],{}) for prior in FORM_WORKFLOW.keys()]))
DEFAULT_FORM_DATA['extra_data'].update(dict([(FORM_WORKFLOW[prior]['label'],{}) for prior in FORM_WORKFLOW.keys()]))
