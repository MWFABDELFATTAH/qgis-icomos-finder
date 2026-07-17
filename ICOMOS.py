# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QLocale, QTranslator, QCoreApplication, Qt
from qgis.core import QgsSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget
from .ICOMOS_dockwidget import ICOMOSNOTESDockWidget
import os.path
import re

class ICOMOSNOTES:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&ICOMOS FINDER')
        self.toolbar = self.iface.addToolBar(u'ICOMOSNOTES')
        self.toolbar.setObjectName(u'ICOMOSNOTES')
        self.pluginIsActive = False
        self.dockwidget = None

    def tr(self, message):
        return QCoreApplication.translate('ICOMOSNOTES', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if add_to_toolbar: self.toolbar.addAction(action)
        if add_to_menu: self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.add_action(icon_path, text=self.tr(u'ICOMOS FINDER'), callback=self.run, parent=self.iface.mainWindow())

    def onClosePlugin(self):
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.pluginIsActive = False

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&ICOMOS FINDER'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True
            if self.dockwidget == None:
                self.dockwidget = ICOMOSNOTESDockWidget()
            
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockwidget)
            
            # Connect the buttons
            self.dockwidget.btn_search.clicked.connect(self.execute_text_search)
            self.dockwidget.btn_reading_list.clicked.connect(self.generate_reading_list)
            
            self.dockwidget.show()

    def execute_text_search(self):
        keyword = self.dockwidget.search_input.text().strip()
        if not keyword:
            self.dockwidget.text_display.setHtml("Please enter a keyword to search.")
            return

        file_path = os.path.join(os.path.dirname(__file__), "icomos_charters.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.dockwidget.text_display.setHtml(f"Could not load file: {str(e)}")
            return

        # Split the document by '###'
        charter_blocks = content.split('###')
        results_html = []
        search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        for block in charter_blocks:
            if not block.strip(): continue
            if '<span style="color: red;">' not in block: continue
            
            # Split exactly at the red span
            parts = block.split('<span style="color: red;">', 1)
            
            # Everything before the red span is the Title
            header_title = parts[0].strip()
            
            # Everything after the red span is the text (including the span closing tag)
            rest_of_block = parts[1]
            if '</span>' in rest_of_block:
                metadata, para_text = rest_of_block.split('</span>', 1)
            else:
                para_text = rest_of_block
                
            paragraphs = re.split(r'\n\s*\n', para_text.strip())
            
            matching_paras = []
            for para in paragraphs:
                if search_pattern.search(para):
                    # Highlight keyword yellow
                    highlighted = search_pattern.sub(
                        lambda m: f'<span style="background-color: yellow; color: black; font-weight: bold;">{m.group(0)}</span>',
                        para.strip()
                    )
                    matching_paras.append(highlighted)
            
            if matching_paras:
                # Display the extracted Title in bold blue, followed by the paragraphs
                results_html.append(f"<div style='margin-bottom:20px;'><b style='color: blue; font-size: 14px;'>{header_title}</b><br><br>" + "<br><br>".join(matching_paras) + "</div><hr>")

        if results_html:
            self.dockwidget.text_display.setHtml("".join(results_html))
        else:
            self.dockwidget.text_display.setHtml(f"No mentions of '<b>{keyword}</b>' found.")

    def generate_reading_list(self):
        import re
        keyword = self.dockwidget.search_input.text().strip()
        if not keyword:
            self.dockwidget.text_display.setHtml("Please enter a keyword to generate a reading list.")
            return

        file_path = os.path.join(os.path.dirname(__file__), "icomos_charters.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.dockwidget.text_display.setHtml(f"Could not load file: {str(e)}")
            return

        charter_blocks = content.split('###')
        charter_list = []
        search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        for block in charter_blocks:
            if not block.strip(): continue
            if '<span style="color: red;">' not in block: continue
            
            # Check if the keyword exists ANYWHERE in this specific charter block
            if search_pattern.search(block):
                # Split exactly at the red span
                parts = block.split('<span style="color: red;">', 1)
                
                # Everything before the red span is the Title
                header_title = parts[0].strip()
                clean_title = re.sub('<[^<]+?>', '', header_title).strip()
                
                if clean_title:
                    charter_list.append(f"<li style='margin-bottom: 8px;'><b>{clean_title}</b></li>")

        # Deduplicate the list
        unique_charters = list(dict.fromkeys(charter_list))

        if unique_charters:
            html_output = f"<h3 style='color: black;'>Charters referencing '{keyword}':</h3><ul>" + "".join(unique_charters) + "</ul>"
            self.dockwidget.text_display.setHtml(html_output)
        else:
            self.dockwidget.text_display.setHtml(f"No charters found mentioning '<b>{keyword}</b>'.")