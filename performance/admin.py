from django.contrib import admin
from .models import Student, Performance, SlowLearner

admin.site.register(Student)
admin.site.register(Performance)
admin.site.register(SlowLearner)
