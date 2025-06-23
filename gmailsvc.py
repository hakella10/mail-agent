import os.path
import base64
from pydantic import Field
from time import strftime, localtime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailService:

    AUTH_SCOPES = ["https://mail.google.com/"]
    AUTH_CREDS  = None
    GMAIL_SERVICE = None

    def __init__(self):
        self.glogin()

    def gecho(self,any : str | None):
        """
        Simple loopback function which echoes back the input. This is a default tool
        Parameters:
            any: string
        """
        return any

    def glogin(self):
        """Gmail Login by redirecting to consent page"""
        if os.path.exists("token.json"):
            self.AUTH_CREDS = Credentials.from_authorized_user_file("token.json", self.AUTH_SCOPES)
        if not self.AUTH_CREDS or not self.AUTH_CREDS.valid:
            if self.AUTH_CREDS and self.AUTH_CREDS.expired and self.AUTH_CREDS.refresh_token:
                self.AUTH_CREDS.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", self.AUTH_SCOPES)
                self.AUTH_CREDS = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(self.AUTH_CREDS.to_json())
        self.GMAIL_SERVICE = build("gmail","v1",credentials=self.AUTH_CREDS)
        return True
    
    #API    = GET https://gmail.googleapis.com/gmail/v1/users/{userId}/labels
    def glabels(self):
        """Get list of folders in user's mailbox"""
        try:
            labels = (self.GMAIL_SERVICE.users().labels().list(userId="me").execute().get('labels',[]))
            result = ["all"]
            for l in labels:
                result.append(l["name"])
            return result
        except HttpError as error: 
            return ["all"]

    #API    = GET https://gmail.googleapis.com/gmail/v1/users/{userId}/messages
    def gmessages(self,
                  query : str = Field(description="Query Criteria. Use keywords instead of the phrases.", default= ""),
                  label : str = Field(description="Search within label", default= "all") ):
        """Search mail messages using a simple query. optionally narrow the search using folder or label"""
        try:
            if (label and label != "all"):
                queryStr = f"in:{label} {query}"
            else:
                queryStr = f"{query}"

            result = []
            messages = (self.GMAIL_SERVICE.users().messages().list(userId="me",q=queryStr).execute().get('messages', []))
            limit = 10
            init  = 0
            for m in messages:
                try:
                    init += 1
                    if init > limit:
                        break
                    msg = (self.GMAIL_SERVICE.users().messages().get(userId="me",id=m["id"],format="metadata",metadataHeaders=["To", "From","Subject"]).execute())

                    mailMessage = {
                        "id":msg["id"],
                        "snippet":msg["snippet"],
                        "threadId": msg["threadId"],
                        "labelIds": msg["labelIds"],
                        "date": strftime('%a %d %b %Y, %I:%M%p', localtime(int(msg["internalDate"])/1000))
                    }

                    for h in msg["payload"]["headers"]:
                        mailMessage[h["name"]] = h["value"]
 
                    result.append(mailMessage)
                except Exception as err:
                    print(f"{err}")
                    continue;
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    #API    = GET https://gmail.googleapis.com/gmail/v1/users/{userId}/threads
    def gthreads(self,
                 threadId : str = Field(description="Get All messages for a given threadId", default= "")):
        """Get all mails for the given threadId. A thread is combination of multiple to/fro mails in the same conversation"""
        if threadId is None:
            raise ValueError("Please provide thread Id")
        try:
            thread = (self.GMAIL_SERVICE.users().threads().get(userId="me",id=threadId,format="metadata",metadataHeaders=["To", "From","Subject"]).execute())
            if thread["messages"] :
                msgs = []
                for msg in thread["messages"] :
                    msg["internalDate"] = strftime('%a %d %b %Y, %I:%M%p', localtime(int(msg["internalDate"])/1000))
                    msgs.append(msg)
                thread["messages"] = msgs
            return thread
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {}

    #API    = GET https://gmail.googleapis.com/gmail/v1/users/{userId}/messages
    def gmessagedetail(self,
                       messageId : str = Field(description="Get full details for a given messageId")):
        """Get full details of message for the given messageId."""
        if messageId is None:
            raise ValueError("Please provide message Id")
        try:
            detail = {}
            msg = (self.GMAIL_SERVICE.users().messages().get(userId="me",id=messageId,format="full").execute())
            detail["id"] = msg["id"]
            detail["threadId"] = msg["threadId"]
            detail["labelIds"] = msg["labelIds"]
            detail["snippet"]  = msg["snippet"]
            
            for h in msg["payload"]["headers"]:
                if h["name"] in ["To", "From","Subject","Date"]:
                    detail[h["name"]] = h["value"]

            detail["body"]     = []
            for p in msg["payload"]["parts"]:
                detail["body"].append(base64.urlsafe_b64decode(p["body"]["data"]))

            return detail
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    #API    = POST https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/modify 
    def gmove(self, 
              messageIds : list = Field(description="Ids of the mails to be moved", default= []),
              addLabel : str = Field(description="Target folder or label to add for the mails", default=""),
              removeLabel : str = Field(description="Existing folder or label to remove for the mails", default="")):
        """Move mails to different folder or label"""
        if messageIds is None or len(messageIds) == 0:
            raise ValueError("Please provide message Ids to be moved")
        try:
            body = {"ids": messageIds}
            if len(addLabel) > 0:
                body["addLabelIds"] = [addLabel]
            if len(removeLabel) > 0:
                body["removeLabelIds"] = [removeLabel]
            result = (self.GMAIL_SERVICE.users().messages().batchModify(userId="me",body=body).execute())
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False