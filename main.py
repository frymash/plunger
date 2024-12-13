""" Plunger - Email unsubscriber

Adapted from "Automate Your Life Using Python! (Email Unsubscribe with Python Tutorial)"
by Tech With Tim https://www.youtube.com/watch?v=rBEQL2tC2xY

This program helps you unsubscribe to every mailing list that clogs your inboxes up.

Feature wishlist (in order of difficulty):
- feat: allow users to choose which mailing lists they want to purge
- feat: introduce Google OAuth in place of app passwords
- feat: introduce unit tests
- feat: allow users to purge emails from specific mailing lists.
"""

import email
import imaplib
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm import tqdm
load_dotenv()

READING_EMAILS_MESSAGE = "Hold it right there, we're looking for unsub links in your inbox"

email_address = os.getenv("EMAIL_ADDRESS")
password = os.getenv("PASSWORD")

def connect_to_mail() -> imaplib.IMAP4_SSL:
    """Establishes a SSL connection to an IMAP server

    Returns:
        imaplib.IMAP4_SSL: an IMAP4 client object that is connected to the mail server
    """
    imap_server = "imap.gmail.com"
    mail = imaplib.IMAP4_SSL(imap_server)
    print("Logging in to", email_address, "...")
    mail.login(email_address, password)
    print("Logged in successfully.\n")
    mail.select("inbox")
    return mail


def extract_links_from_html(html_content: str) -> list[str]:
    """Returns unsubscribe links in from emails in your inbox.

    Args:
        html_content (str): HTML content from emails in your inbox.

    Returns:
        list[str]: All unsubscribe links from emails in your inbox.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    for link in soup.find_all("a", href=True):
        if "unsubscribe" in link["href"].lower():
            links.append(link["href"])
    return links


def click_links(link: str) -> int:
    """Clicks on unsubscribe links within emails.

    Args:
        link (str): an unsubscribe link
    """
    try:
        while True:
            confirm_click = input(f"Unsub from {link}? (y/n) ").lower()
            match confirm_click:
                case "y":
                    break
                case "n":
                    return
                case _:
                    print("Invalid input provided. Try again.")
                    continue
        response = requests.get(link, timeout=10)
        if response.status_code == 200:
            print("Successfully visited", link, "\n")
        else:
            print("Failed to visit", link,
                  "(Error code:", response.status_code, ")")
        return response.status_code
    except Exception as e:
        print("Error with", link, str(e))


def search_for_unsub_links() -> list[str]:
    """Searches for emails with unsubscribe links.

    Returns:
        list[str]: a list containing unsubscribe links from your email.
    """
    mail = connect_to_mail()
    print("Searching for unsubscribe links....")
    _, search_data = mail.search(None, '(BODY "unsubscribe")')
    data = search_data[0].split()
    links = []

    for num in tqdm(data, READING_EMAILS_MESSAGE):
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type == "text/html":
                    html_content = part.get_payload(decode=True).decode()
                    links.extend(extract_links_from_html(html_content))

        else:
            content_type = msg.get_content_type()
            content = msg.get_payload(decode=True).decode()
            if content_type == "text/html":
                links.extend(extract_links_from_html(content))

    mail.logout()
    return links


def save_links(links: list[str]):
    """Writes all unsubscribe links from your email to links.txt.

    Args:
        links (list[str]): A list of all the unsubscribe links from your email.
    """
    with open("links.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(links))


def main():
    """Unsubscribes to all emails """
    links = list(set(search_for_unsub_links()))
    # ic(links)
    links_visited = 0
    for link in links:
        status = click_links(link)
        if status == 200:
            links_visited += 1
    print("Links clicked:", links_visited)
    save_links(links)
    print("The unsubscribe links have been saved to ./links.txt")

if __name__ == "__main__":
    main()
