import asyncio
import lmstudio as lms
import gradio as gr
from gmailsvc import GmailService

#Initialize LLM and LMS
llmmodel  = "meta-llama-3.1-8b-instruct"
lmsllm    = lms.llm(llmmodel)
lmschat   = lms.Chat("""You are AI assistant. Your name is Maya. You are polite but witty.
                        DO NOT CALL THE SAME TOOL MULTIPLE TIMES WITHOUT USER CONFIRMATION""")

#TODO - Initialize GMAIL Client. Hardcoded the functions here. Prefer to source it from mcp-client against mcp-server
gmailsvc   = GmailService()
gmailtools = [gmailsvc.gecho,gmailsvc.glogin,gmailsvc.glabels,gmailsvc.gmessages,gmailsvc.gthreads,gmailsvc.gmessagedetail,gmailsvc.gmove]

def tool_error_handler(exc: lms.LMStudioPredictionError, request: lms.ToolCallRequest | None):
    print(f"{exc} {request}")
    return f"Invalid tool call. Only available tools are {gmailtools}"

async def handle_chat_input(prompt, history):
    #Append current prompt, generate response to lmschat
    lmschat.add_user_message(prompt)
    lmsllm.act(lmschat,gmailtools,max_prediction_rounds=2,on_message=lmschat.append,handle_invalid_tool_request=tool_error_handler)

    #Extract last assistant response to history for gradio ChatInterface
    history += [{"role":"user", "content":prompt}]
    for c in lmschat._get_last_message("assistant").content:
      history += [{"role":"assistant", "content":c.text} ]
    return history , gr.Textbox(value="")

async def main():
    with gr.Blocks(title="Maya AI", fill_height=True) as app:
      gr.Markdown(f"I am Maya. Your AI Mail assistant. I am here to help you with your queries using *{llmmodel}*")
      chatbot = gr.Chatbot(
                  value=[],
                  height= 500,
                  type="messages",
                  show_copy_button=True,
                  avatar_images=("images/User.png", "images/AI.png")
                )
      with gr.Row(equal_height=True):
        msg = gr.Textbox(
                    label="Your question",
                    placeholder="Please enter your question",
                    scale=4
                  )
        clear_btn = gr.Button("Clear",scale=1)
      clear_btn.click(lambda: [], None, chatbot)
      msg.submit(handle_chat_input,[msg,chatbot], [chatbot,msg])

    #ChatInterface will be available at http://127.0.0.1:7860
    app.launch(share=False, server_name="127.0.0.1", server_port=7860, pwa=True)

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    try:
       SystemExit(130)
    except:
       print(f"Killed")