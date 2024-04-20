# File name: Layouts.py
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.pagelayout import PageLayout
from kivy.core.window import Window

# Set the size of the window
# Window.size = (250, 200)

class MyLayout(PageLayout):
    pass

class LayoutsApp(App):
    def build(self):
        return MyLayout()
    
if __name__=="__main__":
    LayoutsApp().run()