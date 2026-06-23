from flask import Flask, request
from dotenv import load_dotenv
import os
import my_logging
import logging
import threading
from supabase import create_client
from nylas_tools import send_draft
from nylas import Client

from rag_nylas import my_index
from llama_index.storage.chat_store.postgres import PostgresChatStore
from llama_index.llms.groq import Groq
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole

load_dotenv(dotenv_path=r'F:\udemy\mera-llama-index-project\.env')

# 1. Setup logging
x_logger = logging.getLogger(__name__)
x_logger.info('Code started')


# SYSTEM PROMPT
my_system_prompt = """
You are a helpful assistant that assists the customer's in products return queries. Be blunt and direct. Answer under 70 words. Alway start your answers with 'Hi, I am the assistant from Nevatech company'
"""


# 2. LLM CONFIG
llm = Groq(model='qwen/qwen3-32b', api_key=os.getenv('GROQ_API_KEY_FREE_1'))


# 3. Intialize Supabase Client
DB_URL = os.getenv('SB_DB_URL_1')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('supabase_api_key_1')
supabase_client  = create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)


# 4. Create the Chat store
chat_store = PostgresChatStore.from_uri(
    uri=DB_URL

)

    


# 7. Create the Nylas Client
my_nylas = Client(os.getenv('nylas_api_key_3'))

# 8. Create the flask instance
backend_app = Flask(__name__)

# -----------------------------------------------------------------------------------------------
#                       BACKGROUND TASK
# -----------------------------------------------------------------------------------------------
def back_task(email_data):
    try:
        if email_data:
            
            # So that the system every time does not have to go thorught the calculation
            my_email= email_data['data']['object']
            # Extracting the thread Id
            thread_id = my_email['thread_id']

            # Extracting the Grant Id
            grant_id = my_email['grant_id']

            # Extracting the email Id
            email_id = my_email['id']

            # Fetching the email body via the Nylas Client
            raw_message = my_nylas.messages.clean_messages(grant_id,request_body={'message_id' : [email_id]})
            email_message = raw_message[0][0].conversation

            # Extracting the email address
            email_address = my_email['from']

            # Extracting the subject
            my_subject = my_email['subject']
            subject = 'Re: ' + my_subject


            


            # Extracting the folder type of the email
            email_type = my_email['folders']
            

            supabase_client.table('Emails').insert({
                'email_data': email_data,
                'thread_id' : thread_id,
                'email_id' : email_id,
                'grant_id' : grant_id,
                'email_address' : email_address,
                'subject': subject,
                'message': email_message,
                'email_type': email_type
            
                }).execute()
            
            
            if not email_type == ['SENT']: 
                session_key = str(email_address[0]['email']) + '::' + str(thread_id)
                chat_memory = ChatMemoryBuffer.from_defaults(
                                                        token_limit= 3500,
                                                        chat_store=chat_store,
                                                        chat_store_key=session_key
                                                        )
                # B. Pulling CHAT HISTORY from SUPABASE        
                chat_history = chat_memory.get()
                # C. Build the Chat Engine (USE CHAT HISTORY NOT CHAT MEMORY)
                chat_engine = my_index.as_chat_engine(
                    chat_mode='context',
                    llm=llm,
                    chat_history = chat_history,
                    system_prompt=(my_system_prompt)
                )
                # D. Call the Chat Engine with the USER QUERY.
                rag_response = chat_engine.chat(message=email_message)
                # E. Clean the RAG RESPONSE
                if rag_response:
                      rag_response = str(rag_response.response.split('</think>')[-1].strip())
                
                # E. Create the USER MSG and add it to SUPABASE CHAT_HISTORY
                USER_MSG = ChatMessage(role=MessageRole.USER, content=email_message)
                chat_memory.put(USER_MSG)

                x_logger.info('/' * 80)
                x_logger.info(f' email_address: {email_address} ')
                x_logger.info(f' RAG response: {rag_response} ')
                x_logger.info(f' Subject: {subject} ')
                send_draft(nylas_obj=my_nylas, grant_id=grant_id,msg_id=email_id,subject=subject,to=email_address,body=rag_response)
                x_logger.info(f'Saved the data on chat history Supabase')
         
            elif email_type == ['SENT'] :
                try:
                    session_key = str(email_address[0]['email']) + '::' + str(thread_id)
                    chat_memory = ChatMemoryBuffer.from_defaults(
                                                        token_limit= 3500,
                                                        chat_store=chat_store,
                                                        chat_store_key=session_key
                                                        )
                    AI_MSG = ChatMessage(role = MessageRole.ASSISTANT, content=email_message)
                    chat_memory.put(AI_MSG)
                    x_logger.info('AI EDITED response SUCCESSFULLY ADDED to SUPABASE')
                except :
                    x_logger.exception('Error in the SENT TYPE part!')
                    
               
            else:
                x_logger.critical(f'Saved a different type email: {email_type}-------{email_id}')
                raise ValueError('EMAIL TYPE IS NOT VALID')
        else:
            x_logger.critical(f'We have a FAKE EMAIL DATA: {email_data}')
            raise ValueError('EMAIL DATA IS NOT VALID')
            
    except Exception as e:
        x_logger.exception('Error inside the back task function!!')

# -----------------------------------------------------------------------------------------------
#                       MAIN FLASK + SUPABASE TASK
# -----------------------------------------------------------------------------------------------

@backend_app.route('/webhook', methods = ['POST', 'GET'])
def testing_route():
    try:

        if request.method == 'GET':
            return request.args.get('challenge', '')

        elif request.method == 'POST':
            
            print(f'--------------Got a post request---------')
            
            x_logger.info(f'Got a new request. Method : {request.method}')
            
            # Fetch teh json email body
            email_data = request.get_json()

            if email_data:
                    x_logger.info(f'This is the folders: {email_data['data']['object']['folders']}')
                    # STEP 1 : Exactract the unique email id from the Nylas webhook(post request)
                    try:
                        email_id = email_data['data']['object']['id']
                    except Exception as e :
                        x_logger.exception('Error with the email id')
                    
                    # STEP 2: Now insert the Email id into the SUPABASE TABLE
                    try:
                        # Insert the email id in the SUPABASE TABLE
                        #----------------------------------------------
                        # If the Email id already exists then the SUPABASE code will throw an error due to which the code will
                        # shift to the 'Except' block.

                        supabase_client.table('nylas_email_ids').insert({"email_ids" : email_id}).execute()
                        # STEP 3: Hooray! New id. Hand it off to the Background thread!
                        x_logger.info(f'---------Email id :{email_id} has been Upserted into the SUPABASE table!!--------')
                        my_thread = threading.Thread(target=back_task,args=(email_data,))
                        my_thread.start()
                    except Exception as e:
                        # STEP 4: The Duplicate Email id appeared
                        # Write it in the logs
                        x_logger.error(f'Duplicate Email id DETECTED: {email_id}, Rejecting the request!!')

                    return 'OK', 200          

        else:
            print(f'\n{'+'*30}\n------------ERROR---------\n{'+'*30}\n')

    except Exception as e:
        x_logger.exception(f'error here{'-' * 100}: \n{e}\n{'-' * 100}')

if __name__ == "__main__":
    backend_app.run(port=5000, debug=True, use_reloader = False)


    
