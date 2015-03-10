__author__ = 'ps3an'

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):

    def on_modified(self, event):
        print "Got it!"

    def on_any_event(self, event):
        print("Detect an event!")

    def on_deleted(self, event):
        #we have to actaully delete the file i trash to test this event
        #Deleting a file without deleting it in trash doesn't really delete the file
        print("Something is deleted")

    def on_created(self, event):
        print("Created smt")

#should look into snapshot
    #system should take snapshot of the folder
    #system should compare what has been changed when starting the program

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/home/student/OneDir_test', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()