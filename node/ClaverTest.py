#!/usr/bin/python

import json
import logging
import os
import sys
import gi
import psutil
import setproctitle
import subprocess
from subprocess import check_output
import websockets
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import asyncio, threading


class ClaverTest(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)
        self.uri = "ws://localhost:6789"
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.t1 = threading.Thread(target=self.run_asyncio)
        self.t1.daemon = True
        self.t1.start()
        print(*sys.argv)    # Full executable path to this script


        setproctitle.setproctitle('Claver Dispatch')
        print(os.getpid())
        process = psutil.Process(os.getpid())
        print(process.name())
        pid_name = check_output(["pidof", "Claver Dispatch"])
        print(pid_name.decode())


    async def __authenticate_connection(self, websocket: websockets) -> bool:
        credentials = json.dumps({"agent": 'browser', "bid": 'cb6070bf-e9aa-11ea-97ab-7085c2d6de42', "token": '958058', "mode": 'WhiteBoard'})
        await websocket.send(credentials)
        response = await websocket.recv()
        data = json.loads(response)
        GLib.idle_add(self.update_gui, data)
        return True

    async def __send_data(self, data):
        message = json.dumps(data)
        await self.websocket.send(message)

    async def __run(self):
        authenticated = False
        async with websockets.connect(self.uri) as websocket:
            self.websocket = websocket
            while True:
                try:
                    if not authenticated:
                        authenticated = await self.__authenticate_connection(websocket)
                    else:
                        message = await websocket.recv()
                        data = json.loads(message)
                        GLib.idle_add(self.update_gui, data)
                except websockets.ConnectionClosed:
                    break

    def run_asyncio(self):
        try:
            self.loop.run_until_complete(self.__run())
        except KeyboardInterrupt:
            pass
        except ConnectionRefusedError:
            print("Connection refused. Server offline")

    def do_activate(self):
        window = Gtk.Window(application=self)
        window.set_title("Claver Client Test")
        window.set_default_size(500, 300)
        window.set_position(Gtk.WindowPosition.CENTER)
        # window.connect("destroy", self.finish)

        self.state_label = Gtk.Label(label="?")
        self.users_label = Gtk.Label(label="? users online")

        minus_button = Gtk.Button()
        minus_button.set_label("-")
        minus_button.connect("clicked", self.do_clicked)

        plus_button = Gtk.Button()
        plus_button.set_label("+")
        plus_button.connect("clicked", self.do_clicked)

        grid = Gtk.Grid()
        grid.set_column_spacing(35)
        grid.attach(minus_button, 0, 0, 1, 1)
        grid.attach(self.state_label, 1, 0, 1, 1)
        grid.attach(plus_button, 2, 0, 1, 1)
        grid.attach_next_to(self.users_label, minus_button, Gtk.PositionType.BOTTOM, 3, 1)
        window.add(grid)

        window.show_all()

    def do_clicked(self, button):
        if button.get_label() == "-":
            data = {"mode": "WhiteBoard", "action": "minus"}
            asyncio.run_coroutine_threadsafe(self.__send_data(data), self.loop)
        elif button.get_label() == "+":
            data = {"mode": "WhiteBoard", "action": "plus"}
            asyncio.run_coroutine_threadsafe(self.__send_data(data), self.loop)

    def update_state_label(self, text):
        self.state_label.set_text(str(text))

    def update_users_label(self, text):
        self.users_label.set_text(f"{text} users online")

    def restart_program(self):
        """Restarts the current program, with file objects and descriptors
           cleanup
        """

        try:
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            logging.error(e)

        python = sys.executable
        os.execl(python, python, *sys.argv)

    def update_gui(self, data):
        if "type" in data:
            if data["type"] == "state":
                if data["value"] == 7:
                    self.restart_program()
                else:
                    self.update_state_label(data["value"])
            elif data["type"] == "users":
                self.update_users_label(data["count"])
            else:
                print("Unsupported event")

if __name__ == "__main__":
    application = ClaverTest()
    exit_status = application.run(sys.argv)
    sys.exit(exit_status)


"""
Create a function that runs when window is being closed.
call loop.call_soon_threadsafe(loop.stop) to close websocket

Resources: Auto Updating Program
https://stackoverflow.com/questions/1750757/restarting-a-self-updating-python-script
https://stackoverflow.com/questions/11329917/restart-python-script-from-within-itself
https://docs.python.org/3/library/os.html#os.execl
https://blog.petrzemek.net/2014/03/23/restarting-a-python-script-within-itself/

Resources: Threadsafe asyncio
https://stackoverflow.com/questions/32586794/submit-a-job-to-an-asyncio-event-loop
https://stackoverflow.com/questions/26675297/asyncio-calls-running-in-gtk-main-loop
https://wiki.gnome.org/Projects/PyGObject/Threading

Resources: Managing Threads
https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
https://stackoverflow.com/questions/4541190/how-to-close-a-thread-from-within

Resources: Systemd Service
https://www.linode.com/docs/quick-answers/linux/start-service-at-boot/

Resources: Git + pip for software updates
https://hackthology.com/how-to-write-self-updating-python-programs-using-pip-and-git.html

Resources: PID
https://stackoverflow.com/questions/26688936/how-to-get-pid-by-process-name
https://www.systutorials.com/how-to-get-the-running-process-pid-in-python/
https://stackoverflow.com/questions/564695/is-there-a-way-to-change-effective-process-name-in-python
https://stackoverflow.com/questions/49098469/how-to-get-process-id-with-name-in-python
https://stackoverflow.com/questions/32295395/how-to-get-the-process-name-by-pid-in-linux-using-python
https://stackoverflow.com/questions/7787120/python-check-if-a-process-is-running-or-not
https://stackoverflow.com/questions/11329917/restart-python-script-from-within-itself?noredirect=1&lq=1

Resources: PIP
https://stackoverflow.com/questions/11248073/what-is-the-easiest-way-to-remove-all-packages-installed-by-pip
https://stackoverflow.com/questions/4536103/how-can-i-upgrade-specific-packages-using-pip-and-a-requirements-file
https://github.com/pypa/pip/issues/3610
"""