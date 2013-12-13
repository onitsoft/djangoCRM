from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LeadForm, leadCommentForm, UserForm, UserInfoForm
from .models import Campaign, Lead, LeadComment, UserInfo
from django.http import HttpResponseRedirect, HttpResponse
from datetime import datetime
from django.conf import settings

# Create your views here.
def about(request):
	context_dict = {'boldmessage': "someStaticMessageAtAbout"}
	return render(request, 'lead_center/about.html', context_dict) 


def register(request):
	registered = False
	userForm = UserForm(request.POST or None)
	userInfoForm = UserInfoForm(request.POST or None)
	if(userForm.is_valid() and userInfoForm.is_valid()):
		user = userForm.save()
		user.set_password(user.password)
		user.save()
		userInfo = userInfoForm.save(commit=False)
		userInfo.user = user
		userInfo.save()
		registered = True
	
	context = {'userForm': userForm, 'userInfoForm': userInfoForm, 'registered': registered}
	return render(request, 'lead_center/register.html', context)

def user_login(request):
	msg = None
	if(request.POST):
		username = request.POST['username'];
		password = request.POST['password'];
		u = authenticate(username=username, password=password)
		print u
		if(u is not None and u.is_active):
			login(request, u)
			redirect_url = request.GET['next'] or '/leads/'
			return HttpResponseRedirect(redirect_url)
		else:
			msg = 'Invalid credentials or inactive account'
		# context.form = userCredentialsForm
	context = {'msg': msg}
	return render(request, 'lead_center/login.html', context)

def lead_form(request, campaign_name='main'):
	campaign = None
	try:
		campaign = Campaign.objects.get(name=campaign_name)
	except Campaign.DoesNotExist:
		pass  # do stuff

	form = LeadForm(request.POST or None)

	context_dict = {'form': form}
	if campaign and form.is_valid():
		# do stuff
		lead = form.save(commit=False)
		lead.campaign = campaign
		lead.save()
		context_dict['success'] = True

	return render(request, 'lead_center/lead_form.html', context_dict)

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/leads/')
	
def index(request):
	leads = Lead.objects.order_by('phone')
	context_dict = {'leads': leads}
	if request.session.has_key('last_visit'):
		last_visit = request.session.get('last_visit')
		visits = request.session.get('visits', 0)
		if(datetime.now() - datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
			request.session['last_visit'] = str(datetime.now())	
			request.session['visits'] = visits + 1
	else:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = 1
	return render(request, 'lead_center/index.html', context_dict)

@login_required
def lead_page(request, lead_name=None):
	split_name = lead_name.split('-')
	leads = None
	comment_list = None
	comment_success = False

	try:
		leads = Lead.objects.filter(first_name = split_name[0], last_name = split_name[1])
	except Lead.DoesNotExist:
		pass
	form = leadCommentForm(request.POST or None)
	if leads:
		comment_list = LeadComment.objects.filter(lead = leads[0])
	if leads and form.is_valid():
		comment = form.save(commit=False)
		comment.lead = leads[0]#change this to many to many blat
		comment.save()
		comment_success = True
	context_dict = {'leads': leads, 'title': lead_name, 'form': form, 'comment_list': comment_list, 'comment_success': comment_success}
	return render(request, 'lead_center/lead_page.html', context_dict)