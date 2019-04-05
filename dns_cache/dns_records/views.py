from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DomainForm
from .models import NSRecord, IPRecord, ARecord
from .functions.dns_functions import determineLocalIPAddressCountry, inDepthLookup

def displayMessage(request, message_type, message):
    message_type_result = None
    if message_type == "S":
        message_type_result = messages.SUCCESS
    elif message_type == "E":
        message_type_result = messages.ERROR
    else:
        message_type_result = messages.INFO
    messages.add_message(request, message_type_result, message)


def saveNSRecords(domain_name, ip_address, name_servers):
    ip_object = IPRecord(domain_name = domain_name, ip_address_resolved= ip_address)
    ip_object.save()
    for ns_record in name_servers:
        print(ns_record)
        name_sapce_obj = NSRecord(ns_name = ns_record['name_server'], ns_address = ns_record['ip_address'])
        name_sapce_obj.save()
        ip_object.ns_records.add(name_sapce_obj)

def saveARecord(domain_name, host_ip):
    ip_object = IPRecord.objects.get(domain_name = domain_name)
    host_obj = ARecord(hostname = domain_name, ip_address = host_ip)
    host_obj.save()
    ip_object.a_record = host_obj
    ip_object.save()


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
                            saveNSRecords(domain_name, results['ipAddress'], corresponding_records[0])
                            saveARecord(domain_name, corresponding_records[1])
                            displayMessage(request, "S", "The domain name has been sent for processing.")
                else:
                    displayMessage(request, "E", "There was an error performing the lookup. Please re-enter the domain name.")
            else:
                displayMessage(request, "E", "There was an error performing the lookup. Please re-enter the domain name.")
        else:
            displayMessage(request, "E", "There was an error performing the lookup. Please re-enter the domain name.")
        return redirect('dns_records:add-domain')
    elif request.method == "GET":
        domain_form = DomainForm()
    return render(request, template_name, {'domain_form':domain_form})
