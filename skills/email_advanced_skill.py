import json
import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill


class EmailAdvancedSkill(Skill):
    """Advanced email automation - compose, read, send, search emails."""

    @property
    def name(self) -> str:
        return "email_advanced"

    def initialize(self, context):
        self._context = context

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Compose and send an email.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "Recipient email address"},
                            "subject": {"type": "string", "description": "Email subject"},
                            "body": {"type": "string", "description": "Email body text"},
                            "cc": {"type": "string", "description": "CC email addresses (comma separated)"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_recent_emails",
                    "description": "Read recent emails from inbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "count": {"type": "number", "description": "Number of emails to read (default: 5)"},
                            "folder": {"type": "string", "description": "Email folder (inbox, sent, drafts)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_emails",
                    "description": "Search emails by subject, sender, or keyword.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keyword or phrase"},
                            "from_address": {"type": "string", "description": "Filter by sender email"},
                            "count": {"type": "number", "description": "Max results (default: 10)"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_email_count",
                    "description": "Get count of unread emails.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_email",
                    "description": "Delete an email by subject search.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "Subject of email to delete"}
                        },
                        "required": ["subject"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "send_email": self.send_email,
            "read_recent_emails": self.read_recent_emails,
            "search_emails": self.search_emails,
            "get_email_count": self.get_email_count,
            "delete_email": self.delete_email,
        }

    def _get_email_config(self):
        email_addr = os.environ.get("EMAIL_ADDRESS")
        password = os.environ.get("EMAIL_PASSWORD")
        imap_server = os.environ.get("EMAIL_IMAP_SERVER", "imap.gmail.com")
        smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
        return email_addr, password, imap_server, smtp_server, smtp_port

    def send_email(self, to: str, subject: str, body: str, cc: str = None) -> str:
        try:
            email_addr, password, _, smtp_server, smtp_port = self._get_email_config()
            if not email_addr or not password:
                return json.dumps({"status": "error", "message": "Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"})

            msg = MIMEMultipart()
            msg["From"] = email_addr
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = cc
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_addr, password)
                recipients = [to]
                if cc:
                    recipients.extend(cc.split(","))
                server.sendmail(email_addr, recipients, msg.as_string())

            return json.dumps({"status": "success", "message": f"Email sent to {to}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _fetch_emails(self, folder: str = "INBOX", count: int = 5, search_criteria: str = None):
        email_addr, password, imap_server, _, _ = self._get_email_config()
        if not email_addr or not password:
            return None, "Email not configured"

        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_addr, password)
        mail.select(folder)

        if search_criteria:
            _, data = mail.search(None, search_criteria)
        else:
            _, data = mail.search(None, "ALL")

        mail_ids = data[0].split()
        recent_ids = mail_ids[-count:] if len(mail_ids) >= count else mail_ids
        recent_ids.reverse()

        emails = []
        for mid in recent_ids:
            _, msg_data = mail.fetch(mid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")
            emails.append({
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body": body[:500]
            })
        mail.logout()
        return emails, None

    def read_recent_emails(self, count: int = 5, folder: str = "inbox") -> str:
        try:
            emails, error = self._fetch_emails(folder=folder.upper(), count=count)
            if error:
                return json.dumps({"status": "error", "message": error})
            return json.dumps({"status": "success", "count": len(emails), "emails": emails})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def search_emails(self, query: str, from_address: str = None, count: int = 10) -> str:
        try:
            search = f'(SUBJECT "{query}")'
            if from_address:
                search = f'(FROM "{from_address}" SUBJECT "{query}")'
            emails, error = self._fetch_emails(count=count, search_criteria=search)
            if error:
                return json.dumps({"status": "error", "message": error})
            return json.dumps({"status": "success", "count": len(emails), "emails": emails})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_email_count(self) -> str:
        try:
            email_addr, password, imap_server, _, _ = self._get_email_config()
            if not email_addr or not password:
                return json.dumps({"status": "error", "message": "Email not configured"})

            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_addr, password)
            mail.select("INBOX")
            _, data = mail.search(None, "UNSEEN")
            unread = len(data[0].split()) if data[0] else 0
            _, data = mail.search(None, "ALL")
            total = len(data[0].split()) if data[0] else 0
            mail.logout()
            return json.dumps({"status": "success", "unread": unread, "total": total})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_email(self, subject: str) -> str:
        try:
            email_addr, password, imap_server, _, _ = self._get_email_config()
            if not email_addr or not password:
                return json.dumps({"status": "error", "message": "Email not configured"})

            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_addr, password)
            mail.select("INBOX")
            _, data = mail.search(None, f'(SUBJECT "{subject}")')
            mail_ids = data[0].split()
            if not mail_ids:
                mail.logout()
                return json.dumps({"status": "error", "message": f"No email found with subject: {subject}"})
            for mid in mail_ids:
                mail.store(mid, "+FLAGS", "\\Deleted")
            mail.expunge()
            mail.logout()
            return json.dumps({"status": "success", "message": f"Deleted {len(mail_ids)} email(s) with subject: {subject}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
