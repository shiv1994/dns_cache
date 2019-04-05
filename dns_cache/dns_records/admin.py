from django.contrib import admin
from .models import IPRecord, NSRecord, ARecord

admin.site.register(NSRecord)
admin.site.register(ARecord)
admin.site.register(IPRecord)
