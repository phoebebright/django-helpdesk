# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-01 19:43
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("helpdesk", "0022_add_submitter_email_id_field_to_ticket"),
    ]

    operations = [
        migrations.AddField(
            model_name="queue",
            name="enable_notifications_on_email_events",
            field=models.BooleanField(
                default=False,
                help_text="When an email arrives to either create a ticket or to interact with an existing discussion. Should email notifications be sent ? Note: the new_ticket_cc and updated_ticket_cc work independently of this feature",
                verbose_name="Notify contacts when email updates arrive",
            ),
        ),
    ]
