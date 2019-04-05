from django.db import models
import datetime

class NSRecord(models.Model):
    ns_name = models.CharField(max_length = 50, unique = True, blank = False)
    ns_address = models.GenericIPAddressField()

class ARecord(models.Model):
    hostname = models.CharField(max_length = 50, unique = True, blank = False)
    ip_address = models.GenericIPAddressField()

class IPRecord(models.Model):
    domain_name = models.CharField(max_length = 50, unique = True, blank = False)
    ip_address_resolved = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ns_records = models.ManyToManyField(NSRecord)
    a_record = models.OneToOneField(ARecord, on_delete=models.CASCADE, blank = True, null = True)

class Stats(models.Model):
    num_transactions = models.IntegerField(default = 0)
    num_requests_local = models.IntegerField(default = 0)
    num_requests_non_local = models.IntegerField(default = 0)
    num_requests_success = models.IntegerField(default = 0)
    num_requests_invalid = models.IntegerField(default = 0)