#All events can be categorized to 3 types:
#1 Create : upload the file
#2 Delete : delete the file
#3 Move : Rename, move, modify will fire off move event. -> server need to delete the old ones and upload the edited file

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

path = '/home/boom/student/OneDir/'

class MyHandler(FileSystemEventHandler):

    def on_deleted(self, event):
        print("Delete :" + (trimPath(event.src_path))[1] )

    def on_created(self, event):
        print("Upload :" + (trimPath(event.src_path))[1] )

    def on_moved(self, event):
        print("Delete :" + (trimPath(event.src_path))[1] )
        print("Upload :" + trimPath(event.dest_path)[1] )


def trimPath(somePath):
    newPath = (somePath + " ").strip()
    newPath = newPath.split(path,1)
    return newPath

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/home/boom/student/OneDir', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
