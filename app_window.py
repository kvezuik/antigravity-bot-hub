"""
Antigravity 2.0 - Native Desktop Application Window
Provides a genuine native desktop application window with Wayland/X11 and Windows support.
Uses PyQt6 WebEngine with clean native window chrome, dark obsidian palette, and native OS shortcuts.
"""

import sys
import os
import webbrowser
from typing import Optional, Callable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PNG = os.path.join(BASE_DIR, "agybots.png")
if not os.path.exists(ICON_PNG):
    ICON_PNG = os.path.join(BASE_DIR, "web", "icon.png")


def run_native_desktop_app(url: str, on_close: Optional[Callable[[], None]] = None) -> bool:
    """
    Launch native desktop application window.
    Returns True if successfully launched via a native GUI toolkit, False otherwise.
    """
    # Prefer PyQt6 for a 100% native desktop application experience
    try:
        return _run_pyqt6_app(url, on_close)
    except Exception as e:
        print(f"[Native App] PyQt6 launch failed: {e}. Trying fallback...")

    # Secondary fallback: pywebview
    try:
        return _run_pywebview_app(url, on_close)
    except Exception as e:
        print(f"[Native App] pywebview launch failed: {e}")

    return False


def _run_pyqt6_app(url: str, on_close: Optional[Callable[[], None]] = None) -> bool:
    # Ensure user-installed site-packages are loaded
    user_site = os.path.expanduser("~/.local/lib/python3.14/site-packages")
    if os.path.exists(user_site) and user_site not in sys.path:
        sys.path.insert(0, user_site)

    # Prefer Wayland on Wayland compositors (Hyprland, Sway, GNOME Wayland)
    if os.environ.get("WAYLAND_DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "wayland;xcb")

    from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineSettings,
        QWebEngineProfile
    )
    from PyQt6.QtGui import QIcon, QColor, QAction, QKeySequence, QShortcut
    from PyQt6.QtCore import QUrl, Qt, QSize

    class AntigravityWebPage(QWebEnginePage):
        def acceptNavigationRequest(self, qurl: QUrl, nav_type, is_main_frame: bool) -> bool:
            url_str = qurl.toString()
            # Allow local app navigation
            if url_str.startswith("http://127.0.0.1") or url_str.startswith("http://localhost") or url_str.startswith("file://") or url_str == "about:blank":
                return True
            # Open external links (e.g. Google OAuth, subscriptions, docs) in default browser
            webbrowser.open(url_str)
            return False

    class AntigravityNativeWindow(QMainWindow):
        def __init__(self, target_url: str):
            super().__init__()
            self.target_url = target_url
            self.on_close_callback = on_close

            self.setWindowTitle("Antigravity 2.0 • Desktop Studio")
            self.resize(1280, 840)
            self.setMinimumSize(880, 580)

            # Native Icon
            if os.path.exists(ICON_PNG):
                self.setWindowIcon(QIcon(ICON_PNG))

            # Deep dark background to eliminate white flashing
            self.setStyleSheet("background-color: #08090d;")

            # Initialize WebEngine View with custom page
            self.view = QWebEngineView(self)
            self.page = AntigravityWebPage(self.view)
            self.page.setBackgroundColor(QColor("#08090d"))
            self.view.setPage(self.page)
            self.view.setStyleSheet("background-color: #08090d;")

            # Configure Engine Settings
            settings = self.view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

            # Clean context menu (replaces generic browser context menu)
            self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)

            # Central widget
            self.setCentralWidget(self.view)

            # Keyboard Shortcuts
            self._setup_shortcuts()

            # Load application URL
            self.view.setUrl(QUrl(self.target_url))

            # Center window on screen
            self._center_on_screen()

        def _setup_shortcuts(self):
            # Fullscreen (F11)
            f11_shortcut = QShortcut(QKeySequence("F11"), self)
            f11_shortcut.activated.connect(self._toggle_fullscreen)

            # Exit Fullscreen (Escape)
            esc_shortcut = QShortcut(QKeySequence("Escape"), self)
            esc_shortcut.activated.connect(self._exit_fullscreen)

            # Reload (Ctrl+R / F5)
            r_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
            r_shortcut.activated.connect(self.view.reload)
            f5_shortcut = QShortcut(QKeySequence("F5"), self)
            f5_shortcut.activated.connect(self.view.reload)

            # Zoom In (Ctrl++ / Ctrl+=)
            zoom_in_1 = QShortcut(QKeySequence("Ctrl++"), self)
            zoom_in_1.activated.connect(lambda: self.view.setZoomFactor(min(2.0, self.view.zoomFactor() + 0.1)))
            zoom_in_2 = QShortcut(QKeySequence("Ctrl+="), self)
            zoom_in_2.activated.connect(lambda: self.view.setZoomFactor(min(2.0, self.view.zoomFactor() + 0.1)))

            # Zoom Out (Ctrl+-)
            zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
            zoom_out.activated.connect(lambda: self.view.setZoomFactor(max(0.5, self.view.zoomFactor() - 0.1)))

            # Zoom Reset (Ctrl+0)
            zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
            zoom_reset.activated.connect(lambda: self.view.setZoomFactor(1.0))

        def _toggle_fullscreen(self):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

        def _exit_fullscreen(self):
            if self.isFullScreen():
                self.showNormal()

        def _center_on_screen(self):
            screen = QApplication.primaryScreen()
            if screen:
                screen_geom = screen.availableGeometry()
                x = (screen_geom.width() - self.width()) // 2
                y = (screen_geom.height() - self.height()) // 2
                self.move(max(0, x), max(0, y))

        def _show_context_menu(self, pos):
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #131620;
                    color: #f8fafc;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 8px;
                    padding: 6px;
                }
                QMenu::item {
                    padding: 6px 20px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QMenu::item:selected {
                    background-color: #2563eb;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background: rgba(255, 255, 255, 0.08);
                    margin: 4px 0;
                }
            """)

            act_reload = menu.addAction("⟳ Обновить интерфейс")
            act_reload.triggered.connect(self.view.reload)

            menu.addSeparator()

            act_fs = menu.addAction("⛶ Полный экран (F11)")
            act_fs.triggered.connect(self._toggle_fullscreen)

            menu.exec(self.view.mapToGlobal(pos))

        def closeEvent(self, event):
            if self.on_close_callback:
                try:
                    self.on_close_callback()
                except Exception:
                    pass
            event.accept()

    # Initialize QApplication
    existing_app = QApplication.instance()
    app = existing_app or QApplication(sys.argv)
    app.setApplicationName("Antigravity 2.0")
    app.setApplicationDisplayName("Antigravity 2.0 • Desktop Studio")
    app.setDesktopFileName("agybots")

    if os.path.exists(ICON_PNG):
        app.setWindowIcon(QIcon(ICON_PNG))

    window = AntigravityNativeWindow(url)
    window.show()

    print("🚀 [Native App] Запущено нативное десктопное окно Antigravity 2.0 (PyQt6)")
    app.exec()
    return True


def _run_pywebview_app(url: str, on_close: Optional[Callable[[], None]] = None) -> bool:
    import webview

    def on_closed():
        if on_close:
            try:
                on_close()
            except Exception:
                pass

    window = webview.create_window(
        title="Antigravity 2.0 • Desktop Studio",
        url=url,
        width=1280,
        height=840,
        min_size=(880, 580),
        background_color="#08090d"
    )
    window.events.closed += on_closed
    print("🚀 [Native App] Запущено нативное окно Antigravity 2.0 (pywebview)")
    webview.start(gui="qt" if "PyQt6" in sys.modules else None)
    return True
