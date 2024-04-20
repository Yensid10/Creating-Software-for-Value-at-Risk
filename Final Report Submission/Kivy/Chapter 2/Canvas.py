# File name: Canvas.py
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.window import Window

# Set the size of the window
Window.size = (250, 200)

class DrawingSpace(RelativeLayout):
    pass

class CanvasApp(App):
    def build(self):
         return DrawingSpace()
 
if __name__=="__main__":
     CanvasApp().run()