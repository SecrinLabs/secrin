from mails.types import MailType

# Define what variables each template expects
TEMPLATE_VARS = {
    MailType.INVITE: ["invite_link", "user_name"],
    MailType.WAITINGLIST: ["name", "email", "subject"]
}
