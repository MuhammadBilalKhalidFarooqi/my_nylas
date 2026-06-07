from flask import Flask, request
import threading
from nylas import Client
import os
from dotenv import load_dotenv
try:
    load_dotenv(dotenv_path=r'F:\udemy\mera-llama-index-project\.env')
    backend_app = Flask(__name__)
    email_data = 'currently nothing!!'
    my_nylas = Client(api_key=os.getenv("nylas_api_key_1"))
    emial_messages = []
    @backend_app.route('/webhook', methods = ['POST', 'GET'])


    def testing_route():
        if request.method == 'GET':
            return request.args.get('challenge', '')
#data['data']['object']['thread_id']
        elif request.method == 'POST':
            global email_data
            global clean_text
            global thread_messages
            
            email_data = request.get_json()
            my_thread_id = email_data.get('data', '').get('object', '').get('thread_id')
            
            grant_id = email_data.get('data', {}).get('object', {}).get('grant_id')
            thread_messages = my_nylas.messages.list(grant_id, query_params={'thread_id' : my_thread_id})
            folders = email_data['data']['object']['folders']

            junk = ["CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "CATEGORY_UPDATES"]
            primary = ['Inbox', "CATEGORY_PERSONAL"]
            
            for x in folders:
                if x in primary:
                    for msg in thread_messages.data:
                                
                        my_clean_email  = my_nylas.messages.clean_messages(grant_id, request_body={'message_id': [msg.id]})
                        emial_messages.append(my_clean_email[0][0].conversation.strip())
                    break        
            emial_messages.reverse()
            #clean_email = my_nylas.messages.clean_messages(grant_id, request_body= {'message_id':[message_id]})
            #clean_text = clean_email + ('\n', '=' * 35, '\n')
            return 'OK', 200
        else:
            print('GOT A THIRD TYPE!!')
except Exception as e:
    print(f'error here: {e}')
    

threading.Thread(target=lambda: backend_app.run(port=5000, debug=True, use_reloader=False), daemon=True).start()
print('Flask app is running!!')
