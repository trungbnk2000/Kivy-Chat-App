import sys

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
import socket_client
import os

Window.clearcolor = (1, 1, 1, 1)


class HomePage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.port = 6969
        # self.ip = '192.168.1.5'
        # self.username = 'Trung'

        self.cols = 1
        self.spacing = 10
        self.size_hint = (0.5, 0.7)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        # image
        self.image = Image(source="assets/image.png")
        self.add_widget(self.image)
        # label
        self.greeting = Label(text="Nhập thông tin của bạn", font_size=18, color=(0, 0, 0, 1))
        self.add_widget(self.greeting)
        # input
        self.ip = TextInput(multiline=False, padding_y=(20, 20), size_hint=(1, 0.8), hint_text="Nhập ip...")
        self.add_widget(self.ip)
        # input
        self.username = TextInput(multiline=False, padding_y=(20, 20), size_hint=(1, 0.8), hint_text="Nhập tên...")
        self.add_widget(self.username)
        # input
        self.port = TextInput(multiline=False, padding_y=(20, 20), size_hint=(1, 0.8), hint_text="Nhập port...")
        self.add_widget(self.port)
        # button
        self.button = Button(text="ĐĂNG NHẬP", size_hint=(0.8, 0.5), bold=True, background_color="50C2C9",
                             background_normal="")
        self.button.bind(on_press=self.login)
        self.add_widget(self.button)

    def login(self, instance):
        port = self.port.text
        ip = self.ip.text
        username = self.username.text
        message = f"Joining {ip}:{port} as {username}"
        chat_app.info_page.update_info(message)
        chat_app.screen_manager.current = "info"
        Clock.schedule_once(self.connect, 1)

    def connect(self, _):
        port = int(self.port.text)
        ip = self.ip.text
        username = self.username.text

        if not socket_client.connect(ip, port, username, show_error):
            return

        chat_app.create_chat_page()
        chat_app.screen_manager.current = "chat"


class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.size_hint = (0.5, 0.7)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        self.greeting = Label(text="Trang gửi tin và hình ảnh", font_size=18, color=(0, 0, 0, 1))
        self.add_widget(self.greeting)

    def update_info(self, id):
        self.greeting.text = id


class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.rows = 2

        self.history = ScrollabelLabel(height=Window.size[1] * 0.9, size_hint_y=None)
        self.add_widget(self.history)

        self.new_message = TextInput(width=Window.size[0] * 0.8, size_hint_x=None, multiline=False)
        self.send = Button(text="Gửi")
        self.send.bind(on_press=self.send_message)

        chat_widget = GridLayout(cols=2)
        chat_widget.add_widget(self.new_message)
        chat_widget.add_widget(self.send)
        self.add_widget(chat_widget)

        Window.bind(on_key_down=self.on_key_down)

        Clock.schedule_once(self.focus_text_input, 1)
        socket_client.start_listening(self.incoming_message, show_error)
        self.bind(size=self.adjust_fields)

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40:
            self.send_message(None)

    def send_message(self, _):
        message = self.new_message.text
        self.new_message.text = ""
        if message:
            self.history.update_chat_history(
                f'[color=dd2020]{chat_app.home_page.username.text}:[/color][color=000000]> {message}[/color]')
            socket_client.send(message)

        Clock.schedule_once(self.focus_text_input, 0.1)

    def focus_text_input(self, _):
        self.new_message.focus = True

    def incoming_message(self, username, message):
        self.history.update_chat_history(f'[color=20dd20]{username}[/color] > {message}')

    def adjust_fields(self, *_):
        # Chat history height - 90%, but at least 50px for bottom new message/send button part
        if Window.size[1] * 0.1 < 50:
            new_height = Window.size[1] - 50
        else:
            new_height = Window.size[1] * 0.9
        self.history.height = new_height

        # New message input width - 80%, but at least 160px for send button
        if Window.size[0] * 0.2 < 160:
            new_width = Window.size[0] - 160
        else:
            new_width = Window.size[0] * 0.8
        self.new_message.width = new_width

        # Update chat history layout
        # self.history.update_chat_history_layout()
        Clock.schedule_once(self.history.update_chat_history_layout, 0.01)


class MainApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        self.home_page = HomePage()
        screen = Screen(name="home")
        screen.add_widget(self.home_page)
        self.screen_manager.add_widget(screen)

        self.info_page = InfoPage()
        screen = Screen(name="info")
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def create_chat_page(self):
        self.chat_page = ChatPage()
        screen = Screen(name="chat")
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)


class ScrollabelLabel(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    def update_chat_history(self, message):
        self.chat_history.text += '\n' + message
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)
        # self.scroll_to(self.scroll_to_point)

    def update_chat_history_layout(self, _=None):
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)


def show_error(message):
    chat_app.info_page.update_info(message)
    chat_app.screen_manager.current = "info"
    Clock.schedule_once(sys.exit, 10)


chat_app = MainApp()
chat_app.run()
