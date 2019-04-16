from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from .forms import DomainForm, LoginForm
from .models import NSRecord, IPRecord, MXRecord
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


def save_ip_record(domain_name, ipv4_address, ipv6_address):
    ip_object = IPRecord(domain_name=domain_name, a_record=ipv4_address, aaaa_record=ipv6_address)
    ip_object.save()
    return ip_object


def save_ns_records(domain_name, ip_address, name_servers, ip_object):
    for ns_record in name_servers:
        name_sapce_obj = NSRecord(ns_name=ns_record['name_server'], ns_address=ns_record['ip_address'],
                                  ip_record=ip_object)
        name_sapce_obj.save()


def save_mx_records(domain_name, mx_records, ip_object):
    for mx_record in mx_records:
        mx_obj = MXRecord(mx_priority = mx_record['priority'] , mx_address = mx_record['host'], ip_record=ip_object)
        mx_obj.save()


def add_domain(request):
    template_name = "dns_records/add_record.html"
    if request.method == "POST":
        domain_form = DomainForm(request.POST)
        if domain_form.is_valid():
            domain_name = domain_form.cleaned_data['domain_name']
            results = determineLocalIPAddressCountry(domain_name)
            if results is not None:
                print("We have results!")
                if results['statusCode'] == "OK":
                    print("We have more results!")
                    if results['countryCode'] == "TT":
                        domain_name_exists = IPRecord.objects.filter(domain_name = domain_name).exists()
                        if domain_name_exists:
                            display_message(request, "I", "The domain name already exists within the system.")
                        else:
                            print("We are now going to fetch corresponding records!")
                            corresponding_records = inDepthLookup(domain_name)
                            ip_object = save_ip_record(domain_name, corresponding_records[1], corresponding_records[3])
                            save_ns_records(domain_name, results['ipAddress'], corresponding_records[0], ip_object)
                            save_mx_records(domain_name, corresponding_records[2], ip_object)
                            display_message(request, "S", "The domain name has been sent for processing.")
                    else:
                        display_message(request, "E", "This domain does not belong to Trinidad.")
                else:
                    display_message(request, "E", "There was an error performing the lookup. Please re-enter the "
                                                  "domain name.")
            else:
                display_message(request, "E", "There was an error performing the lookup. Please re-enter the "
                                              "domain name.")
        else:
            display_message(request, "E", "There was an issue validating the form. Please enter correct data.")
        return redirect('add-domain')
    elif request.method == "GET":
        domain_form = DomainForm()
    return render(request, template_name, {'domain_form':domain_form})


@login_required
def dump(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dump.csv"'
    writer = csv.writer(response, delimiter=' ')
    writer.writerow(['domain', 'record_type', 'resolution'])
    ip_records = IPRecord.objects.all()
    for ip_record in ip_records:
        writer.writerow([ip_record.domain_name, "A", ip_record.a_record])
        if ip_record.aaaa_record is not None:
            writer.writerow([ip_record.domain_name, "AAAA", ip_record.aaaa_record])
        mx_records = MXRecord.objects.all().filter(ip_record = ip_record)
        for mx_record in mx_records:
            writer.writerow([ip_record.domain_name, "MX", mx_record.mx_address, mx_record.mx_priority])
        ns_records = NSRecord.objects.all().filter(ip_record = ip_record)
        for ns_record in ns_records:
            writer.writerow([ip_record.domain_name, "NS", ns_record.ns_name, ns_record.ns_address])
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
    mx_records_altered = 0
    ns_records_altered = 0
    ip_records = IPRecord.objects.all()
    for ip_rec in ip_records:
        # Resolve to all required fields.
        corresponding_records = inDepthLookup(ip_rec.domain_name)
        ip_rec.a_record = corresponding_records[1]
        ip_rec.aaaa_record = corresponding_records[3]
        ip_rec.save()
        # Remove old MX entries and update new ones. Use corresponding_records[2]
        mx_records = MXRecord.objects.all().filter(ip_record = ip_rec)
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
                                  ip_record= ip_rec)
                mx_obj.save()
        # Remove old NS entries and update new ones. Use corresponding_records[0]
        ns_records = NSRecord.objects.all().filter(ip_record = ip_rec)
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
                                  ip_record=ip_rec)
                ns_obj.save()
        return_message = "Cache Rebuild Complete! " + str(ns_records_altered) + " NS records altered and " + \
                         str(mx_records_altered) + " MX records altered."
        messages.add_message(request, messages.SUCCESS, return_message)
    return redirect('dns_records:main')
        


        




