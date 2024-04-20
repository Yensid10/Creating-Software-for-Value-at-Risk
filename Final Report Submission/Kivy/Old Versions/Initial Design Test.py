from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
class ApplicationView(BoxLayout):
    # Declare ObjectProperty variables for the stock list and user inputs
    stockList = ObjectProperty(None)
    userInputs = ObjectProperty(None)
    def __init__(self, **kwargs):
        # Call the parent class's constructor
        super(ApplicationView, self).__init__(**kwargs)
        # Populate the stock list and user inputs
        self.populateList()
        self.populateInputs()
    def populateList(self):
        # Add 100 labels to the stock list, will be updated to include FTSE 100 stocks
        for i in range(100):
            self.stockList.add_widget(Label(text=f'Stock {i + 1}', size_hint_y=None, height=30, font_size=25))
    def populateInputs(self):
        # Add 20 pairs of labels and text inputs to the user inputs, as an example before I implement proper inputs
        for i in range(20):
            self.userInputs.add_widget(Label(text=f'Input {i + 1}', size_hint_y=None, height=30, font_size=25))
            self.userInputs.add_widget(TextInput(size_hint_y=None, height=30))
class IDTApp(App):
    def build(self):
        return ApplicationView()
if __name__ == '__main__':
    IDTApp().run()