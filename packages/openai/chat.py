#--web true
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
from requests.auth import HTTPBasicAuth

#from dotenv import load_dotenv
import subprocess,json, socket, requests
import re

ROLE = """
When requested to write code, pick Python.
When requested to show chess position, always use the FEN notation.
When showing HTML, always include what is in the body tag, 
but exclude the code surrounding the actual content. 
So exclude always BODY, HEAD and HTML .
"""

MODEL = "gpt-35-turbo"
AI = None
allerta_chess = False
input_bk = ''
#load_dotenv()
#api_key = os.getenv("OPENAI_API_KEY")

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"

"""
import re
from pathlib import Path
text = Path("util/test/chess.txt").read_text()
text = Path("util/test/html.txt").read_text()
text = Path("util/test/code.txt").read_text()
"""
def extract(text):
    res = {}

    # search for a chess position
    pattern = r'(([rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8} [bw] (-|K?Q?k?q?) (-|[a-h][36]) \d+ \d+)'
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    #print(m)
    if len(m) > 0:
        res['chess'] = m[0][0]
        return res

    # search for code
    pattern = r"```(\w+)\n(.*?)```"
    m = re.findall(pattern, text, re.DOTALL)
    if len(m) > 0:
        if m[0][0] == "html":
            html = m[0][1]
            # extract the body if any
            pattern = r"<body.*?>(.*?)</body>"
            m = re.findall(pattern, html, re.DOTALL)
            if m:
                html = m[0]
            res['html'] = html
            return res
        res['language'] = m[0][0]
        res['code'] = m[0][1]
        return res
    return res

def verifica_regex(pattern,email):
    if re.search(pattern, email):
        return True
    else:
        return False
    
def risolvoDominio(dominio):
    try:
        indirizzo_IP = socket.gethostbyname(dominio)
        return {
            "output": "Risovi domionio "+dominio,
            "title": "Dominio " + dominio,
            "message": "L'indirizzo IP è "+indirizzo_IP,
            "ip": indirizzo_IP
        }
    except socket.gaierror as e: 
        return {
            "output": "Risovi domionio "+dominio,
            "title": "ERRORE Dominio " + dominio,
            "message": " si è verificato un errore! " + e.strerror
        }

def ciaociao(key,psw):
    url = "https://nuvolaris.dev/api/v1/web/utils/demo/slack\?text=ciao+ciao"
    params = {'text': 'ciao ciao'}
    username = "scardone"
    password = psw
    try:
        headers = {'Authorization': f'{key}'}
        response =  requests.get(url, params=params,  auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            return 'ok'
        else:
            return  f"ko {response.text} ({str(response.status_code)})  using key: {key[0:3]}... o psw: {psw[0:3]}..."
    except:
        return None

def chiamata_api_curl(apiKey):
    username = "username"
    password= "password"

    url = "https://nuvolaris.dev/api/v1/web/utils/demo/slack\?text=ciao+ciao"
    if apiKey is None:
        return "Key non trovata"
    else:
        try:
            #comando = ['curl', '-u', '{}:{}'.format(username, password) , '-s', url]
            #comando = ['curl', '-s', url]
            comando = ['curl', '-H', f'Authorization: {apiKey}', '-s', url]
            #comando = ['curl', '-H', f'Authorization: Bearer {apiKey}', '-s', url]

            output = subprocess.check_output(comando).decode('utf-8').strip()
            if output == "ok":
                return output
            else: 
                errore = json.loads(output)
                messaggio = "si è verificato questo errore: " + errore["error"] +" using key: "+apiKey[0:10]+"..."
                #return output
                return messaggio
    
        except subprocess.CalledProcessError as e:
            print("Errore nel curl", e)
        return None


def chiamata_api_curlPro(url, string):
    try:
        comando = ['curl', '-s', url]
        output = subprocess.check_output(comando).decode('utf-8').strip()
        data = json.loads(output)
        fen = data["items"][0]["fen"]
        return fen;
    
    except subprocess.CalledProcessError as e:
        print("Errore nel curl", e)
        return {"output":"Mi spiaze!"}


def main(args):
    global AI
    global allerta_chess, input_bk
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    psw = "nuVolaris123!"
    pattern_IP = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?\b'
    pattern_EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Ciao! Welcome To the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
        #verifica email
    elif verifica_regex(pattern_EMAIL, input):
        output = ciaociao(key, psw)
        #output = chiamata_api_curl(key)
    
        res = {
            "output": "Ho verificato l'indirizzo email: "+ input +"!  ",
            "title": "Chiamata  ",
            "message": "Con esito: "+ output
        }

    elif verifica_regex(pattern_IP, input):
        try:
            output = risolvoDominio(input)
    
            res = {
            "output": "Ho verificato l'indirizzo IP, "+ input +" corrisponde a "+output["ip"],
            "title": output["title"],
            "message": "Con esito: "+ output["message"]
            }
        except:
            res = {
            "output": "Ho verificato l'indirizzo IP, "+ input +" ma si è verificato un errore",
            "title": "ERRORE",
            "message": ""
            } 

    elif allerta_chess != False:
            allerta_chess = False
            if input.upper()=="YES":
                output = chiamata_api_curlPro("https://pychess.run.goorm.io/api/puzzle?limit=1", input_bk)
                res = extract(output)
                res['output'] = f"Questo il fen della tua richiesta ({input_bk}): {output}"
        
            else:
                res = {
                "output": "Risposta: "+ input,
                "title": "Chiamata CHESS ",
                "message": "Con esito: da verificare"
                }

    elif verifica_regex(r'\bchess|scacchi\b',input) :
        output = f"Is the following a request for a chess puzzle: {input}: Answer Yes or No."
        res = {"output": output}
        allerta_chess = True
        input_bk = input

    else:
        output = ask(input)
        res = extract(output)
        res['output'] = output

    return {"body": res }
