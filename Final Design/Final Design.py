#Adjusting window size to be perfect for the tabs and different screens
from kivy.core.window import Window
Window.size = (800, 550)

#Importing the libraries needed
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager

#Importing the classes from other files within the directory
from Screens.Portfolio import Portfolio
from Screens.Rankings import Rankings
from Screens.Trends import Trends
from Screens.VaRChecker import VaRChecker

class FDApp(App):
    def build(self):
        sm = ScreenManager()        
        sm.add_widget(Portfolio(name='Portfolio'))
        sm.add_widget(Rankings(name='Rankings'))
        sm.add_widget(Trends(name='Trends'))
        sm.add_widget(VaRChecker(name='VaRChecker'))

        def screenSwitch(instance):
            sm.current = instance.text

        tabs = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1})
        for screen in sm.screens:
            tabButton = Button(text=screen.name, size_hint=(0.33, 1))
            tabButton.bind(on_release=screenSwitch)
            tabs.add_widget(tabButton)

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(tabs)
        layout.add_widget(sm)

        return layout

if __name__ == '__main__':
    FDApp().run()
