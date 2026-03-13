from ollama import chat
from ollama import ChatResponse

class AI_Interface:
    history = []
    context = ""
    def __init__(self):
        self.fetch_context()
        self.clear_history()
        
    def prompt(self,message):
        self.history.append({'role':'user','content':message})
        response = chat(model = 'gemma3',messages = self.history)
        self.history.append({'role':'system','content':response['message']['content']})
        #print(f"Gemma3: {response['message']['content']}")
        return response['message']['content']


    def clear_history(self):
        self.history = [{'role':'user','content':self.context}]

    def fetch_context(self):
        try:
            with open('context.txt', 'r', encoding='utf-8') as f:
                self.context = f.read() # Read the entire file into a single 
        except FileNotFoundError:
            print("The file was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        print(self.context)

    def get_ride_wait_time(self,ride_name):
        park_id = 16
        url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
        response = requests.get(url)
        ret_str = ""
        if response.status_code == 200:
            data = response.json()
            # Iterate through rides
            for land in data['lands']:
                for ride in land['rides']:
                     ret_str += f"Ride: {ride['name']}, Wait: {ride['wait_time']} mins \n"
        else:
            ret_str += "Failed to retrieve data \n"
        return ret_str


if __name__ == "__main__":
    ai = AI_Interface()
    while(True):
        prompt = input()
        if prompt == "exit":
            print("Exitting!")
            break;
        elif prompt == "clear":
            ai.clear_history()
            print("Cleared history!")
        else:
            print("Prompted!")
            print(ai.prompt(prompt))
