from django import forms
from django.contrib.auth.models import User
from .models import Dev, Campaign, DevComment, DevStatus, UserInfo, Product, DevHours
from django.forms.extras.widgets import SelectDateWidget

class BootstrapForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(BootstrapForm, self).__init__(*args, **kwargs)
		for field_name, field in self.fields.items():
			field.widget.attrs['class'] = 'form-control'


class UserForm(BootstrapForm):
	password = forms.CharField(widget=forms.PasswordInput())
	class Meta:
		model = User
		fields = ('username', 'password', 'email',)

class UserInfoForm(BootstrapForm):
	# site = forms.UrlField(Blank=true);
	class Meta:
		model = UserInfo
		fields = ('site',)

class ProductForm(BootstrapForm):
	class Meta:
		model = Product
		fields = ('name', 'description',)

class CampaignForm(BootstrapForm):
	class Meta:
		model = Campaign
		fields = ('name', 'description',)

class DevHoursForm(BootstrapForm):
	since = forms.DateField(widget=SelectDateWidget)
	until = forms.CharField(widget=SelectDateWidget)
	class Meta:
		model = DevHours
		fields = ('dev', 'since', 'until',)

class DevStatusForm(BootstrapForm):
	class Meta:
		model = DevStatus
		fields = ('name', 'description',)

class UserLoginForm(BootstrapForm):
	username = forms.CharField(required=True)
	password = forms.CharField(required=True, widget=forms.PasswordInput())
	class Meta:
		model = User
		fields = ('username', 'password',)

class DevForm(BootstrapForm):
	class Meta:
		model = Dev
		fields = ('first_name', 'last_name', 'city', 'phone',
				 'email', 'comment', 'status', 'campaign', 'product',
				  'asana', 'github', 'slack')


class DevCommentForm(BootstrapForm):
	title = forms.CharField(max_length=512, help_text="Summary of the call")
	comment = forms.CharField(max_length=1024, widget=forms.Textarea, help_text="Description of the call")
	def __init__(self, *args, **kwargs):
	    super(DevCommentForm, self).__init__(*args, **kwargs)
	    self.fields['title'].widget.attrs['class'] = 'form-control'
	    self.fields['comment'].widget.attrs['class'] = 'form-control'
	class Meta: 
		model = DevComment
		fields = ('title', 'comment',)


