from django.contrib import admin

from .models import *

admin.site.register(Vocabulary)
admin.site.register(Lemma)
admin.site.register(VocabularyLemma)
admin.site.register(Lang)
admin.site.register(LearnerVocabulary)
admin.site.register(Education)
admin.site.register(EducationLemma)
admin.site.register(Board)

