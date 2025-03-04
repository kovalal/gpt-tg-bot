import json
from functools import partial

class FunctionCalling():

    model = "gpt-4o-mini"
    sys_prompt = "You are a model selection assistant. Your job is to analyze the user's task description, complexity, urgency, and expected output type, and select one the most appropriate model:\n- Use `gpt4o-mini` for simple or lightweight tasks.\n- Use `gpt4o` for medium complexity or general-purpose tasks.\n- Use `gpt-o1` for advanced, high-complexity, or mission-critical tasks.\n- Use `dallee-3` for any image generation tasks.\nMake sure to return only the selected model name as the output."
    tool_choice = "required"
    
    def __init__(self, client, tools):
        self.client = client
        self.tools = {tool_class.name(): tool_class(client) for tool_class in tools}

    def get_tools(self):
        return [{'type': 'function', 'function': func.scheme}
        for func in self.tools.values()]

    def messages(self, prompt):
        return [
            {
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": self.sys_prompt
                }]
            },
            *prompt]

    def choice(self, prompt):
        return self.client.generate_completion(
            model=self.model,
            messages=self.messages(prompt),
            tools=self.get_tools(),
            tool_choice=self.tool_choice
        )

    def run(self, prompt, callback=None):
        call_response = self.choice(prompt)
        print(call_response)
        tool_call = call_response.choices[0].message.tool_calls[0]
        func_name = tool_call.function.name
        call = self.tools[func_name]
        kwargs = json.loads(tool_call.function.arguments)
        return partial(call, **kwargs)
        

        # написать логику выбора функции
        # вызова этой функции
        # и обработки ответа