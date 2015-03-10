#!/usr/bin/env python

'''
Author: Team 3 OneDir, CS 3240 At The University Of Virginia Spring 2014
Ty Dang, Sravan Tumuluri, Piyapath Siratarnsophon, Dylan Doggett
'''

import os, sys, shutil
import optparse
from twisted.internet import reactor, protocol, stdio, defer, task
from twisted.protocols import basic
from twisted.internet.protocol import ClientFactory
from common import COMMANDS, display_message, validate_file_md5_hash, get_file_md5_hash, read_bytes_from_file, clean_and_split_input
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOST = '127.0.0.1'
PORT = 8123
DIRECTORY = '/home/student/testonedirlocal'

#for watchdog

#path = '/home/boom/student/OneDir/'
path = '/home/student/OneDir/'
#dest = '/home/boom/student/OneDir_server/'
dest = '/home/student/OneDir_server/'
fileActivity = []

# File transfer code down below
class OnedirProtocol(basic.LineReceiver):
    delimiter = '\n'

    def __init__(self, server_ip, server_port, files_path):
        self.server_ip = server_ip
        self.server_port = server_port
        self.files_path = files_path
    	self.username = 0
	self.logged_in = False

    def connectionMade(self):
        self.factory = FileTransferClientFactory(self.files_path)
        self.connection = reactor.connectTCP(self.server_ip, self.server_port, self.factory)
        self.factory.deferred.addCallback(self._display_response)

    def lineReceived(self, line):
        """ If a line is received, call sendCommand(), else prompt user for input. """

        if not line:
            self._prompt()
            return

        self._sendCommand(line)

    def _sendCommand(self, line):
        """ Sends a command to the server. """

        data = clean_and_split_input(line)
        if len(data) == 0 or data == '':
            return

        command = data[0].lower()
        if not command in COMMANDS:
            self._display_message('Invalid command')
            return

        if command == 'list' or command == 'help' or command == 'quit' or command == 'registry':
            self.connection.transport.write('%s %s\n' % (command, self.username))
	
	elif command == 'register':
	    try:
		username = data[1]
		password = data[2]
		
	    except IndexError:
                self._display_message('Missing username or password')
		return

            self.connection.transport.write('%s %s %s %s\n' % (command, username, password, self.username))
	

	elif command == 'login':
	    if self.logged_in != False:
		self._display_message('You are already logged in. Log out to change users.')
		return
	    try:
		username = data[1]
		password = data[2]
	    except IndexError:
                self._display_message('Missing username or password')
		return
	    self.username = username
            self.connection.transport.write('%s %s %s %s\n' % (command, username, password, self.username))

	elif command == 'logout':
	    print "elif command == logout: ", self.logged_in
	    if self.logged_in != True:
		self._display_message('You are not logged into any account.')
		return
            self.connection.transport.write('%s %s\n' % (command, self.username))

#############################
        elif command == 'get':
	    if self.logged_in == False:
		self._display_message('You must be logged in')
		return
            try:
                filename = data[1]
            except IndexError:
                self._display_message('Missing filename')
                return
            
            self.connection.transport.write('%s %s %s\n' % (command, filename, self.username))

#############################
        elif command == 'put':

	    if self.logged_in == False:
		self._display_message('You must be logged in')
		return
            try:
                file_path = data[1]
                filename = data[2]
            except IndexError:
                self._display_message('Missing local file path or remote file name')
                return
            
            if not os.path.isfile(file_path):
                self._display_message('This file does not exist')
                return

            file_size = os.path.getsize(file_path) / 1024
            
            print 'Uploading file: %s (%d KB)' % (filename, file_size)
            
            self.connection.transport.write('PUT %s %s %s\n' % (filename, get_file_md5_hash(file_path), self.username))
            self.setRawMode()
            
            for bytes in read_bytes_from_file(file_path):
                self.connection.transport.write(bytes)
            
            self.connection.transport.write('\r\n')   
            
            # When the transfer is finished, we go back to the line mode 
            self.setLineMode()

#####################################
        elif command == 'rename':
            """renames file or directory src to dst and returns True if successful"""
	    if self.logged_in == False:
		self._display_message('You must be logged in.')
	        self._prompt()
            src = '';
            dst = '';
            input = clean_and_split_input(line)
            if len(input) == 3:
                src = input[1];
                dst = input[2];
            if os.path.isfile(src) or os.path.isdir(src):
                try:
                    os.renames(src, dst)
                    print '%s renamed to %s' % (src, dst)
	            self._prompt()
                except OSError, e:
                    print e
	            self._prompt()
            else:
                print "%s does not exist" % src
	        self._prompt()

####################################
        elif command == 'delete':

	    if self.logged_in == False:
		self._display_message('You must be logged in.')
	        self._prompt()

            src = '';
            input = clean_and_split_input(line)
            if len(input) == 2:
                src = input[1];
            if os.path.isdir(src):
                try:
                    shutil.rmtree(src)
                    print '%s removed' % src
	            self._prompt()
                except OSError, e:
                    print e
	            self._prompt()
                except shutil.Error, e:
                    print e
	            self._prompt()
            elif os.path.isfile(src):
                try:
                    os.remove(src)
                    print '%s removed' % src
	            self._prompt()
                except OSError, e:
                    print e
	            self._prompt()
            else:
                print "%s does not exist" % src
	        self._prompt()
#################################################3
        elif command == 'create':

	    if self.logged_in == False:
		self._display_message('You must be logged in.')
	        self._prompt()

            src = '';
            input = clean_and_split_input(line)
            if len(input) == 2:
                src = input[1];
            if not os.path.exists(src):
                try:
                    os.makedirs(src)
                    print '%s created' % src
	            self._prompt()
                except OSError, e:
                    print e
	            self._prompt()
            else:
                print "%s already exists" % src
	        self._prompt()
#####################################################333
        else:
            self.connection.transport.write('%s %s %s\n' % (command, data[1]), self.username)

        self.factory.deferred.addCallback(self._display_response)

    def _display_response(self, lines=None):
        """ Displays a server response. """

        if lines:
            for line in lines:
		data = self._cleanAndSplitInput(line)
		#print 'data: ', data
		if len(data) == 3 and data[0] == 'Logged' and data[1] == 'In':
			#print "display response_Logged in"
		        self.username = data[2]
			self.logged_in = True
	
			#print self.logged_in
		if len(data) == 5 and ' '.join(data[1:]) == "logged out of system":
		    	self.logged_in = False
		    	self.username = 0
                print '%s' % (line)
		#print "display response_logged in flag", self.logged_in
            

        self._prompt()
        self.factory.deferred = defer.Deferred()

    def _prompt(self):
        """ Prompts user for input. """
        self.transport.write('> ')

    def _display_message(self, message):
        """ Helper function which prints a message and prompts user for input. """

        print message
        self._prompt()

    def _cleanAndSplitInput(self, input):
	input = input.strip()
	input = input.split(' ')		
	return input


class FileTransferProtocol(basic.LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        self.buffer = []
        self.file_handler = None
        self.file_data = ()
        self.factory.serverConnectionMade(self)

        print 'Connected to the server'

    def connectionLost(self, reason):
        self.file_handler = None
        self.file_data = ()
        self.factory.serverConnectionLost(self)
        print 'Connection to the server has been lost'
        reactor.stop()

    def lineReceived(self, line):
        if line == 'ENDMSG':
            self.factory.deferred.callback(self.buffer)
            self.buffer = []
        elif line.startswith('HASH'):
            # Received a file name and hash, server is sending us a file
            data = clean_and_split_input(line)

            filename = data[1]
            file_hash = data[2]

            self.file_data = (filename, file_hash)
            self.setRawMode()
        else:
            self.buffer.append(line)

    def rawDataReceived(self, data):
        filename = self.file_data[0]
        file_path = os.path.join(self.factory.files_path, filename)

        print 'Receiving file chunk (%d KB)' % (len(data))

        if not self.file_handler:
            self.file_handler = open(file_path, 'wb')

        if data.endswith('\r\n'):
            # Last chunk
            data = data[:-2]
            self.file_handler.write(data)
            self.setLineMode()

            self.file_handler.close()
            self.file_handler = None

            if validate_file_md5_hash(file_path, self.file_data[1]):
                print 'File %s has been successfully transfered and saved' % (filename)
            else:
                os.unlink(file_path)
                print 'File %s has been successfully transfered, but deleted due to invalid MD5 hash' % (filename)
        else:
            self.file_handler.write(data)


class FileTransferClientFactory(protocol.ClientFactory):
    protocol = FileTransferProtocol

    def __init__(self, files_path):
        global path
        self.server = []
        self.files_path = files_path
        self.deferred = defer.Deferred()
        self.loopCall = task.LoopingCall(self.sendNotification)
        self.loopCall.start(0.1)
        ########### set up the automatic file monitoring for remote client ###########
        self.event_handler = MyHandler()
        observer = Observer()
        observer.schedule(self.event_handler, path= path, recursive=True)
        observer.start()
        #############################################################################

    def sendNotification(self):
        global fileActivity, path, dest
        if(len(fileActivity) != 0):
            # (self.server)[0].transport.write(fileActivity[0]+"\n")

            #manage fileActivity
            f1 = fileActivity[0].strip().split("|")
            if(f1[0] == "Delete"):
                print("Deleting " + f1[1])

                src = dest + f1[1]

                if os.path.isdir(src):
                    try:
                        shutil.rmtree(src)
                    except OSError, e:
                        print e
                    except shutil.Error, e:
                        print e
                elif os.path.isfile(src):
                    try:
                        os.remove(src)
                    except OSError, e:
                        print("error deleting file")
                        print e
                else:
                    print "%s does not exist" % src



            elif(f1[0] == "Upload"):
                #uploading
                print("Uploading " + path + f1[1])
                file_path = path + f1[1]
                filename = dest + f1[1]

                if not os.path.isfile(file_path):
                    print('ERROR: path does not exist')
                    return

                #calculate file size
                file_size = os.path.getsize(file_path) / 1024

                #have to replace ' ' with '|' to prevent ' ' error
                filename_new = filename.replace(' ','|')

                (self.server)[0].transport.write('PUT %s %s\n' % (filename_new, get_file_md5_hash(file_path)))
                (self.server)[0].setRawMode()

                for bytes in read_bytes_from_file(file_path):
                    (self.server)[0].transport.write(bytes)


                (self.server)[0].transport.write('\r\n')

                # When the transfer is finished, we go back to the line mode
                (self.server)[0].setLineMode()

            del fileActivity[0]

    def serverConnectionMade(self, server):
        self.server.append(server)

    def serverConnectionLost(self, server):
        self.server.remove(server)






#WatchDog class for file handling
class MyHandler(FileSystemEventHandler):

    def on_deleted(self, event):
        global fileActivity
        fileActivity.append("Delete" + "|" + (trimPath(event.src_path))[1] )

    def on_created(self, event):
        global fileActivity
        fileActivity.append("Upload" + "|" + (trimPath(event.src_path))[1])

    def on_moved(self, event):
        global fileActivity
        fileActivity.append("Delete" + "|" + (trimPath(event.src_path))[1] )
        fileActivity.append("Upload" + "|" + trimPath(event.dest_path)[1] )


def trimPath(somePath):
    newPath = (somePath + " ").strip()
    newPath = newPath.split(path, 1)
    return newPath


if __name__ == "__main__":
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    print "Connecting to (HOST, PORT): ", (HOST, PORT)
    print "Welcome to Team 3's OneDir! How may we help you?"

    parser = optparse.OptionParser()
    parser.add_option('--ip', action='store', type='string', dest='ip_address', default=HOST, help='137.54.12.144')
    parser.add_option('-p', '--port', action='store', type='int', dest='port', default=PORT, help='server port')
    parser.add_option('--path', action='store', type='string', dest='path', default=DIRECTORY,
                      help='directory where the incoming files are saved')

    (options, args) = parser.parse_args()

    print 'Client started, incoming files will be saved to %s' % (options.path)

    stdio.StandardIO(OnedirProtocol(options.ip_address, options.port, options.path))

    reactor.run()
