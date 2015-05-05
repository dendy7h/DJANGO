# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('net_system', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SnmpCredentials',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(max_length=10)),
                ('community', models.CharField(max_length=50, blank=True)),
                ('port', models.IntegerField(null=True, blank=True)),
                ('username', models.CharField(max_length=50, blank=True)),
                ('auth_proto', models.CharField(max_length=50, blank=True)),
                ('auth_key', models.CharField(max_length=50, blank=True)),
                ('encrypt_proto', models.CharField(max_length=50, blank=True)),
                ('encrypt_key', models.CharField(max_length=50, blank=True)),
                ('description', models.CharField(max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='networkdevice',
            name='cfg_file',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='networkdevice',
            name='snmp_creds',
            field=models.ForeignKey(blank=True, to='net_system.SnmpCredentials', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='networkdevice',
            name='snmp_port',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='credentials',
            name='description',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='networkdevice',
            name='device_type',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='networkdevice',
            name='model',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='networkdevice',
            name='vendor',
            field=models.CharField(max_length=50, blank=True),
        ),
    ]
