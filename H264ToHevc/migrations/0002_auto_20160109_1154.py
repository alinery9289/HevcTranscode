# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('H264ToHevc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediafile',
            name='encodeinfo',
            field=models.CharField(max_length=1200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='processlog',
            name='controljson',
            field=models.CharField(default={}, max_length=1000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='processlog',
            name='taskid',
            field=models.CharField(default=1, max_length=32, unique=True, serialize=False, primary_key=True),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='processlog',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='processlog',
            name='id',
        ),
    ]
