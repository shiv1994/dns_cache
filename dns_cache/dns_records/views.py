from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import formset_factory
from django_q.tasks import async_task, result
from django_q.models import Schedule
from django.utils import timezone

from datetime import datetime, timedelta

from .forms import DomainForm, LoginForm, CaptchaForm
from .models import NSRecord, IPRecord, MXRecord, DomainRecord
from .functions.dns_functions import determineLocalIPAddressCountry, inDepthLookup
from .functions.rebuild_system import rebuild

import csv, time, asyncio


def display_message(request, message_type, message):
    if message_type == "S":
        message_type_result = messages.SUCCESS
    elif message_type == "E":
        message_type_result = messages.ERROR
    else:
        message_type_result = messages.INFO
    messages.add_message(request, message_type_result, message, extra_tags='safe')


def save_domain_record(domain_name):
    domain_object = DomainRecord(domain_name = domain_name)
    domain_object.save()
    return domain_object


def save_ip_records(domain_object, ip_addresses, ip_type):
    if ip_addresses is not None:
        for ip_address in ip_addresses:
            ip_object = IPRecord(domain_record=domain_object, ip_entry=ip_address.address, record_type = ip_type)
            ip_object.save()


def save_ns_records(domain_object, name_servers):
    if name_servers is not None:
        for ns_record in name_servers:
            name_sapce_obj = NSRecord(ns_name=ns_record['name_server'], ns_address=ns_record['ip_address'],
                                    domain_record=domain_object)
            name_sapce_obj.save()


def save_mx_records(domain_object, mx_records):
    if mx_records is not None:
        for mx_record in mx_records:
            mx_obj = MXRecord(mx_priority = mx_record['priority'] , mx_address = mx_record['host'], domain_record=domain_object)
            mx_obj.save()


def get_ip_records(domain_obj):
    text = ""
    ip_records = IPRecord.objects.all().filter(domain_record = domain_obj)
    for ip_record in ip_records:
        text += str(ip_record.ip_entry) +", "
    new_text = text[:len(text)-2]
    return new_text


def get_mx_records(domain_obj):
    text = ""
    mx_records = MXRecord.objects.all().filter(domain_record = domain_obj)
    for mx_record in mx_records:
        text += str(mx_record.mx_address) + ", "
    new_text = text[:len(text)-2]
    return new_text


def get_ns_records(domain_obj):
    text = ""
    ns_records = NSRecord.objects.all().filter(domain_record = domain_obj)
    for ns_record in ns_records:
        text += str(ns_record.ns_address) + ", "
    new_text = text[:len(text)-2]
    return new_text


def save_all_records_async(domain_name):
    corresponding_records = inDepthLookup(domain_name)
    domain_object = save_domain_record(domain_name)
    save_ip_records(domain_object, corresponding_records[1], IPRecord.ipv4)
    save_ip_records(domain_object, corresponding_records[3], IPRecord.ipv6)
    save_ns_records(domain_object, corresponding_records[0])
    save_mx_records(domain_object, corresponding_records[2])


def add_domain(request):
    template_name = "dns_records/add_record.html"
    if request.method == "POST":
        domain_form = DomainForm(request.POST)
        captcha_form = CaptchaForm(request.POST)
        domain_name = ""
        if domain_form.is_valid() and captcha_form.is_valid():
            num_domains_submitted = 0
            num_domains_exist = 0
            num_domains_external = 0
            num_domains_failed = 0
            if 'domain_name' in domain_form.cleaned_data:
                domain_name = domain_form.cleaned_data['domain_name']
                results = determineLocalIPAddressCountry(domain_name)
                if results is not None:
                    if results['statusCode'] == "OK":
                        if results['countryCode'] == "TT":
                            domain_name_exists = DomainRecord.objects.filter(domain_name = domain_name).exists()
                            if domain_name_exists:
                                num_domains_exist = 1
                            else:
                                async_task(save_all_records_async, domain_name)
                                # async_task(save_domain_record, domain_name)
                                num_domains_submitted = 1
                        else:
                            num_domains_external = 1
                    else:
                        num_domains_failed = 1
            if num_domains_submitted == 1:
                # ip_mappings = get_ip_records(domain_object)
                # mx_mappings = get_mx_records(domain_object)
                # ns_mappings = get_ns_records(domain_object)
                # display_message(request, "S", domain_name + " has been cached successfully. <br>A records: "+ip_mappings+ ".<br>MX records: " + mx_mappings + ".<br>NS records: " + ns_mappings +".")
                display_message(request, "S", domain_name + " has been cached successfully.")
                # print("NON_ASYNC FINISHED")
                return redirect('add-domain')
            else:
                message = domain_name + " has not been cached because "
                if num_domains_exist != 0:
                    domain_object = DomainRecord.objects.get(domain_name = domain_name)
                    ip_mappings = get_ip_records(domain_object)
                    mx_mappings = get_mx_records(domain_object)
                    ns_mappings = get_ns_records(domain_object)
                    message += "it exists in the system already.<br>A records: "+ip_mappings+ ".<br>MX records: " + mx_mappings + ".<br>NS records: " + ns_mappings +"."
                if num_domains_external != 0:
                    message += "no local IP mappings exist."
                if num_domains_failed !=0:
                    message += "the domain is not registered."
                display_message(request, "I", message)
                return redirect('add-domain')
        elif not domain_form.is_valid() and not captcha_form.is_valid():
            display_message(request, "E", "You entered an invalid domain and the captcha was not successfully verified.")
            captcha_form = CaptchaForm()
            return render(request, template_name, {'domain_form':domain_form, 'captcha_form':captcha_form})
        elif not domain_form.is_valid():
            display_message(request, "E", "You entered an invalid domain format.")
            captcha_form = CaptchaForm()
            return render(request, template_name, {'domain_form':domain_form, 'captcha_form':captcha_form})
        elif not captcha_form.is_valid():
            display_message(request, "E", "The captcha did not pass verification.")
            captcha_form = CaptchaForm()
            return render(request, template_name, {'domain_form':domain_form, 'captcha_form':captcha_form})
    elif request.method == "GET":
        domain_form = DomainForm()
        captcha_form = CaptchaForm()
        return render(request, template_name, {'domain_form':domain_form, 'captcha_form':captcha_form})


@login_required
def dump(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dump.csv"'
    writer = csv.writer(response, delimiter=' ')
    writer.writerow(['domain', 'record_type', 'resolution'])
    domain_records = DomainRecord.objects.all()
    for domain_record in domain_records:
        ip_records = IPRecord.objects.all().filter(domain_record = domain_record)
        for ip_record in ip_records:
            writer.writerow([domain_record.domain_name, ip_record.record_type, ip_record.ip_entry])
        mx_records = MXRecord.objects.all().filter(domain_record = domain_record)
        for mx_record in mx_records:
            writer.writerow([domain_record.domain_name, "MX", mx_record.mx_address, mx_record.mx_priority])
        ns_records = NSRecord.objects.all().filter(domain_record = domain_record)
        for ns_record in ns_records:
            writer.writerow([domain_record.domain_name, "NS", ns_record.ns_name, ns_record.ns_address])
    return response


def login_view(request):
    template_name = "dns_records/login.html"
    if request.method == "GET":
        form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect('dns_records:main')
            else:
                display_message(request, "E", "Wrong username/password.")
                return redirect('dns_records:login')
        else:
            messages.error(request, 'Error: You have invalid fields in your form.')
            return redirect('dns_records:login')
    return render(request, template_name, {'form':form})


@login_required
def logout_view(request):
    auth.logout(request)
    messages.add_message(request, messages.SUCCESS, 'You have been logged out!')
    return redirect('dns_records:login')


@login_required
def main(request):
    return render(request, 'dns_records/main.html', {})


@staff_member_required
@login_required
def rebuild_db(request):
    return_message = rebuild()
    display_message(request, "S", return_message)
    return redirect('dns_records:main')

      
@staff_member_required
@login_required
def cache_setup(request):
    # Setup schedule for new user requests.
    try:
        new_user_request_obj = Schedule.objects.get(name = 'rebuild_cache')
    except Schedule.DoesNotExist:
        new_user_request_obj = None
    if new_user_request_obj is None:
        Schedule.objects.create(func='dns_records.functions.rebuild_system.rebuild', schedule_type=Schedule.DAILY, args='', name='rebuild_cache',
         next_run=timezone.now().replace(hour = 0, minute = 0, second = 0, microsecond = 0))
    display_message(request, "S", 'Rebuild task scheduled for every day.')
    return redirect('dns_records:main')

        




