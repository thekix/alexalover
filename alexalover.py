#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2018 Rodolfo García Peñas <kix@kix.es>
# Based on the idea of fauxmo, Copyright (c) 2015 Maker Musings
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included in
#     all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#     THE SOFTWARE.

import email.utils
import requests
import subprocess
import select
import socket
import struct
import sys
import time
import urllib
import uuid
from alexa_conf_reader import *

class alexalover:
    upnp_server = None
    alexalover_ip = None
    group = '239.255.255.250'
    dnsserver = "8.8.8.8"
    port = 1900

    debug = False
    poller = None
    devices_conf = []
    devices = []

    def set_alexalover_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((self.dnsserver, 53))
            self.alexalover_ip = s.getsockname()[0]
        except:
            self.alexalover_ip = '127.0.0.1'
        del(s)

    def __init__(self, debug):
        if debug:
            # Set the debug flag
            self.debug = True

        # Load devices from config file
        self.load_devices("alexalover.conf", ";", "#")
        self.set_alexalover_ip()

        # Start the UPnP Server
        self.upnp_server = self.start_upnp_server()

        # Create a poller to handle the socket interaction
        self.poller = poller(self)

        # Add the UPnP Server to the poller
        self.poller.add(self.upnp_server)

        for dev in self.devices_conf:
            udev = upnp_device(self, dev[0], dev[1], dev[2], self.alexalover_ip, dev[3])
            self.devices.append(udev)

        self.dbg("Entering main loop\n")

        while True:
            try:
                # Allow Ctrl-C to stop
                self.poller.poll(100)
                time.sleep(0.1)
            except Exception, e:
                self.dbg('Main loop error: %s' % e)
                self.dbg(e)
                break

    def dbg(self, msg):
        if self.debug:
            print "alexalover: %s" % msg
            sys.stdout.flush()

    def load_devices(self, conffile, delim, comment):
        acr = alexa_conf_reader(conffile, delim, comment)
        self.devices_conf = acr.get_devices()
        for n in self.devices_conf:
            self.dbg("Device loaded: %s %s %s, port %s" % (n[0], n[1], n[2], n[3]))

    def start_upnp_server(self):
        u = alexalover_upnp_server(self)
        return u

    def send_to_devices(self, sender):
        for device in self.devices:
            time.sleep(0.1)
            device.respond_to_search(sender)

    def handle_request(self, data, sender, socket):
        # Server do not do anything here. Only devices have this request
        pass

class alexa_message:
    def __init__(self, device_name, device_serial):
        self.device_name = device_name
        self.device_serial = device_serial

    def upnp_header(self, uuid, puuid, ip_address, port):
        date = email.utils.formatdate(timeval=None, localtime=False, usegmt=True)
        locn = ("http://%s:%s/setup.xml" % (ip_address, port))
        reply = ("HTTP/1.1 200 OK\r\n"
                 "CACHE-CONTROL: max-age=86400\r\n"
                 "DATE: %s\r\n"
                 "EXT:\r\n"
                 "LOCATION: %s\r\n"
                 "OPT: \"http://schemas.upnp.org/upnp/1/0/\"; ns=01\r\n"
                 "01-NLS: %s\r\n"
                 "SERVER: UPnP Server/1.0, UPnP/1.0, kix/1.0\r\n"
                 "ST: urn:Belkin:device:**\r\n"
                 "USN: uuid:%s::urn:Belkin:device:**\r\n"
                 "X-User-Agent: redsonic\r\n\r\n" % (date, locn, uuid, puuid))
        return reply

    def http_header(self, payload):
        date = email.utils.formatdate(timeval=None, localtime=False, usegmt=True)
        reply = ("HTTP/1.1 200 OK\r\n"
                 "CONTENT-LENGTH: %d\r\n"
                 "CONTENT-TYPE: text/xml charset=\"utf-8\"\r\n"
                 "DATE: %s\r\n"
                 "EXT:\r\n"
                 "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT\r\n"
                 "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                 "X-User-Agent: redsonic\r\n"
                 "CONNECTION: close\r\n"
                 "\r\n"
                 "%s" % (len(payload), date, payload))
        return reply

    def success_reply(self):
        payld = ""
        reply = self.http_header(payld)
        return reply

    def setup_reply(self):
        payld = ("<?xml version=\"1.0\"?>\r\n"
                 "<root>\r\n"
                 "  <device>\r\n"
                 "    <deviceType>urn:kix:device:controllee:1</deviceType>\r\n"
                 "    <friendlyName>%s</friendlyName>\r\n"
                 "    <manufacturer>Belkin International Inc.</manufacturer>\r\n"
                 "    <modelName>Socket</modelName>\r\n"
                 "    <modelNumber>1.0</modelNumber>\r\n"
                 "    <UDN>uuid:Socket-1_0-%s</UDN>\r\n"
                 "  </device>\r\n"
                 "</root>\r\n" % (self.device_name, self.device_serial))
        reply = self.http_header(payld)
        return reply

    def getbinarystate_reply(self, status):
        payld = (("<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\""
                  " s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">"
                  "<s:Body>"
                  "<u:GetBinaryStateResponse xmlns:u=\"urn:Belkin:service:basicevent:1\">"
                  "<BinaryState>%s</BinaryState>"
                  "</u:GetBinaryStateResponse>"
                  "</s:Body>"
                  "</s:Envelope>") % (status))
        reply = self.http_header(payld)
        return reply


# A simple utility class to wait for incoming data to be
# ready on a socket.

class poller:
    def __init__(self, al):
        if 'poll' in dir(select):
            self.use_poll = True
            self.poller = select.poll()
        else:
            self.use_poll = False
        self.targets = {}

    def add(self, target, fileno = None):
        if not fileno:
            fileno = target.fileno()
        if self.use_poll:
            self.poller.register(fileno, select.POLLIN)
        self.targets[fileno] = target

    def remove(self, target, fileno = None):
        if not fileno:
            fileno = target.fileno()
        if self.use_poll:
            self.poller.unregister(fileno)
        del(self.targets[fileno])

    def poll(self, timeout = 0):
        if self.use_poll:
            ready = self.poller.poll(timeout)
        else:
            ready = []
            if len(self.targets) > 0:
                (rlist, wlist, xlist) = select.select(self.targets.keys(), [], [], timeout)
                ready = [(x, None) for x in rlist]
        for one_ready in ready:
            target = self.targets.get(one_ready[0], None)
            if target:
                target.do_read(one_ready[0])
 
# Base class for a generic UPnP device. This is far from complete
# but it supports either specified or automatic IP address and port
# selection.

class upnp_device(object):
    @staticmethod
    def make_uuid(name):
        return ''.join(["%x" % sum([ord(c) for c in name])] + ["%x" % ord(c) for c in "%skix.es!" % name])[:14]

    def __init__(self, al, name, action_handler_on, action_handler_off, ip_address, port):
        self.al = al
        self.name = name
        self.action_handler_on = action_handler_on
        self.action_handler_off = action_handler_off
        self.ip_address = ip_address
        self.port = port
        self.status = 0

        self.serial = self.make_uuid(name)
        self.puuid = "Socket-1_0-" + self.serial
        self.uuid = uuid.uuid4()

        # Create the socket using the ip address and the port given
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip_address, self.port))

        # Save the assigned port in the struct if was 0
        if self.port == 0:
            self.port = self.socket.getsockname()[1]

        # Listen the TCP port and wait for messages (add it to the poller)
        self.socket.listen(5)
        self.al.poller.add(self)
        self.client_sockets = {}
        self.al.dbg("Device \"%s\" ready on %s:%s" % (self.name, self.ip_address, self.port))

    def fileno(self):
        return self.socket.fileno()

    def do_read(self, fileno):
        if fileno == self.socket.fileno():
            (client_socket, client_address) = self.socket.accept()
            self.al.poller.add(self, client_socket.fileno())
            self.client_sockets[client_socket.fileno()] = client_socket
        else:
            data, sender = self.client_sockets[fileno].recvfrom(4096)
            if not data:
                self.al.poller.remove(self, fileno)
                del(self.client_sockets[fileno])
            else:
                self.handle_request(data, sender, self.client_sockets[fileno])

    def handle_request(self, data, sender, socket):
        self.al.dbg("Request for device \"%s\"" % self.name)
        if data.find('GET /setup.xml HTTP/1.1') == 0:
            self.al.dbg("Reply for setup.xml")
            msg = alexa_message(self.name, self.serial)
            message = msg.setup_reply()
            socket.send(message)
        elif data.find('urn:Belkin:service:basicevent:1') != -1:
            self.al.dbg("  Request for Get or Set")
            if data.find('GetBinaryState') != -1:
                self.al.dbg("    Get request")
                msg = alexa_message(self.name, self.serial)
                message = msg.getbinarystate_reply(self.status)
                socket.send(message)
            elif data.find('SetBinaryState') != -1:
                self.al.dbg("    Set request")
                success = False
                if data.find('<BinaryState>1</BinaryState>') != -1:
                    self.al.dbg("      Reply ON for device \"%s\", running: %s" % (self.name, self.action_handler_on))
                    args = [self.action_handler_on]
                    success = not subprocess.call(args)
                    if success:
                        self.status = 1
                elif data.find('<BinaryState>0</BinaryState>') != -1:
                    self.al.dbg("      Reply to OFF for device \"%s\", running: %s" % (self.name, self.action_handler_off))
                    args = [self.action_handler_off]
                    success = not subprocess.call(args)
                    if success:
                        self.status = 0
                else:
                    self.al.dbg("      Unknown Request:")
                    self.al.dbg(data)

                if success:
                    self.al.dbg("      Sending success message")
                    msg = alexa_message(self.name, self.serial)
                    message = msg.success_reply()
                    socket.send(message)
            else:
                self.al.dbg(data)
        else:
            self.al.dbg(data)

    def respond_to_search(self, destination):
        self.al.dbg("    Responding to search - Name: \"%s\"" % self.name)
        msg = alexa_message(self.name, self.serial)
        message = msg.upnp_header(self.uuid, self.puuid, self.ip_address, self.port)
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.sendto(message, destination)
 

class alexalover_upnp_server(object):
    TIMEOUT = 0

    def __init__(self, al):
        self.al = al
        ok = True
        try:
            self.ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                self.ssock.bind(('', self.al.port))
            except Exception, e:
                self.al.dbg("UPnP Server: ERROR: Failed to bind %s:%d: %s" % (self.al.group, self.al.port, e))
                ok = False

            self.mreq = struct.pack("4sl", socket.inet_aton(self.al.group), socket.INADDR_ANY)
            try:
                self.ssock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)
            except Exception, e:
                self.al.dbg('UPnP Server: ERROR: Failed to join multicast group: %s' % e)
                ok = False

        except Exception, e:
            self.al.dbg("UPnP Server: Failed to initialize socket: %s" % e)
            return False
        if ok:
            self.al.dbg("UPnP Server: Listening for UPnP broadcasts")

    def fileno(self):
        return self.ssock.fileno()

    def do_read(self, fileno):
        data, sender = self.recvfrom(1024)
        if data:
            if data.find('M-SEARCH') == 0:
                self.al.dbg("UPnP Server: Data - M-SEARCH")
                if data.find('upnp:rootdevice') != -1:
                    # Reply only to UPnP rootdevices, not for all
                    # We sent multiple messages, but no problem
                    self.al.dbg("  UPnP Server: Data - rootdevice")
                    self.al.send_to_devices(sender)
                else:
                    self.al.dbg("  UPnP Server: Data - No discover for UPnP Rootdevices, no reply")

    def recvfrom(self,size):
        if self.TIMEOUT:
            self.ssock.setblocking(0)
            ready = select.select([self.ssock], [], [], self.TIMEOUT)[0]
        else:
            self.ssock.setblocking(1)
            ready = True

        try:
            if ready:
                return self.ssock.recvfrom(size)
            else:
                return False, False
        except Exception, e:
            self.al.dbg("UPnP Server: %s" % e)
            return False, False
