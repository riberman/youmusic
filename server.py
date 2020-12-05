# libs
from __future__ import unicode_literals
import time

# youtube_dl downloader
import youtube_dl

# multiprocessing
from multiprocessing import Process, Manager

# http server
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# socket
import socket
import threading

ydl_opts = {}

# Create Manage to share values in process
manager = Manager()
youtube_queue = manager.dict()
list_of_clients = manager.list()
boolean = manager.dict()
boolean["flag"] = True

host_name = "localhost"
http_port = 9000
socket_port = 9007

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = sock.bind((host_name, socket_port))
sock.listen(100)
print(time.asctime(), "Socket Server Starts - %s:%s" % (host_name, socket_port))

def make_handler():

    class YouMusicServer(BaseHTTPRequestHandler):

        def do_GET(self):
            print(time.asctime(), "YouMusicServer - New GET Resquest")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes("{\"name\": \"youmusicserver\",\n \"status\": \"ok\"}", "utf-8"))

        def do_POST(self):
            print(time.asctime(), "YouMusicServer - New POST Resquest")
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len).decode("utf8")
            try:
                resp_json = json.loads(post_body)

                youtube_queue[resp_json["url"]] = {"folder": resp_json["folder"]}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = bytes("{\"name\": \"youmusicserver\",\n \"status\": \"ok\",\n \"url\": \"%s\",\n \"folder\": \"%s\"}" % (resp_json["url"], resp_json["folder"]), "utf-8")

            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = bytes("{\"name\": \"youmusicserver\",\n \"status\": \"bad request\"}", "utf-8")

            self.wfile.write(response)

    return YouMusicServer

def clientThread(connection, address):
    connection.send(str("You are connected!").encode())
    client_active = True
    while client_active:
        try:
            received = connection.recv(2048).decode()

            if received:
                if received != "exit":
                    message =  str(address[0] + " >>> " + received)
                    broadcast(message)
                else:
                    print(address[0] + " Disconnected")
                    broadcast("exit")
                    remove(connection)
                    client_active = False

        except Exception as e:
            print(e)

def broadcast(message):
    for client in list_of_clients:
        try:
            print(message)
            client.send(str(message).encode())
        except Exception as e:
            print(e)
            client.close()
            remove(client)

def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)

def my_hook(d):
    if d['status'] == 'finished':
        broadcast(time.asctime() + " - Done downloading")
    if d['status'] == 'downloading':
        broadcast(time.asctime() + " - " + d['filename'] + " - " + d['_percent_str'])

def workerYoutubeDownloader():
    while boolean["flag"]:
        if (len(youtube_queue) > 0):
            print(time.asctime(), "workerYoutubeDownloader - Begin job")
            job = next(iter(youtube_queue.copy()))
            ydl_opts = {
                'outtmpl': 'downloaded_music/' + youtube_queue[job]['folder'] + '/%(title)s-%(id)s.%(ext)s',
                'format': 'bestaudio/best',
                'progress_hooks': [my_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([job])
                del youtube_queue[job]
            except Exception as e:
                print(time.asctime(), "workerYoutubeDownloader - " + str(e))
        else:
            print(time.asctime(), "workerYoutubeDownloader - No jobs")
        time.sleep(5)

def startServer():
    print(time.asctime(), "Server Starts - %s:%s" % (host_name, http_port))
    myServer = HTTPServer((host_name, http_port), make_handler())
    myServer.serve_forever()

def startSocketServer():
    while boolean["flag"]:
        print(time.asctime(), "startSocketServer - wait new client")
        connection, address = sock.accept()
        list_of_clients.append(connection)
        print(address[0] + " connected on server")
        p1 = Process(target=clientThread, args=(connection, address,))
        p1.start()
    p1.terminate()

if __name__ == '__main__':
    try:
        p1 = Process(target=startSocketServer)
        p2 = Process(target=startServer)
        p3 = Process(target=workerYoutubeDownloader)
        p1.start()
        p2.start()
        p3.start()
        p1.join()
        p2.join()
        p3.join()
    except KeyboardInterrupt:
        pass
        broadcast("exit")
        myServer.server_close()
        print(time.asctime(), "Server Stop - %s:%s" % (host_name, http_port))
        p1.terminate()
        p2.terminate()
        p3.terminate()
        server.shutdown(sock.SHUT_RDWR)
        server.close()
        print(time.asctime(), "Socket Server Stop - %s:%s" % (host_name, socket_port))
        boolean["flag"] = False
