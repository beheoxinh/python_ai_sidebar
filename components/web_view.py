# File: web_view.py
import os
from urllib.parse import urlparse

from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile,
                                   QWebEngineSettings, QWebEngineUrlRequestInterceptor)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMainWindow

from utils import AppPaths

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

        self.setWindowTitle("Loading...")
        self.setMinimumSize(800, 650)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Get screen size and calculate window size (70%)
        screen = QGuiApplication.primaryScreen().geometry()
        window_width = int(screen.width() * 0.75)
        window_height = int(screen.height() * 0.75)

        # Calculate center position
        center_x = screen.x() + (screen.width() - window_width) // 2
        center_y = screen.y() + (screen.height() - window_height) // 2

        # Set window geometry
        self.setGeometry(center_x, center_y, window_width, window_height)

        # Connect authFinished signal to close the popup
        self.page.authFinished.connect(self.close)

        # Connect titleChanged signal to update window title
        self.page.titleChanged.connect(self.setWindowTitle)

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
        self.setup_scripts()

        # Override các actions mặc định để vô hiệu hóa chúng
        self.action(QWebEnginePage.WebAction.Back).setVisible(False)
        self.action(QWebEnginePage.WebAction.Forward).setVisible(False)
        self.action(QWebEnginePage.WebAction.Reload).setVisible(False)
        self.action(QWebEnginePage.WebAction.ViewSource).setVisible(False)
        self.action(QWebEnginePage.WebAction.SavePage).setVisible(False)
        self.action(QWebEnginePage.WebAction.SelectAll).setVisible(False)
        self.action(QWebEnginePage.WebAction.PasteAndMatchStyle).setVisible(False)
        self.action(QWebEnginePage.WebAction.InspectElement).setVisible(False)
        self.action(QWebEnginePage.WebAction.ExitFullScreen).setVisible(False)
        self.action(QWebEnginePage.WebAction.DownloadLinkToDisk).setVisible(False)
        self.action(QWebEnginePage.WebAction.DownloadImageToDisk).setVisible(False)
        self.action(QWebEnginePage.WebAction.DownloadMediaToDisk).setVisible(False)
        self.action(QWebEnginePage.WebAction.OpenLinkInNewWindow).setVisible(False)
        self.action(QWebEnginePage.WebAction.OpenLinkInNewBackgroundTab).setVisible(False)

    def setup_scripts(self):
        # 1. First inject the message queue handler
        init_script = """
        window.__messageQueue = [];
        window.__messageHandlers = new Set();
        window.MessagePortSafe = {};
        """
        self.runJavaScript(init_script)

        # 2. Inject universal message handling system
        universal_messaging = """
        (function() {
            // Universal Message Handler
            const UniversalMessenger = {
                originalPostMessage: window.postMessage,
                originalAddEventListener: window.addEventListener,
                messageCounter: 0,
                portCounter: 0,

                init() {
                    // Override postMessage globally
                    window.postMessage = (...args) => this.safePostMessage(...args);

                    // Override addEventListener for message events
                    window.addEventListener = (...args) => this.safeAddEventListener(...args);

                    // Override MessagePort
                    if (window.MessagePort) {
                        this.wrapMessagePort();
                    }

                    // Override MessageChannel
                    if (window.MessageChannel) {
                        this.wrapMessageChannel();
                    }

                    // Override BroadcastChannel
                    if (window.BroadcastChannel) {
                        this.wrapBroadcastChannel();
                    }

                    // Add global error handlers
                    this.setupErrorHandling();
                },

                safePostMessage(message, targetOrigin, transfer) {
                    try {
                        // Always use * for targetOrigin to allow cross-origin
                        return this.originalPostMessage.call(
                            window,
                            this.sanitizeMessage(message),
                            '*',
                            transfer
                        );
                    } catch (error) {
                        console.log('PostMessage handled:', error);
                        return this.originalPostMessage.call(
                            window,
                            this.createFallbackMessage(message),
                            '*',
                            transfer
                        );
                    }
                },

                sanitizeMessage(message) {
                    try {
                        // Try to create a clean copy of the message
                        return JSON.parse(JSON.stringify({
                            id: `msg_${Date.now()}_${this.messageCounter++}`,
                            data: message,
                            timestamp: Date.now()
                        }));
                    } catch (error) {
                        return this.createFallbackMessage(message);
                    }
                },

                createFallbackMessage(message) {
                    return {
                        id: `msg_${Date.now()}_${this.messageCounter++}`,
                        data: String(message),
                        timestamp: Date.now(),
                        isStringified: true
                    };
                },

                safeAddEventListener(type, listener, options) {
                    if (type === 'message') {
                        const safeListener = (event) => {
                            try {
                                // Create a safe event object
                                const safeEvent = new MessageEvent('message', {
                                    data: event.data?.data || event.data,
                                    origin: '*',
                                    source: event.source || window,
                                    ports: Array.isArray(event.ports) ? event.ports : []
                                });
                                return listener(safeEvent);
                            } catch (error) {
                                console.log('Message listener handled:', error);
                            }
                        };
                        return this.originalAddEventListener.call(window, type, safeListener, options);
                    }
                    return this.originalAddEventListener.call(window, type, listener, options);
                },

                wrapMessagePort() {
                    const OriginalMessagePort = window.MessagePort;
                    const self = this;

                    class SafeMessagePort extends OriginalMessagePort {
                        constructor() {
                            super();
                            this.id = `port_${Date.now()}_${self.portCounter++}`;
                        }

                        postMessage(message, transfer) {
                            try {
                                super.postMessage(self.sanitizeMessage(message), transfer);
                            } catch (error) {
                                console.log('Port message handled:', error);
                                super.postMessage(self.createFallbackMessage(message), transfer);
                            }
                        }

                        addEventListener(type, listener, options) {
                            if (type === 'message') {
                                const safeListener = (event) => {
                                    try {
                                        const safeEvent = new MessageEvent('message', {
                                            data: event.data?.data || event.data,
                                            origin: '*',
                                            source: null,
                                            ports: []
                                        });
                                        listener(safeEvent);
                                    } catch (error) {
                                        console.log('Port listener handled:', error);
                                    }
                                };
                                super.addEventListener(type, safeListener, options);
                            } else {
                                super.addEventListener(type, listener, options);
                            }
                        }
                    }

                    window.MessagePort = SafeMessagePort;
                },

                wrapMessageChannel() {
                    const OriginalMessageChannel = window.MessageChannel;
                    const self = this;

                    class SafeMessageChannel extends OriginalMessageChannel {
                        constructor() {
                            super();
                            this.id = `channel_${Date.now()}_${self.portCounter++}`;
                            // Wrap both ports
                            this.port1 = new window.MessagePort();
                            this.port2 = new window.MessagePort();
                        }
                    }

                    window.MessageChannel = SafeMessageChannel;
                },

                wrapBroadcastChannel() {
                    const OriginalBroadcastChannel = window.BroadcastChannel;
                    const self = this;

                    class SafeBroadcastChannel extends OriginalBroadcastChannel {
                        constructor(channel) {
                            super(channel);
                            this.id = `broadcast_${Date.now()}_${self.portCounter++}`;
                        }

                        postMessage(message) {
                            try {
                                super.postMessage(self.sanitizeMessage(message));
                            } catch (error) {
                                console.log('Broadcast message handled:', error);
                                super.postMessage(self.createFallbackMessage(message));
                            }
                        }

                        addEventListener(type, listener, options) {
                            if (type === 'message') {
                                const safeListener = (event) => {
                                    try {
                                        const safeEvent = new MessageEvent('message', {
                                            data: event.data?.data || event.data,
                                            origin: '*',
                                            source: null,
                                            ports: []
                                        });
                                        listener(safeEvent);
                                    } catch (error) {
                                        console.log('Broadcast listener handled:', error);
                                    }
                                };
                                super.addEventListener(type, safeListener, options);
                            } else {
                                super.addEventListener(type, listener, options);
                            }
                        }
                    }

                    window.BroadcastChannel = SafeBroadcastChannel;
                },

                setupErrorHandling() {
                    window.addEventListener('error', (event) => {
                        if (event.message?.includes('postMessage')) {
                            event.preventDefault();
                            console.log('Prevented postMessage error:', event.message);
                        }
                    });

                    window.addEventListener('unhandledrejection', (event) => {
                        if (event.reason?.message?.includes('postMessage')) {
                            event.preventDefault();
                            console.log('Prevented unhandled postMessage rejection:', event.reason);
                        }
                    });
                }
            };

            // Initialize the universal messenger
            UniversalMessenger.init();

            // Export for debugging
            window.__UniversalMessenger = UniversalMessenger;

            console.log('Universal messaging system initialized');
        })();
        """
        self.runJavaScript(universal_messaging)

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

        # Create and configure profile with enhanced settings
        self.profile = QWebEngineProfile("secure_browser_profile", self)
        self.setup_profile()

        # Create and configure custom page
        self.custom_page = CustomWebEnginePage(self.profile, self)
        self.setPage(self.custom_page)

        # Connect signals
        self.custom_page.popupCreated.connect(self.handle_popup_created)
        self.custom_page.authCallback.connect(self.handle_auth_callback)
        self.page().loadFinished.connect(self.on_load_finished)

        self.setup_settings()
        self.setup_cookie_store()

        self.setMouseTracking(True)
        self.loaded = False

        # Style cho context menu
        self.menu_style = """
            QMenu {
                position: relative;
                background-color: #2C2C29;
                border: 1px solid transparent;
                border-radius: 5%;
                padding: 0;
                margin: 0;
            }

            QMenu::item {
                position: relative;
                padding: 6px 25px 6px 15px;
                color: #c0c0c0;
                font-size: 13px;
                font-weight: 600;
                font-family: Segoe UI,Segoe UI Emoji,Segoe UI Symbol;
                background-color: transparent;
                transition: background-color 0.5s, color 0.5s;
            }

            QMenu::item:selected {
                cursor: pointer;
                background-color: #333333;
                font-weight: 800;
                padding-left: 18px;
                transition: , padding 0.5s;
            }

            QMenu::separator {
                height: 1px;
                background-color: #4D4D4D;
                margin: 4px 0;
            }

            QMenu::item:disabled {
                cursor: not-allowed;
                color: #6d6d6d;
            }
        """
        # Áp dụng style
        self.setStyleSheet(self.menu_style)

    def setup_profile(self):
        """Enhanced profile setup with additional browser features"""
        paths = AppPaths(app_name="SmartAI", app_author="Hsx2Coder")
        cache_path = os.path.abspath(paths.get_appdata_dir("cache"))
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        self.profile.setCachePath(cache_path)
        self.profile.setPersistentStoragePath(cache_path)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        # Enhanced profile settings
        self.profile.setSpellCheckEnabled(True)
        self.profile.setSpellCheckLanguages(['en-US'])

        # Set default settings
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)

        # Add secure request interceptor
        self.profile.setUrlRequestInterceptor(EnhancedBrowserInterceptor())

    def setup_settings(self):
        """Enhanced settings setup with additional browser features"""
        settings = self.settings()

        # Basic features
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

        # Window features
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, True)

        # Content features
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        # Media features
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)

        # Security settings
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.XSSAuditingEnabled, True)

        # Storage settings
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setDefaultTextEncoding('UTF-8')

    def setup_cookie_store(self):
        cookie_store = self.profile.cookieStore()

        def on_cookie_added(cookie):
            cookie_name = cookie.name().data().decode()
            domain = cookie.domain()
            print(f"Cookie added: {cookie_name} for domain: {domain}")

        def on_cookie_removed(cookie):
            cookie_name = cookie.name().data().decode()
            print(f"Cookie removed: {cookie_name}")

        # Connect signals
        cookie_store.cookieAdded.connect(on_cookie_added)
        cookie_store.cookieRemoved.connect(on_cookie_removed)

        # Ensure cookies are not added/removed repeatedly
        self.cookie_set = set()

        def handle_cookie_added(cookie):
            cookie_name = cookie.name().data().decode()
            if cookie_name not in self.cookie_set:
                self.cookie_set.add(cookie_name)
                on_cookie_added(cookie)

        def handle_cookie_removed(cookie):
            cookie_name = cookie.name().data().decode()
            if cookie_name in self.cookie_set:
                self.cookie_set.remove(cookie_name)
                on_cookie_removed(cookie)

        cookie_store.cookieAdded.connect(handle_cookie_added)
        cookie_store.cookieRemoved.connect(handle_cookie_removed)

    def on_load_finished(self, ok):
        """Handle page load completion"""
        if ok:
            self.inject_enhanced_scripts()
            self.hide_scrollbar()
        else:
            print("Page load failed")

    def inject_enhanced_scripts(self):
        """Inject enhanced browser features via JavaScript"""
        enhanced_scripts = """
        (function() {
            // Enhanced browser features
            window.__browserFeatures = {
                cookiesEnabled: true,
                localStorage: true,
                sessionStorage: true,
                webGL: true,
                indexedDB: true
            };

            // Enhanced messaging system
            window.__messagingSystem = {
                // Override postMessage with enhanced error handling
                init: function() {
                    const originalPostMessage = window.postMessage;
                    window.postMessage = function(message, targetOrigin, transfer) {
                        try {
                            // Always use * for targetOrigin
                            return originalPostMessage.call(
                                this,
                                message,
                                '*',
                                transfer
                            );
                        } catch (e) {
                            console.log('Enhanced postMessage handled:', e);
                            // Try alternative approach
                            try {
                                return originalPostMessage.call(
                                    this,
                                    JSON.parse(JSON.stringify(message)),
                                    '*',
                                    transfer
                                );
                            } catch (e2) {
                                console.log('Alternative approach failed:', e2);
                                // Final fallback
                                return originalPostMessage.call(
                                    this,
                                    String(message),
                                    '*',
                                    transfer
                                );
                            }
                        }
                    };
                }
            };

            // Initialize enhanced features
            window.__messagingSystem.init();

            // Add enhanced error tracking
            window.addEventListener('error', function(e) {
                console.log('Enhanced error tracking:', {
                    message: e.message,
                    filename: e.filename,
                    line: e.lineno,
                    col: e.colno,
                    error: e.error
                });
            });

            window.addEventListener('unhandledrejection', function(e) {
                console.log('Unhandled promise rejection:', e.reason);
            });

            console.log('Enhanced browser features initialized');
        })();
        """
        self.page().runJavaScript(enhanced_scripts)

    def hide_scrollbar(self):
        self.page().runJavaScript("""
            const style = document.createElement('style');
            style.innerHTML = `
                ::-webkit-scrollbar {
                    display: none;
                }
                body {
                    overflow: hidden;
                }
            `;
            document.head.appendChild(style);
            document.body.addEventListener('wheel', function(event) {
                window.scrollBy(0, event.deltaY);
            });
        """)

    def save_last_url(self, url):
        try:
            with open("lasturl", "w") as file:
                file.write(url)
            print(f"URL saved to lasturl: {url}")
        except Exception as e:
            print(f"Error saving URL to lasturl: {e}")

    def load_last_url(self):
        try:
            if os.path.exists("lasturl"):
                with open("lasturl", "r") as file:
                    url = file.read().strip()
                print(f"URL loaded from lasturl: {url}")
                return url
        except Exception as e:
            print(f"Error loading URL from lasturl: {e}")
        return "https://claude.ai/"

    def handle_auth_callback(self, callback_url):
        print(f"WebView: Auth callback received: {callback_url}")
        self.authCompleted.emit(callback_url)

    def handle_popup_created(self, popup):
        print("CustomWebView: New popup created")
        self.popupCreated.emit(popup)

    def createWindow(self, window_type):
        return self.page().createWindow(window_type)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.loaded:
            print("Loading initial URL...")
            last_url = self.load_last_url()
            self.setUrl(QUrl(last_url))
            self.loaded = True

    def enterEvent(self, event):
        self.setFocus()
        super().enterEvent(event)


class EnhancedBrowserInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        """Enhanced request interceptor with full browser headers"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"'
        }

        for name, value in headers.items():
            info.setHttpHeader(name.encode(), value.encode())
