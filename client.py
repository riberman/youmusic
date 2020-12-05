import socket
import time
import threading
import requests

server_host = 'localhost'
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server_host, 9007))

flag = True
last_text_print = ""

def sendRequest(url, folder):
    headers = {'Content-type': 'application/json'}
    url_json = url.decode('utf-8')
    folder_json = folder.decode('utf-8')
    data = {"url": url_json, "folder": folder_json}
    response = requests.post(url="http://" + server_host + ":9000", json=data, timeout=5, headers=headers)
    if (response.status_code == 200):
        print("Trabalho enviado com sucesso!")
    else:
        print("Erro ao anviar trabalho.")

def receiveData(sock):
    global flag
    global last_text_print
    while flag:
        message = sock.recv(2048).decode()
        print(message)
        if "Done downloading" in message:
            print(last_text_print)

        if (message == "exit"):
            flag = False
            time.sleep(2)
    sock.close()

if __name__ == '__main__':
    t1 = threading.Thread(target=receiveData, args=(sock,))
    t1.start()
    while flag:
        try:
            last_text_print = "Enter video URL! \n"
            input_txt_url = str(input(last_text_print)).encode()
            last_text_print = "Enter name folder! \n"
            input_txt_folder = str(input(last_text_print)).encode()
            sendRequest(input_txt_url, input_txt_folder)
        except KeyboardInterrupt:
            flag = False
            time.sleep(2)
    t1.join()
