from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from other.choices import Verb


class Action(models.Model):
    # todo add user action
    brand = models.ForeignKey("brand.Brand",
                              related_name="brand_actions",
                              db_index=True,
                              on_delete=models.CASCADE)
    target_ct = models.ForeignKey(ContentType,
                                  blank=True,
                                  null=True,
                                  related_name='brand_target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True,
                                            blank=True,
                                            db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    verb = models.CharField(max_length=30, choices=Verb.choices, default=Verb.NONE)
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,
                                      db_index=True)

    class Meta:
        ordering = ('-created_at',)
