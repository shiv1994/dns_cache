from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory

from .forms import DomainForm, LoginForm, CaptchaForm
from .models import NSRecord, IPRecord, MXRecord, DomainRecord
from .functions.dns_functions import determineLocalIPAddressCountry, inDepthLookup

import csv


def display_message(request, message_type, message):
    if message_type == "S":
        message_type_result = messages.SUCCESS
    elif message_type == "E":
        message_type_result = messages.ERROR
    else:
        message_type_result = messages.INFO
    messages.add_message(request, message_type_result, message)


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


def add_domain(request):
    template_name = "dns_records/add_record.html"
    if request.method == "POST":
        DomainFormSet = formset_factory(DomainForm)
        domain_formset = DomainFormSet(request.POST, prefix='domain-forms')
        captcha_form = CaptchaForm(request.POST)
        if domain_formset.is_valid() and captcha_form.is_valid():
            num_domains_submitted = 0
            num_domains_total = 0
            num_domains_exist = 0
            existing_domain_names = ""
            invalid_domain_names = ""
            index = -1
            for domain_form in domain_formset:
                index += 1
                num_domains_total += 1
                if 'domain_name' in domain_form.cleaned_data:
                    domain_name = domain_form.cleaned_data['domain_name']
                    results = determineLocalIPAddressCountry(domain_name)
                    if results is not None:
                        if results['statusCode'] == "OK":
                            if results['countryCode'] == "TT":
                                domain_name_exists = DomainRecord.objects.filter(domain_name = domain_name).exists()
                                if domain_name_exists:
                                    existing_domain_names += domain_name + ", "
                                    num_domains_exist += 1
                                else:
                                    corresponding_records = inDepthLookup(domain_name)
                                    domain_object = save_domain_record(domain_name)
                                    save_ip_records(domain_object, corresponding_records[1], IPRecord.ipv4)
                                    save_ip_records(domain_object, corresponding_records[3], IPRecord.ipv6)
                                    save_ns_records(domain_object, corresponding_records[0])
                                    save_mx_records(domain_object, corresponding_records[2])
                                    num_domains_submitted += 1
                            else:
                                invalid_domain_names += domain_name + ", "
                        else:
                            invalid_domain_names += domain_name + ", "
            if num_domains_submitted == num_domains_total:
                display_message(request, "S", "All domains submitted successfully.")
                return redirect('add-domain')
            else:
                existing_domain_names = existing_domain_names[:len(existing_domain_names)-2] + "."
                invalid_domain_names = invalid_domain_names[:len(invalid_domain_names)-2] + "."
                message = str(num_domains_submitted) + " out of " + str(num_domains_total) + " domains have been submitted. The following domain(s) exist already: " +  existing_domain_names + ". The following domain(s) are invalid or do not reside within Trinidad and Tobago: " +  invalid_domain_names
                display_message(request, "I", message)
                return redirect('add-domain')
        elif not captcha_form.is_valid():
            display_message(request, "E", "The captcha was not successfully verified.")
            captcha_form = CaptchaForm()
            render(request, template_name, {'domain_formset':domain_formset, 'captcha_form':captcha_form})
    elif request.method == "GET":
        DomainFormSet = formset_factory(DomainForm, extra = 1)
        domain_formset = DomainFormSet(prefix='domain-forms')
        captcha_form = CaptchaForm()
    return render(request, template_name, {'domain_formset':domain_formset, 'captcha_form':captcha_form})


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


@login_required
def rebuild_db(request):
    # Get and iterate all IP records.
    ip_records_altered = 0
    mx_records_altered = 0
    ns_records_altered = 0
    domain_records = DomainRecord.objects.all()
    for domain_rec in domain_records:
        # Resolve to all required fields.
        corresponding_records = inDepthLookup(domain_rec.domain_name)
        # Remove old ipv4 entries and update new ones. Use corresponding_records[1]
        ip_records = IPRecord.objects.all().filter(domain_record = domain_rec, record_type = IPRecord.ipv4)
        for ip_record_old in ip_records:
            exists = False
            for ip_record_new in corresponding_records[1]:
                if str(ip_record_old.ip_entry) == str(ip_record_new.address):
                    exists = True
                    break
            if not exists:
                ip_records_altered += 1
                ip_record_old.delete()
                ip_obj = IPRecord(domain_record=domain_rec, record_type=IPRecord.ipv4, ip_entry = ip_record_new.address)
                ip_obj.save()
        # Remove old ipv6 entries and update new ones. Use corresponding_records[3]
        ip_records = IPRecord.objects.all().filter(domain_record = domain_rec, record_type = IPRecord.ipv6)
        for ip_record_old in ip_records:
            exists = False
            for ip_record_new in corresponding_records[1]:
                if str(ip_record_old.ip_entry) == str(ip_record_new.address):
                    exists = True
                    break
            if not exists:
                ip_records_altered += 1
                ip_record_old.delete()
                ip_obj = IPRecord(domain_record=domain_rec, record_type=IPRecord.ipv6, ip_entry = ip_record_new.address)
                ip_obj.save()
        # Remove old MX entries and update new ones. Use corresponding_records[2]
        mx_records = MXRecord.objects.all().filter(domain_record = domain_rec)
        for mx_record_old in mx_records:
            exists = False
            for mx_record_new in corresponding_records[2]:
                if str(mx_record_old.mx_address) == str(mx_record_new['host']):
                    exists = True
                    break
            if not exists:
                mx_records_altered += 1
                mx_record_old.delete()
                mx_obj = MXRecord(mx_priority=mx_record_new['priority'] , mx_address = mx_record_new['host'],
                                  domain_record= domain_rec)
                mx_obj.save()
        # Remove old NS entries and update new ones. Use corresponding_records[0]
        ns_records = NSRecord.objects.all().filter(domain_record = domain_rec)
        for ns_record_old in ns_records:
            exists = False
            for ns_record_new in corresponding_records[0]:
                if ns_record_old.ns_name == str(ns_record_new['name_server']) and str(ns_record_old.ns_address) == \
                        str(ns_record_new['ip_address']):
                    exists = True
                    break
            if not exists:
                ns_records_altered += 1
                ns_record_old.delete()
                ns_obj = NSRecord(ns_name=ns_record_new['name_server'], ns_address = ns_record_new['ip_address'],
                                  domain_record=domain_rec)
                ns_obj.save()
        return_message = "Cache Rebuild Complete! " + str(ns_records_altered) + " NS records altered, " + \
                         str(mx_records_altered) + " MX records altered and " +  str(ip_records_altered) + " IP records altered."
        messages.add_message(request, messages.SUCCESS, return_message)
    return redirect('dns_records:main')
        


        




