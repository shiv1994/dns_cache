from django.contrib import admin
from .models import IPRecord, NSRecord, MXRecord

admin.site.register(NSRecord)
admin.site.register(IPRecord)
admin.site.register(MXRecord)
