from flask import Flask, request
import threading
from nylas import Client
import os
from dotenv import load_dotenv
from nylas_tools import send_draft
import my_logging
import logging
import json
x_logger = logging.getLogger(__name__)

x_logger.info('Code started')
try:
    load_dotenv(dotenv_path=r'F:\udemy\mera-llama-index-project\.env')
    backend_app = Flask(__name__)
    
    my_nylas = Client(api_key=os.getenv("nylas_api_key_2"))
    count_num = 1
    

    @backend_app.route('/webhook', methods = ['POST', 'GET'])
    def testing_route():
        
        
        
        
        if request.method == 'GET':
            return request.args.get('challenge', '')

        elif request.method == 'POST':
            global count_num
            print(f'--------------Got a post request---------')
            
            x_logger.info('=' * 100)
            x_logger.info('=' * 100)
            x_logger.info(f'Got a new request. Method : {request.method} with count: {count_num}')
            emails = []
            count_num = count_num + 1
            email_data = request.get_json()

            if email_data:
                    print(f'This is the folders: {email_data['data']['object']['folders']}')
                    print('=' * 45)
                    """
                    my_thread_id = email_data.get('data', '').get('object', '').get('thread_id')
                    x_logger.info(f'        Email Num:       ++ {count_num} ++')
                    x_logger.info(f'        Thread id: {my_thread_id}       ')
                    grant_id = email_data.get('data', {}).get('object', {}).get('grant_id')
                    x_logger.info(f'        Grant id: {grant_id}       ')
                    #thread_messages = my_nylas.messages.list(grant_id, query_params={'thread_id' : my_thread_id})
                    folders = email_data['data']['object']['folders']
                    x_logger.info(f'        folders: {folders}       ')
                    subject = email_data['data']['object']['subject']
                    x_logger.info(f'        Subject: {subject}       ')
                    sender_address  = email_data['data']['object']['from']
                    x_logger.info(f'        Address: {sender_address}       ')
                    primary = ['Inbox', "CATEGORY_PERSONAL"]
                    """
            
            with open(file=r'F:\udemy\mera-llama-index-project\my_nylas\email_info.json', mode= 'r', encoding='utf-8') as next_file:
                data = json.load(next_file)

            data.append(email_data)
            with open(file=r'F:\udemy\mera-llama-index-project\my_nylas\email_info.json', mode= 'w', encoding='utf-8') as my_file:
                json.dump(data, my_file, indent=4 )



            """
            for label in folders:
                if label in primary:
                        x_logger.info(f'+++++++++ Loop started with Label : {label} ++++++++++++++')
                        for msg in thread_messages.data:
                            clean_email_data  = my_nylas.messages.clean_messages(grant_id, request_body={'message_id': [msg.id]})
                            x_logger.info(f'       Email Message: {clean_email_data[0][0].conversation.strip()}              ')
                            emails.append({'email' : clean_email_data[0][0].conversation.strip(), 'message_id' : msg.id, 'address': email_data['data']['object']['from'][0]['email']})
                            emails.reverse()

                        x_logger.info(f'|||||||||| Email list : {emails} ||||||||||||||')
                        send_draft(nylas_obj=my_nylas, grant_id=grant_id, msg_id=emails[-1]['message_id'], to = sender_address, subject=f'Re: {subject}', body=input('\n----------------Please provide body:----------------\n'))
            
            
                        
                elif label == 'SENT':
                        x_logger.info(f'+++++++++ Loop started with Label : {label} ++++++++++++++')
                        for msg in thread_messages.data:
                            clean_email_data  = my_nylas.messages.clean_messages(grant_id, request_body={'message_id': [msg.id]})
                            x_logger.info(f'       Email Message: {clean_email_data[0][0].conversation.strip()}              ')
                            emails.append({'email' : clean_email_data[0][0].conversation.strip(), 'message_id' : msg.id, 'address': email_data['data']['object']['from'][0]['email']})
                            emails.reverse()
                        
                        x_logger.info(f'|||||||||| Email list : {emails} ||||||||||||||')
                        return 'OK', 200
            """            
            return 'OK', 200          
    
            
        else:
            print(f'\n{'+'*30}\n------------GOT------ A ---------THIRD --------TYPE!!---------\n{'+'*30}\n')


    

except Exception as e:
    x_logger.exception(f'error here{'-' * 100}: \n{e}\n{'-' * 100}')
    
"""
threading.Thread(target=lambda: backend_app.run(port=5000, debug=True, use_reloader=False), daemon=True).start()
print('Flask app is running!!')
"""
if __name__ == "__main__":
    backend_app.run(port=5000, debug=True, use_reloader = False)


    
