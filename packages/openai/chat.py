#--web true
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import subprocess,json, socket
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

def verifica_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    else:
        return False
    
def verifica_ip(ip):
    #pattern = r'^\w+(\.\w+){1,2}$'
    pattern = r'\b\w+(\.\w+){1,2}(\.\w+)?\b'
    if re.match(pattern, ip):
        return True
    else:
        return False

def verifica_chess(string):
    pattern =  r'\bchess\b'
    if re.search(pattern, string):
        return True
    else:
        pattern =  r'\bscacchi\b'
        if re.search(pattern, string):
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

def chiamata_api_curl():
    username = "scardone"
    password = "26gcREBJ5jH7GDx"
    url = "https://nuvolaris.dev/api/v1/web/utils/demo/slack\?text=ciao+ciao"
    try:
        comando = ['curl', '-u', '{}:{}'.format(username, password) , '-s', url]
        output = subprocess.check_output(comando).decode('utf-8').strip()
        if output == "ok":
            return output
        else: 
            errore = json.loads(output)
            messaggio = "si è verificato un errore: " + errore["error"]
            print("Si è verificato un errore",errore)
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
        return {
                "output":  "Alla tua richiesta di "+string+" ho associato il FEN: "+ fen,
                "title": "Il tuo puzzle ",
                "message": f"Con FEN: {fen} associato al {string}"
            }
    
    except subprocess.CalledProcessError as e:
        print("Errore nel curl", e)
        return {"output":"Mi spiaze!"}


def main(args):
    global AI
    global allerta_chess, input_bk
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Ciao! Welcome To the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    elif verifica_email(input):
        output = chiamata_api_curl()
    
        res = {
            "output": "Ho verificato l'indirizzo email: "+ input +"!  ",
            "title": "Chiamata CURL ",
            "message": "Con esito: "+ output
        }
    elif verifica_ip(input):
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
            if input.upper()=="YES":
                res = chiamata_api_curlPro("https://pychess.run.goorm.io/api/puzzle?limit=1", input_bk)
            else:
                res = {
                "output": "Risposta: "+ input.upper(),
                "title": "Chiamata CHESS ",
                "message": "Con esito: da verificare"
                }

    elif verifica_chess(input):
        output = f"Is the following a request for a chess puzzle: {input}: Answer Yes or No."
        res = {"output": output}
        allerta_chess = True
        input_bk = input
    

    else:
        output = ask(input)
        res = extract(output)
        res['output'] = output

    return {"body": res }
