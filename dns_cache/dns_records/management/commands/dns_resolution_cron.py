from django.core.management.base import BaseCommand, CommandError
from ...models import NSRecord, ARecord, IPRecord, Stats
from ...functions.dns_functions import inDepthLookup, determineLocalIPAddressCountry

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


def UpdateResolutions():
    domain_name = "pin.tt"
    results = determineLocalIPAddressCountry(domain_name)
    if results is not None:
        if results['statusCode'] == "OK":
            if results['countryCode'] == "TT":
                domain_name_exists = IPRecord.objects.filter(domain_name = domain_name).exists()
                if not domain_name_exists:
                    corresponding_records = inDepthLookup(domain_name)
                    saveNSRecords(domain_name, results['ipAddress'], corresponding_records[0])
                    saveARecord(domain_name, corresponding_records[1])

class Command(BaseCommand):
    def handle(self, *args, **options):
        UpdateResolutions()