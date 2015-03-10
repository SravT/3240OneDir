#!/usr/bin/env python

'''
Author: Team 3 OneDir, CS 3240 At The University Of Virginia Spring 2014
Ty Dang, Sravan Tumuluri, Piyapath Siratarnsophon, Dylan Doggett
'''

import os, sys, shutil
import optparse
from twisted.internet import protocol, reactor
from twisted.protocols import basic
from time import ctime
from common import COMMANDS, display_message, validate_file_md5_hash, get_file_md5_hash, read_bytes_from_file, \
    clean_and_split_input

PORT = 8123
DIRECTORY = '/home/sravan/OneDir_server'

import login_demo

clients = []
admin = []


class FileTransferProtocol(basic.LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        self.factory.clients.append(self)
        self.file_handler = None
        self.file_data = (DIRECTORY)
        self.transport.write('Welcome to Onedir! \n')
        self.transport.write('Need help? Try typing help\n')
        self.transport.write('ENDMSG\n')

        display_message(
            'Connection from: %s (%d clients total)' % (self.transport.getPeer().host, len(self.factory.clients)))

    def connectionLost(self, reason):

        self.factory.clients.remove(self)
        self.file_handler = DIRECTORY
        self.file_data = (DIRECTORY)

        display_message(
            'Connection from %s lost (%d clients left)' % (self.transport.getPeer().host, len(self.factory.clients)))

    def lineReceived(self, line):
        global clients
        display_message('Received the following line from the client [%s]: %s' % (self.transport.getPeer().host, line))

        data = self._cleanAndSplitInput(line)
        if len(data) == 0 or data == '':
            return

        user = data.pop()
        print "in lineReceived: ", data
        command = data[0].lower()
        if not command in COMMANDS:
            self.transport.write('Invalid command\n')
            self.transport.write('ENDMSG\n')
            return

        if command != 'login' and command != 'quit' and user not in clients:
            self.transport.write('You must be logged in\n')
            self.transport.write('ENDMSG\n')
            return

        if command == 'list':
            self._send_list_of_files()

        elif command == 'get':
            try:
                filename = data[1]
            except IndexError:
                self.transport.write('Missing filename\n')
                self.transport.write('ENDMSG\n')
                return

            if not self.factory.files:
                self.factory.files = self._get_file_list()

            if not filename in self.factory.files:
                self.transport.write('File with filename %s does not exist\n' % (filename))
                self.transport.write('ENDMSG\n')
                return

            display_message('Sending file: %s (%d KB)' % (filename, self.factory.files[filename][1] / 1024))

            self.transport.write('HASH %s %s\n' % (filename, self.factory.files[filename][2]))
            self.setRawMode()

            for bytes in read_bytes_from_file(os.path.join(self.factory.files_path, filename)):
                self.transport.write(bytes)

            self.transport.write('\r\n')
            self.setLineMode()
        elif command == 'put':

            try:
                filename = data[1]
                file_hash = data[2]
                #replace the '|' back with ' '
                filename = filename.replace('|', ' ')
                file_hash = file_hash.replace('|', ' ')

            except IndexError:
                self.transport.write('Missing filename or file MD5 hash\n')
                self.transport.write('ENDMSG\n')
                return

            self.file_data = (filename, file_hash)

            # Switch to the raw mode (for receiving binary data)
            print 'Receiving file: %s' % (filename)
            self.setRawMode()
        ##################################################################



        elif command == 'putdir':

            try:
                filename = data[1]
                #replace the '|' back with ' '
                filename = filename.replace('|', ' ')

            except IndexError:
                self.transport.write('Missing filename or file MD5 hash\n')
                self.transport.write('ENDMSG\n')
                return

            os.mkdir(filename)

            # Switch to the raw mode (for receiving binary data)
            print 'Creating directory: %s' % (filename)

        elif command == 'delete':
            print "in delete"
            try:
                filename = data[1]
                #replace the '|' back with ' '
                filename = filename.replace('|', ' ')

            except IndexError:
                self.transport.write('Missing filename or file MD5 hash\n')
                self.transport.write('ENDMSG\n')
                return

            #delete the file
            if os.path.isdir(filename):
                try:
                    shutil.rmtree(filename)
                except OSError, e:
                    print e
                except shutil.Error, e:
                    print e
            elif os.path.isfile(filename):
                print("deleting file")
                try:
                    os.remove(filename)
                except OSError, e:
                    print("error deleting file")
                    print e
            else:
                print "%s does not exist" % filename

            ####################################################################
        elif command == 'help':
            self.transport.write('Available commands:\n\n')

            for key, value in COMMANDS.iteritems():
                self.transport.write('%s - %s\n' % (value[0], value[1]))

            self.transport.write('ENDMSG\n')

        elif command == 'registry':
            global admin
            if user not in admin:
                self.transport.write('%s does not have administrative rights.\n' % user)
                self.transport.write('ENDMSG\n')
            else:

                # TODO; check if user is in admin list first
                registry = login_demo.retrieve_login_info()
                self.transport.write('username\t\tpassword\t\trole\n')
                for key, value in registry.iteritems():
                    self.transport.write('%s\t\t\t%s\t\t\t%s\n' % (key, value[0], value[1]))

                self.transport.write('ENDMSG\n')

        elif command == 'register':
            global admin
            if user not in admin:
                self.transport.write('%s does not have administrative rights.\n' % user)
                self.transport.write('ENDMSG\n')
            # TODO; check if user is in admin list first
            username = data[1]
            password = data[2]
            role = data[3]
            answer = login_demo.register_user(username, password, role)
            print answer

            created = "user %s has been created" % username
            if answer == created:
                user_path = DIRECTORY + "/%s/OneDir" % username
                if not os.path.exists(user_path):
                    try:
                        os.makedirs(user_path)
                    except OSError, e:
                        print e
            else:
                print "%s already exists" % path
                return False

            self.transport.write('%s\n' % answer)
            self.transport.write('ENDMSG\n')


        #####################################################################3
        elif command == 'change_password':
            global admin
            if user not in admin:
                self.transport.write('%s does not have administrative rights.\n' % user)
                self.transport.write('ENDMSG\n')
            username = data[1]
            password = data[2]
            login_demo.change_password(username, password)
            self.transport.write('ENDMSG\n')

        elif command == 'remove_user':
            global admin
            if user not in admin:
                self.transport.write('%s does not have administrative rights.\n' % user)
                self.transport.write('ENDMSG\n')
            username = data[1]
            login_demo.delete_user(username)
            user_path = DIRECTORY + "/%s" % username
            print user_path
            if os.path.isdir(user_path):
                try:
                    shutil.rmtree(user_path)
                except OSError, e:
                    print e
                except shutil.Error, e:
                    print e
            else:
                print "%s does not exist" % user_path
            self.transport.write('ENDMSG\n')

        elif command == 'login':
            global clients
            global admin
            print "user: ", user
            print "data[1]: ", data[1]
            if user in clients or data[1] in clients:
                self.transport.write('%s is already logged in.\n' % data[1])
                self.transport.write('ENDMSG\n')
            else:
                username = data[1]
                password = data[2]
                answer = login_demo.login(username, password)
                message = answer[0]
                role = ' '
                if message == "Logged In":
                    role = answer[1]
                    display_message(username)
                    display_message(role)
                    clients.append(username)
                    if role == "admin":
                        admin.append(username)
                print message
                print "clients: ", clients
                print "admin: ", admin
                self.transport.write('%s %s\n' % (message, username))
                self.transport.write('ENDMSG\n')

        elif command == 'logout':
            global clients
            global admin
            clients.remove(user)
            if user in admin:
                admin.remove(user)

            print "clients: ", clients
            print "admin: ", admin

            self.transport.write('%s logged out of system\n' % user)
            self.transport.write('ENDMSG\n')

        elif command == 'quit':
            self.transport.loseConnection()

    def rawDataReceived(self, data):
        filename = self.file_data[0]
        file_path = os.path.join(self.factory.files_path, filename)

        display_message('Receiving file chunk (%d KB)' % (len(data)))

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
                self.transport.write('File was successfully transferred and saved\n')
                # self.transport.write('ENDMSG\n')

                display_message('File %s has been successfully transfered' % (filename))
            else:
                os.unlink(file_path)  ###################################################
                self.transport.write('File was successfully transfered but not saved, due to invalid MD5 hash\n')
                self.transport.write('ENDMSG\n')

                display_message(
                    'File %s has been successfully transfered, but deleted due to invalid MD5 hash' % (filename))
        else:
            self.file_handler.write(data)

    def _send_list_of_files(self):
        files = self._get_file_list()
        self.factory.files = files

        self.transport.write('Files (%d): \n\n' % len(files))
        for key, value in files.iteritems():
            self.transport.write('- %s (%d.2 KB)\n' % (key, (value[1] / 1024.0)))

        self.transport.write('ENDMSG\n')

    def _get_file_list(self):
        """ Returns a list of the files in the specified directory as a dictionary:

        dict['file name'] = (file path, file size, file md5 hash)
        """

        file_list = {}
        for filename in os.listdir(self.factory.files_path):
            file_path = os.path.join(self.factory.files_path, filename)

            if os.path.isdir(file_path):
                continue

            file_size = os.path.getsize(file_path)
            md5_hash = get_file_md5_hash(file_path)

            file_list[filename] = (file_path, file_size, md5_hash)

        return file_list

    def _cleanAndSplitInput(self, input):
        input = input.strip()
        input = input.split(' ')

        return input


class FileTransferServerFactory(protocol.ServerFactory):
    protocol = FileTransferProtocol

    def __init__(self, files_path):
        self.files_path = files_path
        self.clients = []
        self.files = None


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', action='store', type='int', dest='port', default=PORT,
                      help='server listening port')
    parser.add_option('--path', action='store', type='string', dest='path', default=DIRECTORY,
                      help='directory where the incoming files are saved')
    (options, args) = parser.parse_args()

    display_message('Listening on port %d, serving files from directory: %s' % (options.port, options.path))

    reactor.listenTCP(options.port, FileTransferServerFactory(DIRECTORY))
    reactor.run()
