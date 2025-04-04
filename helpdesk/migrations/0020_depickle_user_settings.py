# Generated by Django 2.0.7 on 2018-10-19 14:11
from django.db import migrations, models
import helpdesk.models


def unpickle_settings(settings_pickled):
    # return a python dictionary representing the pickled data.
    try:
        import pickle
    except ImportError:
        import cPickle as pickle
    try:
        # Python 2 support
        from base64 import urlsafe_b64decode as b64decode
    except ImportError:
        # Python 3 support
        from base64 import decodebytes as b64decode
    try:
        return pickle.loads(b64decode(settings_pickled.encode("utf-8")))
    except Exception:
        return {}


def move_old_values(apps, schema_editor):
    UserSettings = apps.get_model("helpdesk", "UserSettings")
    db_alias = schema_editor.connection.alias

    for user_settings in UserSettings.objects.using(db_alias).all():
        if user_settings.settings_pickled:
            settings_dict = unpickle_settings(user_settings.settings_pickled)
            for setting, value in settings_dict.items():
                user_settings.__setattr__(setting, value)


class Migration(migrations.Migration):
    dependencies = [
        ("helpdesk", "0019_ticket_secret_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersettings",
            name="email_on_ticket_assign",
            field=models.BooleanField(
                default=helpdesk.models.email_on_ticket_assign_default,
                help_text="If you are assigned a ticket via the web, do you want to receive an e-mail?",
                verbose_name="E-mail me when assigned a ticket?",
            ),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="email_on_ticket_change",
            field=models.BooleanField(
                default=helpdesk.models.email_on_ticket_change_default,
                help_text="If you're the ticket owner and the ticket is changed via the web by somebody else, do you want to receive an e-mail?",
                verbose_name="E-mail me on ticket change?",
            ),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="login_view_ticketlist",
            field=models.BooleanField(
                default=helpdesk.models.login_view_ticketlist_default,
                help_text="Display the ticket list upon login? Otherwise, the dashboard is shown.",
                verbose_name="Show Ticket List on Login?",
            ),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="tickets_per_page",
            field=models.IntegerField(
                choices=[(10, "10"), (25, "25"), (50, "50"), (100, "100")],
                default=helpdesk.models.tickets_per_page_default,
                help_text="How many tickets do you want to see on the Ticket List page?",
                verbose_name="Number of tickets to show per page",
            ),
        ),
        migrations.AddField(
            model_name="usersettings",
            name="use_email_as_submitter",
            field=models.BooleanField(
                default=helpdesk.models.use_email_as_submitter_default,
                help_text="When you submit a ticket, do you want to automatically use your e-mail address as the submitter address? You can type a different e-mail address when entering the ticket if needed, this option only changes the default.",
                verbose_name="Use my e-mail address when submitting tickets?",
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="settings_pickled",
            field=models.TextField(
                blank=True,
                help_text="DEPRECATED! This is a base64-encoded representation of a pickled Python dictionary. Do not change this field via the admin.",
                null=True,
                verbose_name="DEPRECATED! Settings Dictionary DEPRECATED!",
            ),
        ),
        migrations.RunPython(move_old_values),
    ]
