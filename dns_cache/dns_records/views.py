from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from .forms import DomainForm, LoginForm
from .models import NSRecord, IPRecord, MXRecord
from .functions.dns_functions import determineLocalIPAddressCountry, inDepthLookup

import csv

def displayMessage(request, message_type, message):
    message_type_result = None
    if message_type == "S":
        message_type_result = messages.SUCCESS
    elif message_type == "E":
        message_type_result = messages.ERROR
    else:
        message_type_result = messages.INFO
    messages.add_message(request, message_type_result, message)


def saveIPRecord(domain_name, ipv4_address, ipv6_address):
    ip_object = IPRecord(domain_name = domain_name, a_record= ipv4_address, aaaa_record = ipv6_address)
    ip_object.save()
    return ip_object


def saveNSRecords(domain_name, ip_address, name_servers, ip_object):
    for ns_record in name_servers:
        name_sapce_obj = NSRecord(ns_name = ns_record['name_server'], ns_address = ns_record['ip_address'], ip_record = ip_object)
        name_sapce_obj.save()


def saveMXRecords(domain_name, mx_records, ip_object):
    for mx_record in mx_records:
        mx_obj = MXRecord(mx_priority = mx_record['priority'] , mx_address = mx_record['host'], ip_record= ip_object)
        mx_obj.save()


def add_domain(request):
    template_name = "dns_records/add_record.html"
    if request.method == "POST":
        domain_form = DomainForm(request.POST)
        if domain_form.is_valid():
            domain_name = domain_form.cleaned_data['domain_name']
            results = determineLocalIPAddressCountry(domain_name)
            if results is not None:
                if results['statusCode'] == "OK":
                    if results['countryCode'] == "TT":
                        domain_name_exists = IPRecord.objects.filter(domain_name = domain_name).exists()
                        if domain_name_exists:
                            displayMessage(request, "I", "The domain name already exists within the system.")
                        else:
                            corresponding_records = inDepthLookup(domain_name)
                            ip_object = saveIPRecord(domain_name, corresponding_records[1], corresponding_records[3])
                            saveNSRecords(domain_name, results['ipAddress'], corresponding_records[0], ip_object)
                            saveMXRecords(domain_name, corresponding_records[2], ip_object)
                            displayMessage(request, "S", "The domain name has been sent for processing.")
                else:
                    displayMessage(request, "S", "There was an error performing the lookup. Please re-enter the domain name.")
            else:
                displayMessage(request, "E", "There was an error performing the lookup. Please re-enter the domain name.")
        else:
            displayMessage(request, "E", "There was an issue validating the form. Please enter correct data.")
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
                displayMessage(request, "E", "Wrong username/password.")
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
