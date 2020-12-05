from __future__ import unicode_literals
import youtube_dl
import time
from multiprocessing import Process, Manager
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

ydl_opts = {}

hostName = "localhost"
hostPort = 9000

def make_handler(youtube_queue):

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
                respJson = json.loads(post_body)

                youtube_queue[respJson["url"]] = {"folder": respJson["folder"], "client_uuid": respJson["client_uuid"]}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = bytes("{\"name\": \"youmusicserver\",\n \"status\": \"ok\",\n \"url\": \"%s\",\n \"folder\": \"%s\"}" % (respJson["url"], respJson["folder"]), "utf-8")

            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = bytes("{\"name\": \"youmusicserver\",\n \"status\": \"bad request\"}", "utf-8")

            self.wfile.write(response)

    return YouMusicServer

def my_hook(d):
    if d['status'] == 'finished':
        print("Done downloading")
    if d['status'] == 'downloading':
        print(d['filename'], d['_percent_str'])

def workerYoutbeDownloader(youtube_queue):
    while True:
        if (len(youtube_queue) > 0):
            print(time.asctime(), "workerYoutbeDownloader - Begin job")
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
                print(time.asctime(), "workerYoutbeDownloader - " + str(e))
        else:
            print(time.asctime(), "workerYoutbeDownloader - No jobs")
        time.sleep(5)

def startServer(youtube_queue):
    print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))
    myServer = HTTPServer((hostName, hostPort), make_handler(youtube_queue))
    myServer.serve_forever()

if __name__ == '__main__':
    try:
        manager = Manager()
        youtube_queue = manager.dict()
        p1 = Process(target=startServer, args=(youtube_queue,))
        p2 = Process(target=workerYoutbeDownloader, args=(youtube_queue,))
        p1.start()
        p2.start()
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        pass
        myServer.server_close()
        print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
        p1.terminate()
        p2.terminate()
