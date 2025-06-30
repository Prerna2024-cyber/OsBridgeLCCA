import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QFrame, QSplitter,
                            QToolBar, QAction, QGroupBox, QMenu, QLineEdit,
                            QComboBox, QSizePolicy, QMessageBox, QTextEdit, QScrollArea,
                            QTabWidget, QStackedWidget)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize


class MainWindow(QMainWindow): # Renamed to MainWindow, inheriting QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle("<untitled draft> - BICCA Studio 1.0.0")
        self.setGeometry(100, 100, 1440, 1024)
        self.setStyleSheet("background-color: rgb(255, 255, 255);")

        # Initialize tutorial page counter
        self.current_tutorial_page = 1
        self.total_tutorial_pages = 4

        # Tutorial content
        self.tutorial_pages = [
            {
                "page_number": "1/4",
                "title": "Welcome to\nBICCA Studio",
                "content": """
                BICCA Studio has a lot of features to offer. In the next few minutes, you'll learn how to use BICCA Studio efficiently, from setting up and managing projects, to navigating the user interface. This tutorial will guide you through essential features, including customization options, shortcuts, and export capabilities, ensuring a seamless workflow. Whether you're a beginner or an advanced user, this guide will help you unlock the full potential of BICCA Studio and enhance your productivity.
                """
            },
            {
                "page_number": "2/4",
                "title": "Welcome to\nBICCA Studio",
                "content": """
                The Project General Information page is the foundation of your project setup, allowing you to input essential details for accurate documentation and streamlined management. Here, you will provide key information starting with the Company Name, which represents the organization behind the project. Next is the Project Title, a concise name that defines the scope of work. The Project Description further elaborates on the objectives and purpose of the project. Additionally, you will need to enter the Name of the Valuer responsible for the valuation, along with the Job Number for easy reference. The Client field identifies the primary stakeholder of the project, while the Country specifies the project's geographical location. Finally, the Base Year establishes a reference period for analysis and reports.
                """
            },
            {
                "page_number": "3/4",
                "title": "Understanding\nInput Parameters",
                "content": """
                Input Parameters are crucial for accurate analysis and results. This section allows you to define various technical specifications, economic factors, and operational variables that will influence your project outcomes. You can specify factors such as time periods, growth rates, discount rates, and other numerical inputs that the software will use for calculations. Each parameter can be customized according to your specific requirements, ensuring that the analysis reflects real-world conditions accurately. The intuitive interface makes it easy to adjust these parameters as needed, and you can save different parameter sets for future use or comparisons.
                """
            },
            {
                "page_number": "4/4",
                "title": "Working with\nOutputs",
                "content": """
                The Outputs section displays the results of your analysis based on the information and parameters you've entered. Here you can view comprehensive reports, charts, and visualizations that present your data in meaningful ways. You can customize the output format according to your preferences or your client's requirements. BICCA Studio allows you to export these outputs in various formats including PDF, Excel, or as image files for easy sharing and presentation. Additionally, you can compare different scenarios by adjusting your inputs and generating new outputs, providing valuable insights for decision-making processes.
                """
            }
        ]

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- CORRECTED ORDER: Create UI elements BEFORE retranslateUi ---
        self.create_menu_bar()
        self.create_toolbar()
        self.create_window_tabs() # Custom tab buttons that control splitter visibility
        self.create_content_area() # Contains the QSplitter for panels
        self.create_status_bar() # Includes the persistent "Data" section

        self.retranslateUi(self) # Call retranslateUi *after* all widgets are created

        self.update_tutorial_content()

        # Set initial visible panels and button states for the custom tabs
        self.handle_tab_click("Tutorials", initial_load=True)
        self.handle_tab_click("Project Details", initial_load=True)

        # Connect QGroupBox toggled signals
        self.generalInfoGroup.toggled['bool'].connect(lambda checked: self.toggle_general_info_group_content(self.generalInfoGroup, checked))
        self.inputParamsGroup.toggled['bool'].connect(lambda checked: self.toggle_input_params_group_content(self.inputParamsGroup, checked))
        self.outputsGroup.toggled['bool'].connect(lambda checked: self.toggle_outputs_group_content(self.outputsGroup, checked))

        # Connect internal buttons to hide/show their respective sub-content
        self.pushButton.clicked.connect(lambda: self.toggle_sub_buttons_visibility(self.gridLayout_3, self.pushButton))
        self.pushButton_7.clicked.connect(lambda: self.toggle_sub_buttons_visibility(self.gridLayout_4, self.pushButton_7))

        # Initially hide the collapsible sub-sections' content
        self.gridLayout_3_widget.setVisible(False) # Hide the widget holding gridLayout_3
        self.gridLayout_4_widget.setVisible(False) # Hide the widget holding gridLayout_4

        # Manually trigger initial state for General Info, Input Params, Outputs groups
        self.toggle_general_info_group_content(self.generalInfoGroup, self.generalInfoGroup.isChecked())
        self.toggle_input_params_group_content(self.inputParamsGroup, self.inputParamsGroup.isChecked())
        self.toggle_outputs_group_content(self.outputsGroup, self.outputsGroup.isChecked())

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "<untitled draft> - BICCA Studio 1.0.0"))
        
        # Custom Tab button texts
        self.tab_buttons["Tutorials"].setText(_translate("MainWindow", "Tutorials"))
        self.tab_buttons["Project Details"].setText(_translate("MainWindow", "Project Details"))
        self.tab_buttons["Results"].setText(_translate("MainWindow", "Results"))
        self.tab_buttons["Compare"].setText(_translate("MainWindow", "Compare"))

        # Headers for panels
        self.tutorials_header_label.setText(_translate("MainWindow", "Tutorials"))
        self.project_header_label.setText(_translate("MainWindow", "Project Details Window"))
        self.results_header_label.setText(_translate("MainWindow", "Results"))
        self.compare_header_label.setText(_translate("MainWindow", "Compare"))

        # Group Box Titles
        self.generalInfoGroup.setTitle(_translate("MainWindow", "General Information"))
        self.inputParamsGroup.setTitle(_translate("MainWindow", "Input Parameters"))
        self.outputsGroup.setTitle(_translate("MainWindow", "Outputs"))

        # General Information Labels and Placeholders
        self.label_company_name.setText(_translate("MainWindow", "Company Name"))
        self.lineEdit_company_name.setPlaceholderText(_translate("MainWindow", "Enter Company Name"))
        self.label_project_title.setText(_translate("MainWindow", "Project Title"))
        self.lineEdit_project_title.setPlaceholderText(_translate("MainWindow", "Enter Project Title"))
        self.label_project_description.setText(_translate("MainWindow", "Project Description"))
        self.textEdit_project_description.setPlaceholderText(_translate("MainWindow", "Enter Project Description"))
        self.label_valuer_name.setText(_translate("MainWindow", "Name of Valuer"))
        self.lineEdit_valuer_name.setPlaceholderText(_translate("MainWindow", "Enter Valuer's Name"))
        self.label_job_number.setText(_translate("MainWindow", "Job Number"))
        self.lineEdit_job_number.setPlaceholderText(_translate("MainWindow", "Enter Job Number"))
        self.label_client.setText(_translate("MainWindow", "Client"))
        self.lineEdit_client.setPlaceholderText(_translate("MainWindow", "Enter Client Name"))
        self.label_country.setText(_translate("MainWindow", "Country"))
        self.label_base_year.setText(_translate("MainWindow", "Base Year"))
        self.lineEdit_base_year.setPlaceholderText(_translate("MainWindow", "e.g., 2023"))

        # Input Parameters Buttons
        self.pushButton.setText(_translate("MainWindow", "Structure Works Data"))
        self.pushButton_3.setText(_translate("MainWindow", "Super-Structure"))
        self.pushButton_2.setText(_translate("MainWindow", "Foundation"))
        self.pushButton_4.setText(_translate("MainWindow", "Sub-Structure"))
        self.pushButton_5.setText(_translate("MainWindow", "Miscellaneous"))
        self.pushButton_6.setText(_translate("MainWindow", "Financial Data"))
        self.pushButton_7.setText(_translate("MainWindow", "Carbon Emission Data"))
        self.pushButton_8.setText(_translate("MainWindow", "Carbon Emission Cost Data"))
        self.pushButton_9.setText(_translate("MainWindow", "Bridge and Traffic Data"))
        self.pushButton_10.setText(_translate("MainWindow", "Maintenance and Repair"))
        self.pushButton_11.setText(_translate("MainWindow", "Disposal and Recycling"))

        # Outputs Label
        self.label_10.setText(_translate("MainWindow", "Output content goes here."))

        # Menu and Toolbar actions
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuHome.setTitle(_translate("MainWindow", "Home"))
        self.menuReports.setTitle(_translate("MainWindow", "Reports"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actionNew.setText(_translate("MainWindow", "New"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionSave_As.setText(_translate("MainWindow", "Save As..."))
        self.actionCreate_a_Copy.setText(_translate("MainWindow", "Create a Copy"))
        self.actionPrint.setText(_translate("MainWindow", "Print"))
        self.actionRename.setText(_translate("MainWindow", "Rename"))
        self.actionExport.setText(_translate("MainWindow", "Export"))
        self.actionVersion_History.setText(_translate("MainWindow", "Version History"))
        self.actionInfo.setText(_translate("MainWindow", "Info"))
        self.actionContact_Us.setText(_translate("MainWindow", "Contact Us"))
        self.actionFeedback.setText(_translate("MainWindow", "Feedback"))
        self.actionVideo_Tutorials.setText(_translate("MainWindow", "Video Tutorials"))
        self.actionJoin_our_Community.setText(_translate("MainWindow", "Join our Community"))

        # Data section retranslate
        self.combo_box_lookup.setItemText(0, _translate("MainWindow", "Carbon Data"))
        self.combo_box_lookup.setItemText(1, _translate("MainWindow", "Maintenance Rate Data"))
        self.combo_box_lookup.setItemText(2, _translate("MainWindow", "Recycling Data"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
