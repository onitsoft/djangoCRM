from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .forms import DevForm, CampaignForm, DevCommentForm, UserForm, UserInfoForm, ProductForm, DevStatusForm, DevHoursForm
from .models import Campaign, Dev, DevComment, DevStatus, Product, DevHours
from django.http import HttpResponseRedirect
from datetime import datetime

from rest_framework import viewsets, permissions
from .serializers import DevSerializer
from .custom_permissions import PostOnly

from karinacms import settings
import requests
import json
import re

# import sys
# sys.path.insert(0, '/path/to/application/app/folder')


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


def parse_message(message):
    hours = minutes = 0
    if '#time' in message:
        time_tag = str(message.split('#time')[1])
        time_spent = [int(s) for s in re.findall(r'\d+', time_tag)]
        hours = time_spent[0]
        minutes = time_spent[1] if len(time_spent) > 1 else 0

    seconds = hours * 3600
    seconds += minutes * 60

    return seconds


@login_required
def set_admin_permissions(devData, github, asana):
    workspaces = get_asana_workspaces(devData)
    send_github_invitation(devData, devData.github) if devData.github != github or devData.status.name != 'inactive' else None
    send_asana_invitation(devData, devData.asana, workspaces) if devData.asana != asana or devData.status.name != 'inactive' else None
    revoke_github_permissions(devData, devData.github) if devData.status.name == 'inactive' else None
    revoke_asana_permissions(devData, devData.asana, workspaces) if devData.status.name == 'inactive' else None


@login_required
def send_github_invitation(req, user):
    # Sends a github invitation to the Team to the selected User.
    # User MUST be a username. Can't be an email.

    r = requests.put(settings.API_GITHUB_URL + settings.GIT_MEMBERSHIP + user,
                     auth=(settings.GIT_USER, settings.GIT_ACCESS_TOKEN))
    return r


@login_required
def revoke_github_permissions(req, user):
    # If the user is set to inactive, permissions to the user are denied

    r = requests.delete(settings.API_GITHUB_URL + settings.GIT_MEMBERSHIP + user,
                        auth=(settings.GIT_USER, settings.GIT_ACCESS_TOKEN))

    return r


@login_required
def get_asana_workspaces(req):
    # Gets all projects available
    # Todo: Selectable project invitation.

    work_r = requests.get(settings.API_ASANA_URL + settings.ASANA_WORKSPACES,
                          headers={'Authorization': 'Bearer %s' % settings.ASANA_ACCESS_TOKEN})

    work = json.loads(work_r.text)
    workspaces = [str(i['id']) for i in work['data']]

    return workspaces


@login_required
def send_asana_invitation(req, user, workspaces):
    # Sends an invitation to each of the available workspaces.

    responses = []
    for i in workspaces:
        r = requests.post(settings.API_ASANA_URL + settings.ASANA_WORKSPACES + i + settings.ASANA_ADD_USER,
                          data={'user': user},
                          headers={'Authorization': 'Bearer %s' % settings.ASANA_ACCESS_TOKEN})
        responses.append(r)

    return responses


@login_required
def revoke_asana_permissions(req, user, workspaces):
    # If the user is set to inactive, permissions to the user are denied

    responses = []
    for i in workspaces:
        r = requests.post(settings.API_ASANA_URL + settings.ASANA_WORKSPACES + i + settings.ASANA_DELETE_USER,
                          data={'user': user},
                          headers={'Authorization': 'Bearer %s' % settings.ASANA_ACCESS_TOKEN})
        responses.append(r)

    return responses


@login_required
def get_commits_and_hours_worked(req, params):
    # Calls functions to get all commits and parse them into hours worked

    repositories = get_github_repos(req)
    commit_responses = get_all_github_commits(req, repositories, params)
    hours_worked = get_hours_worked(commit_responses)

    return hours_worked

@login_required
def get_github_repos(req):
    # Gets All github repos of the Organization (GIT_ORGANIZATION)

    response = requests.get(settings.API_GITHUB_URL + settings.GIT_GET_REPOS,
                            auth=(settings.GIT_USER, settings.GIT_ACCESS_TOKEN))
    resp_json = response.json()
    repos = [r['name'] for r in resp_json]

    return repos


@login_required
def get_all_github_commits(req, repos, params):
    # Gets all commits from the repos of the organization

    commit_responses = {}
    for repo in repos:
        response = requests.get(settings.API_GITHUB_URL + settings.GIT_REPOS + repo + '/commits',
                                params=params,
                                auth=(settings.GIT_USER, settings.GIT_ACCESS_TOKEN))
        commit_responses[repo] = response.json()

        while 'link' in response.headers and 'next' in response.headers['link']:
            link_next_page = response.headers['link'].split('; rel="next"')[0].replace('<', '').replace('>', '')
            response = requests.get(link_next_page,
                                    params=params,
                                    auth=(settings.GIT_USER, settings.GIT_ACCESS_TOKEN))

            commit_responses[repo] = response.json() + commit_responses[repo]

    return commit_responses


def get_hours_worked(commit_responses):
    # Parse Info into hours works for each repo and dev available

    hours_worked = {'repo': {}, 'devs': {}}
    for repo, commits in commit_responses.iteritems():
        for commit in commits:
            time_worked = parse_message(commit['commit']['message'])

            if repo in hours_worked['repo']:
                hours_worked['repo'][repo] += time_worked
            else:
                hours_worked['repo'][repo] = time_worked

            commiter = commit['commit']['committer']['name']
            if commiter in hours_worked['devs']:
                hours_worked['devs'][commiter] += time_worked
            else:
                hours_worked['devs'][commiter] = time_worked

    return hours_worked


@login_required
def dev_form(request, campaign_name='eartohear.info'):
    campaign = None
    try:
        campaign = Campaign.objects.get(name=campaign_name)
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
        workspaces = get_asana_workspaces(request)
        git_response = send_github_invitation(request, dev.github) if dev.github else None
        asana_responses = send_asana_invitation(request, dev.asana, workspaces) if dev.asana else None
        # Todo: Show exceptions and success

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
    except Dev.DoesNotExist:
        pass #pass

    if devData:
        github = devData.github
        asana = devData.asana
        title = 'Edit dev - ' + devData.first_name + ' ' + devData.last_name
        form = DevForm(request.POST or None, instance=devData)
        if form.is_valid():
            #save for and show success
            devData.save()
            form.save()
            devEdited = True
            set_admin_permissions(devData, github, asana)
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
def edit_obj(request, obj_type, obj_id):
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
def hours_list(request):
    params = {'per_page': 100}
    form = DevHoursForm(request.POST or None)
    if form.is_valid():
        hours = form.save()
        params['author'] = str(form.cleaned_data['dev'].github) if form.cleaned_data['dev'] else None
        print form.cleaned_data['since']
        print form.cleaned_data['until']
        hours_worked = get_commits_and_hours_worked(request, params)
    else:
        hours_worked = get_commits_and_hours_worked(request, params)
    context_dict = {'form': form, 'obj_type': 'Hours', 'hours_worked': hours_worked}
    return render(request, 'dev_center/hours_list.html', context_dict)


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
