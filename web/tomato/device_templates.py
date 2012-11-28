# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2012 Integrated Communication Systems Lab, University of Kaiserslautern
#
# This file is part of the ToMaTo project
#
# ToMaTo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import *
import xmlrpclib
import base64

class TemplateForm(forms.Form):
    label = forms.CharField(max_length=255, help_text="The displayed label for this profile")
    subtype = forms.CharField(max_length=255, required=False)
    preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")

class AddTemplateForm(TemplateForm):
    torrentfile  = forms.FileField(label="Torrent:", help_text='See the <a href="https://tomato.readthedocs.org/en/latest/docs/templates/" target="_blank">template documentation about the torrent file.</a> for more information')
    name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all profiles. Cannot be changed. Not displayed.")
    tech = forms.CharField(max_length=255,widget = forms.widgets.Select(choices=[('kvmqm','kvmqm'),('openvz','openvz'),('repy','repy')]))
    def __init__(self, *args, **kwargs):
        super(AddTemplateForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['name', 'label', 'subtype', 'tech', 'preference','torrentfile']
    
class EditTemplateForm(TemplateForm):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
class ChangeTemplateTorrentForm(forms.Form):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    torrentfile  = forms.FileField(label="Torrent containing image:", help_text='See the <a href="https://tomato.readthedocs.org/en/latest/docs/templates/" target="_blank">template documentation about the torrent file.</a> for more information')    
    
class RemoveResourceForm(forms.Form):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
def is_hostManager(account_info):
    return 'hosts_manager' in account_info['flags']

@wrap_rpc
def index(api, request):
    reslist = api.resource_list()
    templ_list = []
    for res in reslist:
        if res['type'] == 'template':
            templ_list.append(res)
        
    return render_to_response("admin/device_templates/index.html", {'user': api.user, 'templ_list': templ_list, 'hostManager': is_hostManager(api.account_info())})


@wrap_rpc
def add(api, request):
    if request.method == 'POST':
        form = AddTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            formData = form.cleaned_data
            f = request.FILES['torrentfile']
            torrent_data = base64.b64encode(f.read())
            api.resource_create('template',{'name':formData['name'],'label':formData['label'],'subtype':formData['subtype'],'preference':formData['preference'],'tech': formData['tech'],'torrent_data':torrent_data})
            return render_to_response("admin/device_templates/add_success.html", {'user': api.user, 'label': formData['label']})
        else:
            return render_to_response("admin/device_templates/form.html", {'user': api.user, 'form': form, "edit":False})
    else:
        form = AddTemplateForm
        return render_to_response("admin/device_templates/form.html", {'user': api.user, 'form': form, "edit":False})
   

@wrap_rpc
def remove(api, request):
    if request.method == 'POST':
        form = RemoveResourceForm(request.POST)
        if form.is_valid():
            res_id = form.cleaned_data["res_id"]
            if api.resource_info(res_id) and api.resource_info(res_id)['type'] == 'template':
                label = api.resource_info(res_id)['attrs']['label']
                api.resource_remove(res_id)
                return render_to_response("admin/device_templates/remove_success.html", {'user': api.user, 'label':label})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'There is no template with id '+res_id})
        else:
            res_id = request.POST['res_id']
            if res_id:
                form = RemoveResourceForm()
                form.fields["res_id"].initial = res_id
                return render_to_response("admin/device_templates/remove_confirm.html", {'user': api.user, 'label': api.resource_info(res_id)['attrs']['label'], 'hostManager': is_hostManager(api.account_info()), 'form': form})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        res_id = request.GET['id']
        if res_id:
            form = RemoveResourceForm()
            form.fields["res_id"].initial = res_id
            return render_to_response("admin/device_templates/remove_confirm.html", {'user': api.user, 'label': api.resource_info(res_id)['attrs']['label'], 'hostManager': is_hostManager(api.account_info()), 'form': form})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})
    

@wrap_rpc
def edit(api, request):
    return render_to_response("admin/device_templates/edit_unspecified.html",{'user': api.user, 'res_id':request.GET['id'],'label':api.resource_info(request.GET['id'])['attrs']['label']})

@wrap_rpc
def edit_torrent(api, request):
    if request.method=='POST':
        form = ChangeTemplateTorrentForm(request.POST,request.FILES)
        if form.is_valid():
            formData = form.cleaned_data
            f = request.FILES['torrentfile']
            torrent_data = base64.b64encode(f.read())
            res_info = api.resource_info(formData['res_id'])
            if res_info['type'] == 'template':
                api.resource_modify(formData["res_id"],{'torrent_data':torrent_data})
                return render_to_response("admin/device_templates/edit_success.html", {'user': api.user, 'label': res_info['attrs']['label']})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no template.'})
        else:
            label = request.POST["label"]
            if label:
                return render_to_response("admin/device_templates/form.html", {'user': api.user, 'label': label, 'form': form, "edit":True, 'edit_data':False})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            form = ChangeTemplateTorrentForm()
            form.fields['res_id'].initial = res_id
            return render_to_response("admin/device_templates/form.html", {'user': api.user, 'label': res_info['attrs']['label'], 'form': form, "edit":True, 'edit_data':False})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})


@wrap_rpc
def edit_data(api, request):
    if request.method=='POST':
        form = EditTemplateForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if api.resource_info(formData['res_id'])['type'] == 'template':
                api.resource_modify(formData["res_id"],{'label':formData['label'],'subtype':formData['subtype'],'preference':formData['preference']})
                return render_to_response("admin/device_templates/edit_success.html", {'user': api.user, 'label': formData["label"]})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no template.'})
        else:
            label = request.POST["label"]
            if label:
                return render_to_response("admin/device_templates/form.html", {'user': api.user, 'label': label, 'form': form, "edit":True, 'edit_data':True})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        res_id = request.GET['id']
        if res_id:
            res_info = api.resource_info(res_id)
            origData = res_info['attrs']
            origData['res_id'] = res_id
            form = EditTemplateForm(origData)
            return render_to_response("admin/device_templates/form.html", {'user': api.user, 'label': res_info['attrs']['label'], 'form': form, "edit":True, 'edit_data':True})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})

