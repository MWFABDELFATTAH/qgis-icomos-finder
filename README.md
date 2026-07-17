# ICOMOS Finder - QGIS Plugin

An experimental digital humanities and GeoAI research plugin for QGIS. This tool acts as a spatial-textual bridge, allowing heritage researchers to rapidly query ICOMOS Charters and extract theoretical frameworks directly within their GIS environment.

## 🌟 Features
* **Keyword-to-Charter Engine:** Rapidly scans ICOMOS documents and isolates relevant paragraphs based on thematic keywords.
* **Reading List Generator:** Automatically compiles a clean, deduplicated bibliography of charters referencing specific heritage themes (e.g., "water", "authenticity", "community").
* **Offline Processing:** Runs entirely locally via a compiled text database without requiring API calls.

## 📥 How to Install
Since this is an experimental research tool, it is not yet in the official QGIS repository. To install it manually:

1. Click the green **Code** button at the top of this page and select **Download ZIP**.
2. Do **not** unzip the file.
3. Open QGIS.
4. Go to **Plugins** > **Manage and Install Plugins** > **Install from ZIP**.
5. Select the downloaded ZIP file and click Install.
6. The ICOMOS logo will appear in your QGIS toolbar!

## 🔬 Research Context
This plugin was developed as a methodological tool to assist in deep case studies of urban hydrological heritage and vulnerable landscapes. By streamlining the retrieval of international conservation standards, it frees up researcher time for ground-truth validation and community-driven mapping.



---------------------------

### Prerequisites

Before writing code, ensure you have the following installed within QGIS:

1. **Plugin Builder 3:** A tool to generate the basic folder structure (install via QGIS > Plugins > Manage and Install Plugins).
2. **Plugin Reloader:** A tool to refresh your plugin without having to close QGIS every time you make a change.

---

### Step 1: Generate the Plugin Boilerplate

We start by asking QGIS to create the basic "skeleton" of the plugin.

1. Open QGIS and click **Plugins > Plugin Builder > Plugin Builder**.
2. Fill out the form:
* **Class name:** `ICOMOSNOTES`
* **Plugin name:** `ICOMOS FINDER`
* **Description:** `Extracts spatial-heritage knowledge from ICOMOS charters.`
* **Module name:** `icomos`


3. Click **Next** until you reach the end, selecting **Tool button with dock widget** as the template type.
4. Generate the plugin and save it directly to your QGIS active profile plugin directory:
`C:\Users\YOUR_USER\AppData\Roaming\QGIS\QGIS4\profiles\default\python\plugins\icomos\`

---

### Step 2: Design the User Interface (UI)

We need to create the visual interface where users type their keywords.

1. In your plugin folder, find the file ending in `_dockwidget_base.ui` and open it with **Qt Designer** (a free software that comes bundled with QGIS).
2. Drag and drop the following widgets onto your blank canvas from the left panel:
* **Line Edit:** (For the user to type their keyword).
* *Crucial:* In the Property Editor on the right, change its `objectName` to `search_input`.


* **Push Button:** (To trigger the search).
* *Crucial:* Change its `objectName` to `btn_search` and change the text to "Search Charters".


* **Push Button:** (To generate the bibliography).
* *Crucial:* Change its `objectName` to `btn_reading_list` and change the text to "Generate Reading List".


* **Text Browser:** (To display the results).
* *Crucial:* Change its `objectName` to `text_display`.




3. Save the file in Qt Designer.
4. Compile the UI by running the `compile.bat` file in your plugin folder (or using the `pb_tool` command if you have it set up).

---

### Step 3: Prepare the Data File

Your Python code needs a rigorously formatted text file to read from.

1. Create a text file in your plugin folder named exactly: **`icomos_charters.txt`**.
2. Format your ICOMOS charters using this exact structure:
* `###` to indicate a new charter.
* The text immediately following is the **Title**.
* `<span style="color: red;">` to mark the metadata/adoption details.
* The rest of the text is the charter body.



**Example format inside your text file:**

```text
###
PRINCIPLES FOR THE PRESERVATION OF HISTORIC TIMBER STRUCTURES (1999)
<span style="color: red;">Adopted by ICOMOS at the 12th General Assembly in Mexico, October 1999.</span>
The aim of this document is to define basic and universally applicable principles...

Another paragraph of the text...

```

---

### Step 4: Write the Python Logic

This is the brain of your plugin. It reads the UI inputs, scans the text file, and formats the output.

1. Open the `ICOMOS.py` file in your plugin folder using a code editor (like Notepad++, VS Code, or PyCharm).
2. Delete everything inside it and paste the final, polished code below:

```python
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
            
            # Connect UI buttons to Python functions
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

        charter_blocks = content.split('###')
        results_html = []
        search_pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        for block in charter_blocks:
            if not block.strip(): continue
            if '<span style="color: red;">' not in block: continue
            
            parts = block.split('<span style="color: red;">', 1)
            header_title = parts[0].strip()
            rest_of_block = parts[1]
            
            if '</span>' in rest_of_block:
                metadata, para_text = rest_of_block.split('</span>', 1)
            else:
                para_text = rest_of_block
                
            paragraphs = re.split(r'\n\s*\n', para_text.strip())
            
            matching_paras = []
            for para in paragraphs:
                if search_pattern.search(para):
                    highlighted = search_pattern.sub(
                        lambda m: f'<span style="background-color: yellow; color: black; font-weight: bold;">{m.group(0)}</span>',
                        para.strip()
                    )
                    matching_paras.append(highlighted)
            
            if matching_paras:
                results_html.append(f"<div style='margin-bottom:20px;'><b style='color: blue; font-size: 14px;'>{header_title}</b><br><br>" + "<br><br>".join(matching_paras) + "</div><hr>")

        if results_html:
            self.dockwidget.text_display.setHtml("".join(results_html))
        else:
            self.dockwidget.text_display.setHtml(f"No mentions of '<b>{keyword}</b>' found.")

    def generate_reading_list(self):
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
            
            if search_pattern.search(block):
                parts = block.split('<span style="color: red;">', 1)
                header_title = parts[0].strip()
                clean_title = re.sub('<[^<]+?>', '', header_title).strip()
                
                if clean_title:
                    charter_list.append(f"<li style='margin-bottom: 8px;'><b>{clean_title}</b></li>")

        unique_charters = list(dict.fromkeys(charter_list))

        if unique_charters:
            html_output = f"<h3 style='color: black;'>Charters referencing '{keyword}':</h3><ul>" + "".join(unique_charters) + "</ul>"
            self.dockwidget.text_display.setHtml(html_output)
        else:
            self.dockwidget.text_display.setHtml(f"No charters found mentioning '<b>{keyword}</b>'.")

```

3. Save the file.

---

### Step 5: Add a Professional Icon

Ditch the default green plugin icon for a custom one.

1. Download or create a square `.png` image of your chosen logo.
2. Rename the image exactly to `icon.png`.
3. Drop it into your plugin folder, overwriting the default `icon.png` generated by the Plugin Builder.

---

### Step 6: Test in QGIS

1. Open QGIS.
2. If QGIS was already open, use the **Plugin Reloader** tool to refresh your plugin, or simply restart QGIS entirely.
3. Your custom icon will appear in the toolbar. Click it, dock the interface to the side, type in a keyword like "water", and hit **Search Charters** or **Generate Reading List**.
