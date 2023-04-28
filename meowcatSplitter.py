import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image


def split_image(image_file):
    with Image.open(image_file) as im:
        width, height = im.size
        mid_x = width // 2
        mid_y = height // 2
        top_left = im.crop((0, 0, mid_x, mid_y))
        top_right = im.crop((mid_x, 0, width, mid_y))
        bottom_left = im.crop((0, mid_y, mid_x, height))
        bottom_right = im.crop((mid_x, mid_y, width, height))
        return top_left, top_right, bottom_left, bottom_right

class ImageSplitterHandler(FileSystemEventHandler):
    def process(self, event):
        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path).lower()
        if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif')) and not any(x in file_name for x in ["top_left", "top_right", "bottom_left", "bottom_right"]):
            print(f"New image detected: {event.src_path}")

            # Add a delay to allow the file to be completely written
            time.sleep(2)

            image = Image.open(event.src_path)
            top_left, top_right, bottom_left, bottom_right = split_image(event.src_path)

            file_prefix = os.path.splitext(os.path.basename(event.src_path))[0]
            output_folder = os.path.join(os.path.dirname(event.src_path), "singles")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            top_left.save(os.path.join(output_folder, file_prefix + "_top_left.jpg"))
            top_right.save(os.path.join(output_folder, file_prefix + "_top_right.jpg"))
            bottom_left.save(os.path.join(output_folder, file_prefix + "_bottom_left.jpg"))
            bottom_right.save(os.path.join(output_folder, file_prefix + "_bottom_right.jpg"))

            print(f"Image split and saved in: {output_folder}")  # Move this line inside the if block

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

if __name__ == "__main__":
    path = "C:\meowcat69000"
    event_handler = ImageSplitterHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
