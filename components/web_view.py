# File: web_view.py
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile,
                                   QWebEngineSettings, QWebEngineCookieStore,
                                   QWebEngineUrlRequestInterceptor)
from PyQt6.QtCore import QUrl, Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtNetwork import QNetworkCookie
import os
import sys
import time
from urllib.parse import urlparse, parse_qs, urlencode

class SecureBrowserInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        # Add secure headers
        info.setHttpHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        info.setHttpHeader(b"Accept", b"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
        info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.5")
        info.setHttpHeader(b"DNT", b"1")
        info.setHttpHeader(b"Upgrade-Insecure-Requests", b"1")

class PopupWindow(QMainWindow):
    popupClosed = pyqtSignal()

    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.parent = parent

        self.web_view = QWebEngineView(self)
        self.page = CustomWebEnginePage(profile, self)
        self.web_view.setPage(self.page)
        self.setCentralWidget(self.web_view)

        self.setMinimumSize(800, 600)
        self.setWindowTitle("Authentication")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Get screen size and calculate window size (70%)
        screen = QGuiApplication.primaryScreen().geometry()
        window_width = int(screen.width() * 0.7)
        window_height = int(screen.height() * 0.7)

        # Calculate center position
        center_x = screen.x() + (screen.width() - window_width) // 2
        center_y = screen.y() + (screen.height() - window_height) // 2

        # Set window geometry
        self.setGeometry(center_x, center_y, window_width, window_height)

        # Connect authFinished signal to close the popup
        self.page.authFinished.connect(self.close)

    def closeEvent(self, event):
        print("PopupWindow: Closing")
        if self.parent:
            self.parent.popupClosed.emit()
        self.popupClosed.emit()
        event.accept()

class CustomWebEnginePage(QWebEnginePage):
    popupCreated = pyqtSignal(object)
    authCallback = pyqtSignal(str)
    authFinished = pyqtSignal(str)

    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self._profile = profile
        self.parent = parent
        self.auth_in_progress = False
        self.current_url = None

        self.auth_domains = [
            'accounts.google.com',
            'login.microsoftonline.com',
            'github.com',
            'login.auth0.com',
            'www.facebook.com',
            'facebook.com',
            'www.google.com'
        ]

    def javaScriptConsoleMessage(self, level, message, line, sourceid):
        print(f"JS [{level}] {message} (line {line})")

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        url_str = url.toString()
        parsed_url = urlparse(url_str)

        if "claude.ai" in parsed_url.netloc:
            if self.auth_in_progress:
                print("Auth completed, returning to app")
                self.auth_in_progress = False
                self.authFinished.emit(url_str)  # Emit authFinished signal
                return True
        return True

    def reloadWithAuth(self):
        """Reload page after auth completion"""
        if self.current_url:
            print(f"Reloading after auth: {self.current_url}")
            self.setUrl(QUrl(self.current_url))
            self.current_url = None
            self.auth_in_progress = False

    def createWindow(self, window_type):
        try:
            popup = PopupWindow(self._profile, self.parent)
            popup.show()
            self.popupCreated.emit(popup)
            return popup.page
        except Exception as e:
            print(f"Error creating popup window: {e}")
            return None

class CustomWebView(QWebEngineView):
    popupCreated = pyqtSignal(object)
    popupClosed = pyqtSignal()
    authCompleted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")

        # Create and configure profile
        self.profile = QWebEngineProfile("secure_browser_profile", self)
        self.setup_profile()

        # Create and configure custom page
        self.custom_page = CustomWebEnginePage(self.profile, self)
        self.setPage(self.custom_page)

        # Connect signals
        self.custom_page.popupCreated.connect(self.handle_popup_created)
        self.custom_page.authCallback.connect(self.handle_auth_callback)

        self.setup_settings()
        self.setup_cookie_store()

        self.setMouseTracking(True)
        self.loaded = False

    def handle_auth_callback(self, callback_url):
        print(f"WebView: Auth callback received: {callback_url}")
        self.authCompleted.emit(callback_url)

    def handle_popup_created(self, popup):
        print("CustomWebView: New popup created")
        self.popupCreated.emit(popup)

    def setup_profile(self):
        # Set up cache and storage
        cache_path = os.path.abspath("./secure_cache")
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        self.profile.setCachePath(cache_path)
        self.profile.setPersistentStoragePath(cache_path)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        # Add secure request interceptor
        self.profile.setUrlRequestInterceptor(SecureBrowserInterceptor())

    def setup_settings(self):
        settings = self.settings()

        # Enable required features
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)

        # Security settings
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)

        # Disable unnecessary features
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadIconsForPage, False)

    def setup_cookie_store(self):
        cookie_store = self.profile.cookieStore()

        def on_cookie_added(cookie):
            cookie_name = cookie.name().data().decode()
            domain = cookie.domain()
            print(f"Cookie added: {cookie_name} for domain: {domain}")

        def on_cookie_removed(cookie):
            cookie_name = cookie.name().data().decode()
            print(f"Cookie removed: {cookie_name}")

        cookie_store.cookieAdded.connect(on_cookie_added)
        cookie_store.cookieRemoved.connect(on_cookie_removed)

    def createWindow(self, window_type):
        return self.page().createWindow(window_type)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.loaded:
            print("Loading initial URL...")
            self.setUrl(QUrl("https://claude.ai/"))
            self.loaded = True

    def enterEvent(self, event):
        self.setFocus()
        super().enterEvent(event)