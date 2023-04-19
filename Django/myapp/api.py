from rest_framework.decorators import api_view


from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .openai_key import key
import requests
import json
import sys;
sys.path.append(r'E:\System\key')
import key1
import os

openai_secret_key = key1.key

@api_view(['POST'])
def chat_api(request):
    data = json.loads(request.data['data'])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_secret_key}'
    }
    response = requests.post('https://service-r7j07fhi-1317823330.hk.apigw.tencentcs.com/v1/chat/completions', headers=headers, json=data)
    # response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    response_data = response.json()
    print(response_data)
    text = response_data["choices"][0]
    return Response({'text': text})

# @api_view(['GET','POST'])
# def chat_api(request):
#     message = request.GET['msg']
#     print(message)
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {openai_secret_key}'
#     }
#     data = {
#         "model": "gpt-3.5-turbo",
#         "messages": [{"role": "user", "content": message}],
#         "temperature": 0.7
#     }
#     response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
#     response_data = response.json()
#     text = response_data["choices"][0]
#     return Response({'text': text})