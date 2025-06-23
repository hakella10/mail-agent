import asyncio

from fastmcp import FastMCP
from pydantic import Field
from gmailsvc import GmailService

mcp = FastMCP(name="GmailMCP",
              instructions="Provides tools to iteract with mail server",
              mask_error_details=True)

svc = GmailService()

@mcp.tool(description="Simple loopback function which echoes back the input. This is a default tool")
def echo(any : str = Field(description="Loopback Echo", default= None)):
    return svc.gecho(any)

@mcp.tool(description="login by redirecting to consent page")
def login():
    return svc.glogin()

@mcp.tool(description="Get list of folders in user's mailbox")
def labels():
    return svc.glabels()

@mcp.tool(description="Search mails with a query")
def messages(query : str = Field(description="Query Criteria. Use keywords instead of the phrases", default= ""),
             label : str = Field(description="Search within label", default= "all")):
    return svc.gmessages(query=query, label=label)

@mcp.tool(description="Get all mails for the given threadId. A thread is combination of multiple to/fro mails in the same conversation")
def threads(threadId : str = Field(description="Get All messages for a given threadId", default= "")):
    if threadId is None:
      raise ValueError("Please provide thread Id")
    return svc.gthreads(threadId=threadId)

@mcp.tool(description="Get full details of message for the given messageId.")
def messagedetail(messageId : str = Field(description="Get full details for a given messageId", default= "")):
    if messageId is None:
      raise ValueError("Please provide message Id")
    return svc.gmessagedetail(messageId=messageId)

@mcp.tool(description="Move mails to different folder or label")
def move(messageIds : list = Field(description="Ids of the mails to be moved", default= []),
         addLabel : str = Field(description="Target folder or label to add for the mails", default=""),
         removeLabel : str = Field(description="Existing folder or label to remove for the mails", default=""),
         ):   
    if messageIds is None or len(messageIds) == 0:
      raise ValueError("Please provide message Ids to move")
    if addLabel is None and removeLabel is None:
      raise ValueError("Please provide valid label to add or remove. Use labels() to get list of valid labels")
    return svc.gmove(messageIds,addLabel,removeLabel)

async def main():
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())