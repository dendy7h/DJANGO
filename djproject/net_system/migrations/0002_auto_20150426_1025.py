# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('net_system', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='networkdevice',
            name='cfg_archive_time',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='networkdevice',
            name='cfg_last_changed',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
