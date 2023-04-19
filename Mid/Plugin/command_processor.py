import os
from datetime import datetime


def process_command(command, context_path, user_number, persona):
    #在以后，我可能会逐步扩充指令集，在指令很多的时候，我是否有必要将processcommand函数放在另一个文件中？
    #这只是一个测试程序，之后会被转变为一个bot的消息处理程序，因此你需要修改processco函数，使其会将要输出的text先返回，再在while循环中输出
    cmd_parts = command.split(" ")
    command_output = ""

    if cmd_parts[0] == "!new":
        new_file_name = f"{user_number}_{persona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        new_file_path = os.path.join(memory_path, new_file_name)
        with open(new_file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        command_output = "New conversation started."
    elif cmd_parts[0] == "!change":
        if len(cmd_parts) > 1:
            new_persona = cmd_parts[1]
            scenario_file_path = os.path.join(scenario_path, f"{new_persona}.json")
            if os.path.exists(scenario_file_path):
                command_output = f"Persona changed to {new_persona}."
                persona = new_persona
            else:
                command_output = f"Persona '{new_persona}' not found. Keeping current persona."
        else:
            command_output = "Please provide a persona name."
    elif command == "!end":
        return "end", persona, command_output
    else:
        command_output = "Invalid command."

    return context_path, persona, command_output