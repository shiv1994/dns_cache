from django.db import models
import datetime

class DomainRecord(models.Model):
    domain_name = models.CharField(max_length = 50, unique = True, blank = False)
    timestamp = models.DateTimeField(auto_now_add=True)

class IPRecord(models.Model):
    ipv4 = "A"
    ipv6 = "AAAA"
    IP_TYPES = (
        (ipv4, 'ipv4'),
        (ipv6, 'ipv6'),
    )
    record_type = models.CharField(max_length=4, choices= IP_TYPES)
    ip_entry = models.GenericIPAddressField(blank = False)
    domain_record = models.ForeignKey(DomainRecord, on_delete=models.CASCADE, related_name='a_records')

class NSRecord(models.Model):
    ns_name = models.CharField(max_length = 50, unique = True, blank = False)
    ns_address = models.GenericIPAddressField()
    domain_record = models.ForeignKey(DomainRecord, on_delete=models.CASCADE, related_name='ns_records')

class MXRecord(models.Model):
    mx_priority = models.IntegerField(blank = False)
    mx_address = models.CharField(max_length = 50, blank = False)
    domain_record = models.ForeignKey(DomainRecord, on_delete=models.CASCADE, related_name='mx_records')

class Stats(models.Model):
    num_transactions = models.IntegerField(default = 0)
    num_requests_local = models.IntegerField(default = 0)
    num_requests_non_local = models.IntegerField(default = 0)
    num_requests_success = models.IntegerField(default = 0)
    num_requests_invalid = models.IntegerField(default = 0)
