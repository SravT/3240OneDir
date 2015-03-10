#!/usr/bin/env python

#### need to fix list and get later..



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

HOST = 'localhost' #'172.27.99.118'
PORT = 8123
DIRECTORY = '/home/student/testonedirlocal'

#for watchdog
path = '/home/boom/student/OneDir/'
dest = '/home/boom/student/OneDir_server/' #'/home/sravan/OneDir/'
fileActivity = []
username = 'test_user'
synchronized = False    #current synchronize state
setSynchronize = False  #desire synchronize state

# File transfer code down below
class OnedirProtocol(basic.LineReceiver):
    delimiter = '\n'

    def __init__(self, server_ip, server_port, files_path):
        self.server_ip = server_ip
        self.server_port = server_port
        self.files_path = files_path

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
        global setSynchronize, synchronized
        """ Sends a command to the server. """
        data = clean_and_split_input(line)
        if len(data) == 0 or data == '':
            return

        command = data[0].lower()
        if not command in COMMANDS:
            self._display_message('Invalid command')
            return

        if command == 'list' or command == 'help' or command == 'quit':
            self.connection.transport.write('%s\n' % (command))

        elif command == 'register':
            try:
                username = data[1]
                password = data[2]
            except IndexError:
                self._display_message('Missing username or password')
                return
            self.connection.transport.write('%s %s %s\n' % (command, username, password))

        elif command == 'login':
            try:
                username = data[1]
                password = data[2]
            except IndexError:
                self._display_message('Missing username or password')
                return
            self.connection.transport.write('%s %s %s\n' % (command, username, password))

        elif command == 'get':
            try:
                filename = data[1]
            except IndexError:
                self._display_message('Missing filename')
                return

            self.connection.transport.write('%s %s\n' % (command, filename))
        elif command == 'put':
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

            self.connection.transport.write('PUT %s %s\n' % (filename, get_file_md5_hash(file_path)))
            self.setRawMode()

            for bytes in read_bytes_from_file(file_path):
                self.connection.transport.write(bytes)

            self.connection.transport.write('\r\n')

            # When the transfer is finished, we go back to the line mode 
            self.setLineMode()
        elif command == 'rename':
            """renames file or directory src to dst and returns True if successful"""
            src = '';
            dst = '';
            input = clean_and_split_input(line)
            if len(input) == 3:
                src = input[1];
                dst = input[2];
            if os.path.isfile(src) or os.path.isdir(src):
                try:
                    os.renames(src, dst)
                    return True
                except OSError, e:
                    print e
                    return False
            else:
                print "%s does not exist" % src
                return False
        elif command == 'delete':
            src = '';
            input = clean_and_split_input(line)
            if len(input) == 2:
                src = input[1];
            if os.path.isdir(src):
                try:
                    shutil.rmtree(src)
                    return True
                except OSError, e:
                    print e
                    return False
                except shutil.Error, e:
                    print e
                    return False
            elif os.path.isfile(src):
                try:
                    os.remove(src)
                    return True
                except OSError, e:
                    print e
                    return False
            else:
                print "%s does not exist" % src
                return False
        elif command == 'create':
            src = '';
            input = clean_and_split_input(line)
            if len(input) == 2:
                src = input[1];
            if not os.path.exists(src):
                try:
                    os.makedirs(src)
                    return True
                except OSError, e:
                    print e
                    return False
            else:
                print "%s already exists" % src
                return False
        elif command == 'syncon':
            #turn on synchronization
            setSynchronize = True
        elif command == 'syncoff':
            #turn off the synchronization
            setSynchronize = False
        else:
            self.connection.transport.write('%s %s\n' % (command, data[1]))

        self.factory.deferred.addCallback(self._display_response)

    def _display_response(self, lines=None):
        """ Displays a server response. """

        if lines:
            for line in lines:
                print '%s' % (line)

        self._prompt()
        self.factory.deferred = defer.Deferred()

    def _prompt(self):
        """ Prompts user for input. """
        self.transport.write('> ')

    def _display_message(self, message):
        """ Helper function which prints a message and prompts user for input. """

        print message
        self._prompt()


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
        print(line)
        if line == 'ENDMSG':
            print("here")
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
        global fileActivity, path, dest,username, synchronized, path,setSynchronize
        fileList = []
        if setSynchronize and (not synchronized):
            print("Start synchronization")
            #deleting the old oneDir and creating new oneDir
            print("Deleting previously stored oneDir on server")

            src = dest + username + '/OneDir'

            #have to replace ' ' with '|' to prevent ' ' error
            src_new = src.replace(' ','|')

            (self.server)[0].transport.write('DELETE %s %s\n' % (src_new, 0))

            #for directory
            (self.server)[0].transport.write('PUTDIR %s %s\n' % (src_new, 0))


            # When the transfer is finished, we go back to the line mode
            (self.server)[0].setLineMode()


            #upload onedir
            for root, subFolders, files in os.walk(path):
                for f in subFolders:
                    fileList.append(os.path.join(root,f))
                for file in files:
                    fileList.append(os.path.join(root,file))
            print fileList

            #upload the files
            for f in fileList:
                fileActivity.append("Upload" + "|" + (trimPath(f))[1])

            #start synchronize
            synchronized = True

        if (not setSynchronize) and synchronized:
            print("Stop synchronization")
            synchronized = False
        if synchronized:
            if(len(fileActivity) != 0):
                # (self.server)[0].transport.write(fileActivity[0]+"\n")

                #manage fileActivity
                f1 = fileActivity[0].strip().split("|")
                if(f1[0] == "Delete"):
                    print("Deleting " + f1[1])

                    src = dest + username + '/OneDir/' + f1[1]

                    #have to replace ' ' with '|' to prevent ' ' error
                    src_new = src.replace(' ','|')

                    (self.server)[0].transport.write('DELETE %s %s\n' % (src_new, 0))

                    # When the transfer is finished, we go back to the line mode
                    (self.server)[0].setLineMode()

                elif(f1[0] == "Upload"):
                    #uploading
                    print("Uploading " + path + f1[1])
                    file_path = path + f1[1]
                    filename = dest + username  + '/OneDir/'  +f1[1]
                    isDir = 0
                    ############# testing #############
                    print("current filename is " + filename)
                    print("file to append is : " + f1[1])
                    if os.path.isdir(file_path):
                        isDir = 1
                    elif os.path.isfile(file_path):
                        isDir = 0
                    else:
                        print "%s does not exist" % file_path
                        return

                    #calculate file size
                    file_size = os.path.getsize(file_path) / 1024

                    #have to replace ' ' with '|' to prevent ' ' error
                    filename_new = filename.replace(' ','|')

                    if( not isDir):
                        (self.server)[0].transport.write('PUT %s %s\n' % (filename_new, get_file_md5_hash(file_path)))
                        (self.server)[0].setRawMode()

                        for bytes in read_bytes_from_file(file_path):
                            (self.server)[0].transport.write(bytes)


                        (self.server)[0].transport.write('\r\n') #the end of raw input
                    else:
                        #for directory
                        (self.server)[0].transport.write('PUTDIR %s %s\n' % (filename_new, 0))

                    # When the transfer is finished, we go back to the line mode
                    (self.server)[0].setLineMode()

                #remove activity from the queue
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
