from ..models import DomainRecord, IPRecord, MXRecord, NSRecord
from .dns_functions import inDepthLookup, determineLocalIPAddressCountry


def rebuild():
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
    return return_message