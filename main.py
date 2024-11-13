import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown

import easyocr
import re

class FileChooserPopup(Popup):
    def __init__(self, select_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Choose a picture'
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = False

        self.layout = BoxLayout(orientation='vertical')
        self.filechooser = FileChooserListView()
        self.layout.add_widget(self.filechooser)

        self.buttons = BoxLayout(size_hint_y=0.1)
        self.select_button = Button(text='Select')
        self.cancel_button = Button(text='Cancel')

        self.select_button.bind(on_press=lambda *args: select_callback(self, self.filechooser.path, self.filechooser.selection))
        self.cancel_button.bind(on_press=self.dismiss)

        self.buttons.add_widget(self.select_button)
        self.buttons.add_widget(self.cancel_button)
        self.layout.add_widget(self.buttons)

        self.add_widget(self.layout)

class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)
        self.capture = None
        self.image = Image()
        self.add_widget(self.image)

        self.capture_button = Button(text="Capture", size_hint=(1, 0.1), pos_hint={'center_x': 0.5, 'y': 0})
        self.capture_button.bind(on_press=self.capture_photo)
        self.add_widget(self.capture_button)

    def on_enter(self, *args):
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0 / 30.0)

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.image.texture = texture

    def capture_photo(self, *args):
        ret, frame = self.capture.read()
        if ret:
            cv2.imwrite("photo.png", frame)
            self.manager.current = 'review'

    def on_leave(self, *args):
        Clock.unschedule(self.update)
        if self.capture:
            self.capture.release()
            self.capture = None

class ReviewScreen(Screen):
    def __init__(self, **kwargs):
        super(ReviewScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.image = Image(source='photo.png')
        self.layout.add_widget(self.image)

        self.label = Label(text="Is this photo okay?")
        self.layout.add_widget(self.label)

        self.button_layout = BoxLayout(size_hint=(1, 0.2))

        self.yes_button = Button(text="Yes")
        self.yes_button.bind(on_press=self.approve)
        self.button_layout.add_widget(self.yes_button)

        self.no_button = Button(text="No")
        self.no_button.bind(on_press=self.retake)
        self.button_layout.add_widget(self.no_button)

        self.layout.add_widget(self.button_layout)
        self.add_widget(self.layout)

    def on_enter(self, *args):
        global selected_image_path
        self.image.source = selected_image_path if selected_image_path else 'photo.png'
        self.image.reload()

    def approve(self, *args):
        self.manager.current = 'display'

    def retake(self, *args):
        self.manager.current = 'camera'

class DisplayScreen(Screen):
    def __init__(self, **kwargs):
        super(DisplayScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.image = Image(source='photo.png')
        self.layout.add_widget(self.image)

        self.layout_button = BoxLayout(orientation='horizontal')
        self.scan_button = Button(text="Scan for dates", size_hint=(0.5, 0.2))
        self.scan_button.bind(on_press=self.scan_for_dates)
        self.layout_button.add_widget(self.scan_button)

        self.enter_button = Button(text="Enter Manual", size_hint=(0.5, 0.2))
        self.enter_button.bind(on_press=self.enter_dates)
        self.layout_button.add_widget(self.enter_button)

        self.layout.add_widget(self.layout_button)
        self.back_button = Button(text="Back to Main", size_hint=(1, 0.2))
        self.back_button.bind(on_press=self.go_back_to_main)
        self.layout.add_widget(self.back_button)

        self.add_widget(self.layout)

    def on_enter(self, *args):
        global selected_image_path
        self.image.source = selected_image_path if selected_image_path else 'photo.png'
        self.image.reload()

    def go_back_to_main(self, *args):
        self.manager.current = 'main'

    def scan_for_dates(self, *args):
        self.dates_label = Label(text="")
        self.layout.add_widget(self.dates_label)
        image_path = 'photo.png'
        reader = easyocr.Reader(['en'])
        result = reader.readtext(image_path)

        pattern1 = r"\d{2}[/-]\d{2}[/-]\d{4}"  # Regular expression pattern for date dd/mm/yyyy or dd-mm-yyyy

        found_dates = []

        for text in result:
            text_req = text[1]
            date_matches = re.findall(pattern1, text_req)
            found_dates.extend(date_matches)

        if not found_dates:
            self.dates_label.text = "No dates found."
        else:
            self.dates_label.text = "Found dates:\n" + "\n".join(found_dates)

    def enter_dates(self, *args):
        pass

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        btn1 = Button(text="Insurance Papers", size_hint=(1, 0.1))
        btn2 = Button(text="Driver License", size_hint=(1, 0.1))
        btn3 = Button(text="Others", size_hint=(1, 0.1))

        btn1.bind(on_release=self.show_image_options)
        btn2.bind(on_release=self.show_image_options)
        btn3.bind(on_release=self.show_image_options)

        self.layout.add_widget(btn1)
        self.layout.add_widget(btn2)
        self.layout.add_widget(btn3)

        self.add_widget(self.layout)

    def show_image_options(self, button):
        dropdown = DropDown()

        take_photo_btn = Button(text='Take a Photo', size_hint_y=None, height=40)
        take_photo_btn.bind(on_release=lambda btn: self.open_camera(dropdown))
        dropdown.add_widget(take_photo_btn)

        choose_image_btn = Button(text='Choose from Gallery', size_hint_y=None, height=40)
        choose_image_btn.bind(on_release=lambda btn: self.show_file_chooser(dropdown, btn))
        dropdown.add_widget(choose_image_btn)

        dropdown.open(button)

    def show_file_chooser(self, dropdown, instance):
        dropdown.dismiss()
        content = FileChooserPopup(select_callback=self.select)
        content.open()

    def select(self, popup, path, selection):
        global selected_image_path
        if selection:
            selected_image_path = selection[0]
            popup.dismiss()
            self.manager.current = 'review'

    def open_camera(self, dropdown, *args):
        dropdown.dismiss()
        self.manager.current = 'camera'

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ReviewScreen(name='review'))
        sm.add_widget(DisplayScreen(name='display'))
        return sm

if __name__ == '__main__':
    selected_image_path = None
    MyApp().run()
