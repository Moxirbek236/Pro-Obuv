from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
import webbrowser

# Dashboard URL (update this to your real domain)
DASHBOARD_URL = 'https://safety.uz/super-admin/dashboard'

class AdminLauncher(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Logo or Header
        layout.add_widget(Label(
            text="Pro Obuv Admin", 
            font_size='30sp', 
            size_hint=(1, 0.2),
            color=(0.94, 0.84, 0, 1) # Yellow accent
        ))
        
        layout.add_widget(Label(
            text="Bu ilova Super Admin paneliga\navtomatik kirishni ta'minlaydi.",
            halign='center'
        ))

        # Main Action Button
        btn = Button(
            text="DASHBOARDNI OCHISH",
            size_hint=(1, 0.2),
            background_color=(0, 0.5, 1, 1),
            color=(1, 1, 1, 1)
        )
        btn.bind(on_press=self.open_dashboard)
        layout.add_widget(btn)
        
        # Footer
        layout.add_widget(Label(text="Powered by Safety.uz Framework", font_size='12sp', size_hint=(1, 0.1)))
        
        return layout

    def open_dashboard(self, instance):
        # Opens the default system browser (Chrome/Safari)
        # This is the most reliable way to maintain your CSS/JS functionality
        webbrowser.open(DASHBOARD_URL)

if __name__ == '__main__':
    AdminLauncher().run()
