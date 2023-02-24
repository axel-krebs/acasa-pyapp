#!/usr/bin/env python
"""
Admin GUI for Acasa
"""
from wx import *

def make_login_dialog(root):
    _ld = Dialog(root)
    # Add controls
    return _ld

class AdminGUI(Frame):
    
    def __init__(self, *args, **kw):
        super(AdminGUI, self).__init__(*args, **kw)

        pnl = Panel(self)
        st = StaticText(pnl, label="WELCOME (empty)")
        font = st.GetFont()
        font.PointSize += 10
        font = font.Bold()
        st.SetFont(font)

        sizer = BoxSizer(VERTICAL)
        sizer.Add(st, SizerFlags().Border(TOP|LEFT, 25))

        pnl.SetSizer(sizer)

        # create a login dialog
        self._login_dialog = make_login_dialog(pnl)

        # create a menu bar
        self.make_menu_bar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Status..")
        
    def make_menu_bar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
                "Help string shown in status bar for this menu item")
        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(ID_EXIT)

        # Now a help menu for the about item
        helpMenu = Menu()
        loginItem = helpMenu.Append(-1, "Login")
        aboutItem = helpMenu.Append(ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(EVT_MENU, self.on_hello, helloItem)
        self.Bind(EVT_MENU, self.on_exit,  exitItem)
        self.Bind(EVT_MENU, self.on_about, aboutItem)
        self.Bind(EVT_MENU, self.on_login, loginItem)

    def on_login(self, event):
        self._login_dialog.CenterOnScreen()
        self._login_dialog.ShowModal()

    def on_exit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def on_hello(self, event):
        """Say hello to the user."""
        MessageBox("Hello again from wxPython")

    def on_about(self, event):
        """Display an About Dialog"""
        MessageBox("This is a wxPython Hello World sample",
                      "About Hello World 2",
                      OK|ICON_INFORMATION)
    
def start_admin_app():
    app = App()
    frm = AdminGUI(None, title='Acasa Admin')
    frm.SetSize(x=10, y=10, width=800, height=600, sizeFlags=SIZE_AUTO)
    frm.CentreOnScreen()
    frm.Show()
    app.MainLoop()
    
# Calling GUI directly
if __name__ == '__main__':
    cred = input("Do you have credentials? >")
    if cred == "Ye$":
        start_admin_app()
    else:
        print("Your credentials couldn't be verified..")
        exit()