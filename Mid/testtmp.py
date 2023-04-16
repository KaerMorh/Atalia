import os
import openai
import json
import requests
import re
import tiktoken
from datetime import datetime

key = "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"
#

user_number = '1830616305'
debug_mode = True
scenario_path = r"C:\Users\KaerMorh\Atalia\Mid\Senario"
memory_path = r"C:\Users\KaerMorh\Atalia\Mid\Memory"
log_path = r"C:\Users\KaerMorh\Atalia\Mid\Log"
os.open


def loadScenario(name):  # 加载人格
    file_path = os.path.join(scenario_path, f"{name}.json")

    with open(file_path, "r", encoding="utf-8") as file:
        scenario_data = json.load(file)

    return scenario_data["prompt"]


def requestApi(data):  # 请求api
    payload = {
        "data": json.dumps(data)
    }
    response = requests.post('http://127.0.0.1:8000/chat-api/', data=payload)
    result = json.loads(response.text)
    text = result['text']['message']['content']
    return result


def convert(persona, msg, role=0):  # 将人格与对话合一，生成conversation user:0, assissant:1
    if role == 0:
        user_message = {
            "role": "user",
            "content": msg
        }
    else:
        user_message = {
            "role": "assistant",
            "content": msg
        }
    result = persona.copy()
    result.append(user_message)

    return result


def save2txt(context_path, msg, role=0):
    with open(context_path, "r", encoding="utf-8") as f:
        existing_conversation = json.load(f)

    updated_conversation = convert(existing_conversation, msg, role)

    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(updated_conversation, f)


# start the Thread
if not os.path.exists(context_path):
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump([], f)

msg = ''


def load_context(context_path):
    with open(context_path, "r", encoding="utf-8") as f:
        context = json.load(f)

    # Ensure the last role in the context is 'assistant'
    while context and context[-1]["role"] != "assistant":
        context.pop()

    # Save the modified context back to the JSON file
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context, f)

    return context


def log_message(log_path, context_path, tokens_used, user_msg, assistant_msg, debug_mode=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = f"{timestamp}\nUser: {user_msg}\nAssistant: {assistant_msg}\nTokens used: {tokens_used}\n\n"

    log_file_name = os.path.basename(context_path).replace(".json", ".log")
    log_file_path = os.path.join(log_path, log_file_name)

    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

    if debug_mode:
        print(log_entry)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")


def initMemory():


while msg != 'end':
    persona = loadScenario('Atalia')

    # 修改这附近，增加一个函数initMemory,传入参数为user_number,功能如下：
    # user_number+创建时间.json
    # 读取Memory下的json文件名。并寻找匹配user_number且创建时间离现在最近的json，根据里面最后一次对话的时间戳判断：如果最后一次对话和现在时间间隔不超过20分钟，则返回它的文件名；若不存在这样的json，则
    # 以user_number+当前时间作为文件名 创建新的json记录
    context_path = initMemory(user_number)

    context = load_context(context_path)

    full_conversation = persona.copy()

    if context:
        full_conversation.extend(context)

    msg = input("Please enter your message: ")
    if msg == 'end':
        break
    # Use the full_conversation variable instead of persona in the convert function
    conversation = convert(full_conversation, msg)

    data = {
        "model": "gpt-3.5-turbo",
        "messages": conversation,
        "temperature": 0.7
    }

    response = requestApi(data)
    text = response['text']['message']['content']
    print(text)

    save2txt(context_path, msg, 0)
    save2txt(context_path, text, 1)

    updated_context = load_context(context_path)

    # Calculate tokens used in the conversation
    tokens_used = num_tokens_from_messages(updated_context)
    log_message(log_path, context_path, tokens_used, msg, text, debug_mode)

# def loadScenario(name):  #加载人格
#     file_path = os.path.join(scenario_path, f"{name}.json")
#
#     with open(file_path, "r", encoding="utf-8") as file:
#         scenario_data = json.load(file)
#
#     return scenario_data["prompt"]
#
# def requestApi(data):  #请求api
#     # data = loadScenario()
#     payload = {
#         "data": json.dumps(data)
#     }
#     response = requests.post('http://127.0.0.1:8000/chat-api/', data=payload)
#     result = json.loads(response.text)
#     text = result['text']['message']['content']
#     return result
#
#
# def convert(persona, msg, role=0): #将人格与对话合一，生成conversation user:0, assissant:1
#     if role == 0:
#         user_message = {
#             "role": "user",
#             "content": msg
#         }
#     else:
#         user_message = {
#             "role": "assistant",
#             "content": msg
#         }
#     result = persona.copy()
#     result.append(user_message)
#     return result
#
# def save2txt(context_path, msg, role=0):
#     with open(context_path   as f:
#         tmp = convert(f,msg,role)
#     #需要修改，将f与msg合并为tmp，并将tmp保存为新的f
#
#
# msg = ''
# while msg != 'end':
#     persona = loadScenario('Atalia')
#     msg = input("Please enter your message: ")
#
#
#     conversation = convert(persona, msg)
#
#     data = {
#         "model": "gpt-3.5-turbo",
#         "messages": conversation,
#         "temperature": 0.7
#     }
#
#     respone = requestApi(data)
#     text = respone['text']['message']['content']
#     print(text)
#
#     save2txt(context_path,msg)
#     save2txt(context_path,text)


# openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": "Who won the world series in 2020?"},
#         {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
#         {"role": "user", "content": "Where was it played?"}
#     ]
# )


# pattern = re.compile(r"\]([^\]]*)\]")
pattern = re.compile(r"^chatGPT\s*(.*)$")  # 匹配以 chatGPT 开头的字符串，并获取后面的内容

# def requestApi(msg):
#     msg_body = {
#         "msg": msg
#     }
#     response = requests.get('http://127.0.0.1:8000/chat-api/?msg=' + msg)
#     result = json.loads(response.text)
#     text = result['text']['message']['content']
#     return result


# @chatgpt.handle()
# async def handle_function(event: Event):
#     message = event.get_plaintext()
#
#     if message:
#         match = pattern.match(message.strip())
#         if not match:
#             # 如果匹配失败则结束命令处理
#             # await chatgpt.finish("命令格式错误，请输入 chatGPT + 需要查询的内容")
#             await chatgpt.finish(message + ' ' + event.get_user_id() + ' ' + event.get_message())
#             return
#         query = match.group(1)  # 获取正则匹配结果中第一个括号中的内容
#         text = requestApi(query)
#         print(text)
#
#         # query = message
#         # text = requestApi(query)
#
#         await chatgpt.finish(text)
#     else:
#         await chatgpt.finish("请输入内容")
