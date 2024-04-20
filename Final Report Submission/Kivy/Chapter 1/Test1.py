import kivy as kv

from kivy.app import App
from kivy.uix.button import Label

class Test2App(App):
    def build(self):
        return Label()
 
if __name__=="__main__":
        Test2App().run()