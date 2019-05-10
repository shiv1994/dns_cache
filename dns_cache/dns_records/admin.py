from django.contrib import admin
from .models import IPRecord, NSRecord, MXRecord, DomainRecord

admin.site.register(NSRecord)
admin.site.register(IPRecord)
admin.site.register(MXRecord)
admin.site.register(DomainRecord)