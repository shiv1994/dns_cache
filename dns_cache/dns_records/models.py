from django.db import models
import datetime

class IPRecord(models.Model):
    domain_name = models.CharField(max_length = 50, unique = True, blank = False)
    a_record = models.GenericIPAddressField(blank = False)
    aaaa_record = models.GenericIPAddressField(blank = True, null = True)
    timestamp = models.DateTimeField(auto_now_add=True)

class NSRecord(models.Model):
    ns_name = models.CharField(max_length = 50, unique = True, blank = False)
    ns_address = models.GenericIPAddressField()
    ip_record = models.ForeignKey(IPRecord, on_delete=models.CASCADE, related_name='ns_records')

class MXRecord(models.Model):
    mx_priority = models.IntegerField(blank = False)
    mx_address = models.CharField(max_length = 50, blank = False)
    ip_record = models.ForeignKey(IPRecord, on_delete=models.CASCADE, related_name='mx_records')

class Stats(models.Model):
    num_transactions = models.IntegerField(default = 0)
    num_requests_local = models.IntegerField(default = 0)
    num_requests_non_local = models.IntegerField(default = 0)
    num_requests_success = models.IntegerField(default = 0)
    num_requests_invalid = models.IntegerField(default = 0)
