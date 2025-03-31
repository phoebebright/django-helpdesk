from django.conf import settings
from django.core.mail import get_connection
from django.utils.safestring import mark_safe
import logging
import os
from smtplib import SMTPException


logger = logging.getLogger("helpdesk")


def send_templated_mail(
    template_name,
    context,
    recipients,
    sender=None,
    bcc=None,
    fail_silently=False,
    files=None,
    extra_headers=None,
):
    """
    send_templated_mail() is a wrapper around Django's e-mail routines that
    allows us to easily send multipart (text/plain & text/html) e-mails using
    templates that are stored in the database. This lets the admin provide
    both a text and a HTML template for each message.

    template_name is the slug of the template to use for this message (see
        models.EmailTemplate)

    context is a dictionary to be used when rendering the template

    recipients can be either a string, eg 'a@b.com', or a list of strings.

    sender should contain a string, eg 'My Site <me@z.com>'. If you leave it
        blank, it'll use settings.DEFAULT_FROM_EMAIL as a fallback.

    bcc is an optional list of addresses that will receive this message as a
        blind carbon copy.

    fail_silently is passed to Django's mail routine. Set to 'True' to ignore
        any errors at send time.

    files can be a list of tuples. Each tuple should be a filename to attach,
        along with the File objects to be read. files can be blank.

    extra_headers is a dictionary of extra email headers, needed to process
        email replies and keep proper threading.

    """
    from django.core.mail import EmailMultiAlternatives
    from django.template import engines

    from_string = engines["django"].from_string

    from helpdesk.models import EmailTemplate
    from helpdesk.settings import (
        HELPDESK_EMAIL_FALLBACK_LOCALE,
        HELPDESK_EMAIL_SUBJECT_TEMPLATE,
    HELPDESK_EMAIL_BACKEND,
    )

    headers = extra_headers or {}

    locale = context["queue"].get("locale") or HELPDESK_EMAIL_FALLBACK_LOCALE

    try:
        t = EmailTemplate.objects.get(
            template_name__iexact=template_name, locale=locale
        )
    except EmailTemplate.DoesNotExist:
        try:
            t = EmailTemplate.objects.get(
                template_name__iexact=template_name, locale__isnull=True
            )
        except EmailTemplate.DoesNotExist:
            logger.warning('template "%s" does not exist, no mail sent', template_name)
            return  # just ignore if template doesn't exist

    subject_part = (
        from_string(HELPDESK_EMAIL_SUBJECT_TEMPLATE % {"subject": t.subject})
        .render(context)
        .replace("\n", "")
        .replace("\r", "")
    )

    footer_file = os.path.join("helpdesk", locale, "email_text_footer.txt")

    text_part = from_string(
        "%s\n\n{%% include '%s' %%}" % (t.plain_text, footer_file)
    ).render(context)

    email_html_base_file = os.path.join("helpdesk", locale, "email_html_base.html")
    # keep new lines in html emails
    if "comment" in context:
        context["comment"] = mark_safe(context["comment"].replace("\r\n", "<br>"))

    html_part = from_string(
        "{%% extends '%s' %%}"
        "{%% block title %%}%s{%% endblock %%}"
        "{%% block content %%}%s{%% endblock %%}"
        % (email_html_base_file, t.heading, t.html)
    ).render(context)

    if isinstance(recipients, str):
        if recipients.find(","):
            recipients = recipients.split(",")
    elif type(recipients) is not list:
        recipients = [recipients]

    # Create message
    msg = EmailMultiAlternatives(
        subject_part,
        text_part,
        sender or settings.DEFAULT_FROM_EMAIL,
        recipients,
        bcc=bcc,
        headers=headers,
        connection=get_connection(backend=HELPDESK_EMAIL_BACKEND)
    )
    msg.attach_alternative(html_part, "text/html")

    # Handle attachments
    if files:
        for filename, filefield in files:
            filefield.open("rb")
            content = filefield.read()
            msg.attach(filename, content)
            filefield.close()

    logger.info(f"Sending email to: {recipients} using backend {HELPDESK_EMAIL_BACKEND} with fail silently={fail_silently}")

    # Special handling for post_office if needed
    if HELPDESK_EMAIL_BACKEND == 'post_office.backend.EmailBackend':
        from post_office import mail
        try:
            email = mail.send(
                recipients=recipients,
                sender=sender or settings.DEFAULT_FROM_EMAIL,
                subject=subject_part,
                message=text_part,
                html_message=html_part,
                headers=headers,
                priority='now',
                attachments=[
                    (filename, content, mimetype)
                    for filename, content, mimetype in (
                        (f[0], f[1].read(), f[1].content_type)
                        for f in files or []
                    )
                ] if files else None
            )
            return 1 if email else 0
        except Exception as e:
            logger.exception("Error sending email via post_office to {}".format(recipients))
            if not fail_silently:
                raise
            return 0
    else:
        # Standard sending for Anymail/SMTP backends
        try:
            return msg.send(fail_silently=fail_silently)
        except SMTPException as e:
            logger.exception(
                "SMTPException raised while sending email to {}".format(recipients)
            )
            if not fail_silently:
                raise
            return 0
