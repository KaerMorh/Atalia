from nonebot import on_message
from nonebot.adapters import Event

import os
import json
import requests
import tiktoken
from datetime import datetime, timedelta
import sys

main_path = r"C:\Users\KaerMorh\Atalia\Mid"
sys.path.append(main_path)
from config import debug_mode, allow_group, perso

# import config

# perso = config.perso
# debug_mode = config.debug_mode
# main_path = config.main_path

# id = '12345'
# user_id = '183'
# msg = ''
main_path = r"C:\Users\KaerMorh\Atalia\Mid"


def initialize_paths(main_path):
    scenario_path = os.path.join(main_path, "Scenario")
    memory_path = os.path.join(main_path, "Memory")
    log_path = os.path.join(main_path, "Log")
    plugin_path = os.path.join(main_path, "Plugin", "Commands")

    os.makedirs(scenario_path, exist_ok=True)
    os.makedirs(memory_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)
    os.makedirs(plugin_path, exist_ok=True)

    return scenario_path, memory_path, log_path, plugin_path


scenario_path, memory_path, log_path, plugin_path = initialize_paths(main_path)

chatgpt = on_message()


@chatgpt.handle()
async def handle_function(event: Event):
    # perso = 'Atalia'
    # debug_mode = True
    global perso, allow_group
    is_group = False
    msg = event.get_plaintext()
    user_id = event.get_user_id()
    group_id = '1467'

    # await chatgpt.finish('')
    if ((is_group == True) and (allow_group == False)):
        await chatgpt.finish('')
    id = user_id
    if is_group:  # group manage 1
        id = group_id

    context_path = os.path.join(memory_path, initMemory(id, perso))
    if msg.startswith('!'):
        context_path, perso, command_output = process_command(
            msg, context_path, id, perso)
        await chatgpt.finish(command_output)
        if context_path == "end":
            return
        else:
            return

    if msg == 'end':
        return

    context_path = os.path.join(memory_path, initMemory(id, perso))

    persona = loadScenario(perso)
    context = load_context(context_path)
    full_conversation = persona.copy()

    if context:
        full_conversation.extend(context)

    if is_group:
        msg = groupConvert(user_id, msg)
    conversation = convert(full_conversation, msg)

    data = {
        "model": "gpt-3.5-turbo",
        "messages": conversation,
        "temperature": 0.7
    }

    response = requestApi(data)
    text = response['text']['message']['content']

    save2txt(context_path, msg, 0)
    save2txt(context_path, text, 1)

    updated_context = load_context(context_path)

    tokens_used = num_tokens_from_messages(updated_context)
    log_message(log_path, context_path, tokens_used, msg, text, debug_mode)

    await chatgpt.finish(text)


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


def load_context(context_path):
    with open(context_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Return None if the file is empty
    if not file_content:
        return None

    context = json.loads(file_content)

    # If the context has only one element and it's a timestamp, return an empty context
    if len(context) == 1 and "timestamp" in context[0]:
        return []

    # Remove the timestamp entry from the context
    context.pop() if context and "timestamp" in context[-1] else None

    # Ensure the last role in the context is 'assistant'
    while context and context[-1]["role"] != "assistant":
        context.pop()

    # Save the modified context back to the JSON file, without affecting the timestamp
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context + [{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}], f)

    return context


def save2txt(context_path, msg, role=0):
    with open(context_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    # If the file is empty or has an incorrect format, initialize it with an empty list
    existing_conversation = json.loads(file_content) if file_content else []

    # Remove the timestamp entry from the context
    existing_conversation.pop() if existing_conversation and "timestamp" in existing_conversation[-1] else None

    updated_conversation = convert(existing_conversation, msg, role)

    # Save the updated conversation back to the JSON file, with the timestamp
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(updated_conversation + [{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}], f)


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


def initMemory(id, persona):
    files = os.listdir(memory_path)
    json_files = [f for f in files if f.startswith(f"{id}_{persona}") and f.endswith('.json')]
    latest_file = None
    latest_timestamp = None

    for json_file in json_files:
        file_path = os.path.join(memory_path, json_file)
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        # If the file is empty or has an incorrect format, skip it
        if not file_content:
            continue

        conversation = json.loads(file_content)

        # Get the timestamp from the last entry in the conversation
        if conversation and "timestamp" in conversation[-1]:
            timestamp_str = conversation[-1]["timestamp"]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            if not latest_timestamp or timestamp > latest_timestamp:
                time_diff = datetime.now() - timestamp
                if time_diff <= timedelta(minutes=20):
                    latest_timestamp = timestamp
                    latest_file = json_file

    if latest_file:
        return latest_file
    else:
        new_file_name = f"{id}_{persona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        new_file_path = os.path.join(memory_path, new_file_name)
        with open(new_file_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        return new_file_name


def update_config(main_path, variable_name, new_value):
    config_file_path = os.path.join(main_path, "config.py")

    # Read the content of the config.py file
    with open(config_file_path, "r", encoding="utf-8") as f:
        content = f.readlines()

    # Find the line containing the variable and update its value
    try:
        variable_found = False
        for i, line in enumerate(content):
            if line.startswith(variable_name):
                content[i] = f"{variable_name} = {new_value}\n"
                variable_found = True
                break

        if not variable_found:
            raise ValueError(f"Variable '{variable_name}' not found in the config file.")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    # Write the updated content back to the config.py file
    with open(config_file_path, "w", encoding="utf-8") as f:
        f.writelines(content)


def process_command(command, context_path, id, persona):
    # 在以后，我可能会逐步扩充指令集，在指令很多的时候，我有必要将processcommand函数的内容放在另一个文件中。我创造了一个新路径/Mid/Plugin/Commands，请不要将函数放出去，而是将每个指令槽交由对应的指令文件处理。

    # 例如，收到了!stip，则应该去Plugin中寻找stip.py，如果找得到则进行相应处理，找不到则提出警告
    # 这只是一个测试程序，之后会被转变为一个bot的消息处理程序，因此你需要修改processco函数，使其会将要输出的text先返回，再在while循环中输出
    cmd_parts = command.split(" ")
    command_output = ""
    if cmd_parts[0] == "!new":
        new_file_name = f"{id}_{persona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        new_file_path = os.path.join(memory_path, new_file_name)
        with open(new_file_path, "w", encoding="utf-8") as f:
            json.dump([{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}], f)
        command_output = "New conversation started."
    elif cmd_parts[0] == "!change":
        if len(cmd_parts) > 1:
            new_persona = cmd_parts[1]
            scenario_file_path = os.path.join(scenario_path, f"{new_persona}.json")
            if os.path.exists(scenario_file_path):
                command_output = f"Persona changed to {new_persona}."
                persona = new_persona
                config_file = os.path.join(main_path, "config.py")

                with open(config_file, "r", encoding="utf-8") as file:
                    lines = file.readlines()

                with open(config_file, "w", encoding="utf-8") as file:
                    for line in lines:
                        if line.startswith("perso"):
                            file.write(f'perso = "{new_persona}"\n')
                        else:
                            file.write(line)
            else:
                command_output = f"Persona '{new_persona}' not found. Keeping current persona."
        else:
            command_output = "Please provide a persona name."
    elif command == "!end":
        return "end", persona, command_output
    else:
        command_output = "Invalid command."

    return context_path, persona, command_output


def groupConvert(user_id, msg):
    return user_id + ':' + msg



