DOMAINS=set("""mailinator.com guerrillamail.com guerrillamail.net sharklasers.com 10minutemail.com tempmail.com temp-mail.org yopmail.com trashmail.com getnairmail.com dispostable.com maildrop.cc throwawaymail.com fakeinbox.com mintemail.com mohmal.com emailondeck.com tempail.com burnermail.io spamgourmet.com mailnesia.com mytemp.email tempmailo.com tmail.ws mail.tm moakt.com inboxkitten.com getairmail.com 33mail.com mailcatch.com spambox.us discard.email tempr.email emltmp.com tmpmail.org tmpmail.net linshiyouxiang.net 1secmail.com 1secmail.org 1secmail.net byom.de mailpoof.com""".split())
def is_disposable(email):
    d=email.rsplit("@",1)[-1].lower()
    return d in DOMAINS or any(d.endswith("."+x) for x in DOMAINS)
