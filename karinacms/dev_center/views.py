from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .forms import DevForm, CampaignForm, DevCommentForm, UserForm, UserInfoForm, ProductForm, DevStatusForm
from .models import Campaign, Dev, DevComment, DevStatus, UserInfo, Product
from django.http import HttpResponseRedirect, HttpResponse
from datetime import datetime
from django.conf import settings

from rest_framework import viewsets, permissions
from .serializers import DevSerializer
from .custom_permissions import PostOnly

class DevViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows devs being viewed and edited
    """
    model = Dev
    serializer_class = DevSerializer
    permission_classes = [PostOnly]


def register(request):
	registered = False
	userForm = UserForm(request.POST or None)
	userInfoForm = UserInfoForm(request.POST or None)
	if userForm.is_valid() and userInfoForm.is_valid():
		user = userForm.save()
		user.set_password(user.password)
		user.save()
		userInfo = userInfoForm.save(commit=False)
		userInfo.user = user
		userInfo.save()
		registered = True
	
	context = {'userForm': userForm, 'userInfoForm': userInfoForm, 'registered': registered}
	return render(request, 'dev_center/register.html', context)

def user_login(request):
	msg = None
	next = None

	if request.method == 'POST':
		username = request.POST['username'];
		password = request.POST['password'];
		u = authenticate(username=username, password=password)
		if u and u.is_active:
			login(request, u)
			redirect_url = request.GET.get('next') or '/devs/'
			return HttpResponseRedirect(redirect_url)
		else:
			msg = 'Invalid credentials or inactive account'
		# context.form = userCredentialsForm
	context = {'msg': msg}
	return render(request, 'dev_center/login.html', context)

@login_required
def dev_form(request, campaign_name='eartohear.info'):
	campaign = None
	try:
		campaign = Campaign.objects.get(name=campaign_name)
		print campaign
	except Campaign.DoesNotExist:
		pass  # do stuff

	form = DevForm(request.POST or None)

	context_dict = {'form': form, 'title': 'Create new dev'}
	if form.is_valid():
		# do stuff
		dev = form.save(commit=False)
		dev.campaign = campaign
		dev.save()
		context_dict['success'] = True

	return render(request, 'dev_center/dev_form.html', context_dict)

@login_required
def dev_edit_form(request, dev_id):
	devData=None
	form=None
	devEdited=False
	notFound=False
	title=None
	try:
		devData = Dev.objects.get(id=dev_id)
		print devData.id
	except Dev.DoesNotExist:
		pass #pass

	if devData:
		title = 'Edit dev - ' + devData.first_name + ' ' + devData.last_name
		form = DevForm(request.POST or None, instance=devData)
		if form.is_valid():
			#save for and show success			
			devData.save()
			form.save()
			devEdited = True
	else:
		#no such dev
		title = 'No such dev'
		notFound = True
	context_dict = {'title': title, 'notFound': notFound, 'devEdited': devEdited, 'form': form}
	return render(request, 'dev_center/dev_form.html', context_dict)

@login_required
def product_list(request):
	productAdded = False
	products = Product.objects.annotate(dev_count=Count('product_devs'))
	#products = = Product.objects.all()

	form=ProductForm(request.POST or None)
	if form.is_valid():
		product = form.save()
		product.save()
		productAdded = True
	context_dict = {'products': products, 'form': form, 'productAdded': productAdded, 'obj_type': 'Product'}
	return render(request, 'dev_center/product_list.html', context_dict)

@login_required
def search_list(request):
	object_type = request.GET['object_type']
	query_string = request.GET['query_string']
	if object_type == 'Campaign':
		model_class = Campaign
		objStr = 'campaign'
	elif object_type == 'Product':
		model_class = Product
		objStr = 'product'
	elif object_type == 'Status':
		model_class = DevStatus
		objStr = 'status'
	elif object_type == 'Dev':
		model_class = Dev
		objStr = 'dev'
	result_set = model_class.objects.filter(name__icontains=query_string)
	return render(request, 'dev_center/common/generic_list.html', {'obj': result_set, 'objStr': objStr})
	
@login_required
def delete_obj(request, obj_type, obj_id):
	if obj_type == 'campaign':
		title = 'Delete campagign?'
		model_class = Campaign
		redirect_url = 'campaign_list' 
	elif obj_type == 'product':
 		title = 'Delete product?'
 		model_class = Product
 		redirect_url = 'product_list'
 	elif obj_type == 'status':
 		title = 'Delete status?'
 		model_class = DevStatus
 		redirect_url = 'status_list'
 	else:
 		raise Http404

	success = None
	try:
		obj = model_class.objects.get(pk=obj_id)
	except (Campaign.DoesNotExist, Product.DoesNotExist):
		raise Http404

	if request.method == "POST" and obj:
		obj.delete()
		return redirect(redirect_url)
	
	return render(request, 'dev_center/common/delete_obj.html', {'title': delete_obj, 'success': success, 'object': obj})


@login_required
def edit_obj (request, obj_type, obj_id):
	if obj_type == 'campaign':
		model = Campaign
		form_class = CampaignForm
		title = 'Edit campaign'
		redirect_url = 'campaign_list'
	elif obj_type == 'product':
		model = Product
		form_class = ProductForm
		title = 'Edit product'
		redirect_url = 'product_list'
	elif obj_type == 'status':
		model = DevStatus
		form_class = DevStatusForm
		title = 'Edit dev status'
		redirect_url = 'status_list'
	else:
		raise Http404

	success = None
	try:
		obj = model.objects.get(pk=obj_id)
	except model.DoesNotExist:
		raise Http404

	form = form_class(request.POST or None, instance=obj)
	
	if form.is_valid() and obj:
		form.save()
		return redirect(redirect_url)
	return render(request, 'dev_center/common/edit_obj.html', {'title': title, 'formTitle': obj.name, 'form': form})



@login_required
def campaign_list(request):
	campaignAdded = False
	campaigns = Campaign.objects.annotate(dev_count=Count('campaign_devs'))
	#products = = Product.objects.all()
	form=CampaignForm(request.POST or None)
	if form.is_valid():
		campaign = form.save()
		campaignAdded = True
	context_dict = {'campaigns': campaigns, 'form': form, 'campaignAdded': campaignAdded, 'obj_type': 'Campaign'}
	return render(request, 'dev_center/campaign_list.html', context_dict)

@login_required
def status_list(request):
	statusAdded = False
	statuses = DevStatus.objects.annotate(dev_count=Count('status_devs'))
	#products = = Product.objects.all()
	form=DevStatusForm(request.POST or None)
	if form.is_valid():
		status = form.save()
		statusAdded = True
	context_dict = {'statuses': statuses, 'form': form, 'statusAdded': statusAdded, 'obj_type': 'Status'}
	return render(request, 'dev_center/status_list.html', context_dict)


@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/devs/')
	
def index(request):
	devs = Dev.objects.all().order_by('phone')
	context_dict = {'devs': devs}
	if request.session.has_key('last_visit'):
		last_visit = request.session.get('last_visit')
		visits = request.session.get('visits', 0)
		if(datetime.now() - datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
			request.session['last_visit'] = str(datetime.now())	
			request.session['visits'] = visits + 1
	else:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = 1
	return render(request, 'dev_center/index.html', context_dict)

@login_required
def dev_page(request, dev_name=None):
	split_name = dev_name.split('-')
	devs = None
	comment_list = None
	comment_success = False

	devs = Dev.objects.filter(first_name = split_name[0], last_name = split_name[1])

	form = DevCommentForm(request.POST or None)
	if devs:
		comment_list = DevComment.objects.filter(dev = devs[0])
	if devs and form.is_valid():
		comment = form.save(commit=False)
		comment.dev = devs[0]#change this to many to many blat
		comment.save()
		comment_success = True
	context_dict = {'devs': devs, 'title': dev_name, 'form': form, 'comment_list': comment_list, 'comment_success': comment_success}
	return render(request, 'dev_center/dev_page.html', context_dict)