#Adjusting window size to be perfect for the tabs and different screens
from kivy.core.window import Window
Window.size = (800, 550)

#Importing the libraries needed
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, SlideTransition

#Importing the classes from other files within the directory
from Screens.Portfolio import Portfolio
from Screens.Graphs import Graphs
from Screens.VaRChecker import VaRChecker

class FDApp(App):
    def build(self):
        sm = ScreenManager()        
        sm.add_widget(Portfolio(name='Portfolio'))
        sm.add_widget(Graphs(name='Graphs'))
        sm.add_widget(VaRChecker(name='VaRChecker'))

        def screenSwitcher(instance):
            currentTabIndex = sm.screen_names.index(sm.current) # Getting the index of the current screen
            selectedTabIndex = sm.screen_names.index(instance.text) # Getting the index of the screen that was clicked

            if selectedTabIndex > currentTabIndex: # If the selected tab is to the right of the current tab, slide left
                sm.transition = SlideTransition(direction='left')
            else: # Otherwise, slide right
                sm.transition = SlideTransition(direction='right')

            sm.current = instance.text # Switch to the selected screen


        tabs = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1}) # Creating the tabs, takes up 10% of the screen space at the top
        for screen in sm.screens:
            tabButton = Button(text=screen.name, size_hint=(0.33, 1)) # There are 3, so they take up the available space
            tabButton.bind(on_release=screenSwitcher)
            tabs.add_widget(tabButton)

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(tabs)
        layout.add_widget(sm)

        return layout

if __name__ == '__main__':
    FDApp().run() # Runs the App
