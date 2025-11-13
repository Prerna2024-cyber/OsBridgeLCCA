from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QCoreApplication, Qt, QSize, Signal
from PySide6.QtWidgets import (QHBoxLayout, QPushButton, QLineEdit, QComboBox, QGridLayout, QWidget, QLabel, QVBoxLayout, QScrollArea, QSpacerItem, QSizePolicy, QFrame)
from PySide6.QtGui import QIcon
from ..utils.data import *
import sys

class ComponentWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.widgets = []
        self.data = data
        self.material_rows = [] # To store references to widgets in each material row
        self.current_material_row_idx = 1 # Start index for material rows (0 is header)    

        self.init_ui()

    def init_ui(self):
        self.component_first_scroll_content_layout = QVBoxLayout(self) # Set QVBoxLayout directly on self
        self.component_first_scroll_content_layout.setContentsMargins(10, 10, 10, 10)
        self.component_first_scroll_content_layout.setSpacing(10)

        # --- Material Details Grid Layout ---
        self.material_grid_layout = QGridLayout()
        self.material_grid_layout.setHorizontalSpacing(10)
        self.material_grid_layout.setVerticalSpacing(5)

        # Header Row - Updated headers for clarity (no specific unit in header now)
        headers = ["Type of Material and Grade", "Quantity", "Unit", "Embodied Carbon Energy", "Carbon Emission Factor"]
        for col, header_text in enumerate(headers):
            label = QLabel(header_text)
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("MaterialGridLabel")
            if header_text=="Embodied Carbon Energy":
               self.material_grid_layout.addWidget(label, 0, col, alignment=Qt.AlignmentFlag.AlignRight)
            else: 

               self.material_grid_layout.addWidget(label, 0, col, alignment=Qt.AlignmentFlag.AlignCenter)   

        self.component_first_scroll_content_layout.addLayout(self.material_grid_layout)
    
        # Add initial two material rows
        for item in self.data:
            self.widgets.append(self.add_material_row(item))
            
        # --- Add Material Button ---
        self.add_material_button = QPushButton("+ Add Material")
        self.add_material_button.setObjectName("add_material_button")
        self.add_material_button.clicked.connect(self.add_material_row)
        self.component_first_scroll_content_layout.addWidget(self.add_material_button, alignment=Qt.AlignCenter)
        
    def add_material_row(self, item=[]):
        row_idx = self.current_material_row_idx
        row_widgets = []

        # Set fixed width for input widgets.
        fixed_input_width_combo = 80
        fixed_input_width_line_edit = 80

        # Type of Material (Column 0)
        if item:
            type_material = QComboBox()
            type_material.addItem(item[0])
        else:
            type_material = QLineEdit()
            type_material.setPlaceholderText("Material...")
        type_material.setObjectName("MaterialGridInput")
        type_material.setFixedWidth(fixed_input_width_combo)
        self.material_grid_layout.addWidget(type_material, row_idx, 0, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Quantity (Column 1)
        quantity_edit = QLineEdit()
        if item:
            quantity_edit.setText(str(item[2]))
            quantity_edit.setReadOnly(True)
        quantity_edit.setObjectName("MaterialGridInput")
        quantity_edit.setFixedWidth(fixed_input_width_line_edit)
        self.material_grid_layout.addWidget(quantity_edit, row_idx, 1, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Unit (Column 2)
        if item:
            unit_combo = QComboBox()
            unit_combo.addItem(str(item[1]))
        else:
            unit_combo = QLineEdit()
            unit_combo.setPlaceholderText("Unit...")
        unit_combo.setObjectName("MaterialGridInput")
        unit_combo.setFixedWidth(fixed_input_width_combo)
        self.material_grid_layout.addWidget(unit_combo, row_idx, 2, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Build row_widgets array in correct order: [unit, quantity, type, grade, embodied_carbon, carbon_emission]
        if item:
            row_widgets = [item[1], item[2], item[3], item[4]]
        else:
            row_widgets = [unit_combo, quantity_edit, type_material, None]

        # --- Embodied Carbon Energy (LineEdit + QLabel for unit text) - Column 3 ---
        embodied_carbon_layout = QHBoxLayout()
        embodied_carbon_layout.addStretch()
        embodied_carbon_layout.setContentsMargins(0, 0, 0, 0)
        embodied_carbon_layout.setSpacing(5)

        embodied_carbon_edit = QLineEdit()
        embodied_carbon_edit.setPlaceholderText("0.00")
        embodied_carbon_edit.setObjectName("MaterialGridInput")
        embodied_carbon_edit.setFixedWidth(fixed_input_width_combo)
        embodied_carbon_layout.addWidget(embodied_carbon_edit)

        embodied_carbon_unit_label = QLabel("(MJ/kg)")
        embodied_carbon_unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        embodied_carbon_unit_label.setStyleSheet("color: #3F3E5E; font-size: 11px;")
        embodied_carbon_layout.addWidget(embodied_carbon_unit_label)

        self.material_grid_layout.addLayout(embodied_carbon_layout, row_idx, 3, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Add embodied carbon edit to row_widgets (index 4)
        row_widgets.append(embodied_carbon_edit)

        # --- Carbon Emission Factor (LineEdit + QLabel for unit text) - Column 4 ---
        carbon_emission_layout = QHBoxLayout()
        carbon_emission_layout.setContentsMargins(0, 0, 0, 0)
        carbon_emission_layout.setSpacing(5)
        carbon_emission_layout.addStretch()

        carbon_emission_edit = QLineEdit()
        carbon_emission_edit.setPlaceholderText("0.00")
        carbon_emission_edit.setObjectName("MaterialGridInput")
        carbon_emission_edit.setFixedWidth(fixed_input_width_combo)
        carbon_emission_layout.addWidget(carbon_emission_edit)

        # Create the carbon emission unit label
        if item:
            carbon_emission_unit_label = QLabel("kg CO2e/" + str(item[1]))
        else:
            carbon_emission_unit_label = QLabel("kg CO2e/kg")
        carbon_emission_unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        carbon_emission_unit_label.setStyleSheet("color: #3F3E5E; font-size: 11px;")
        carbon_emission_layout.addWidget(carbon_emission_unit_label)

        carbon_emission_layout.addStretch()
        self.material_grid_layout.addLayout(carbon_emission_layout, row_idx, 4)
        
        # Add carbon emission edit to row_widgets (index 5)
        row_widgets.append(carbon_emission_edit)

        # Only connect if it's a custom row (unit_combo is QLineEdit, not QComboBox)
        if not item:  # This means it's a custom material row
            def update_carbon_unit(text):
                unit_text = text.strip() if text.strip() else "kg"
                carbon_emission_unit_label.setText(f"kg CO2e/{unit_text}")
            
            unit_combo.textChanged.connect(update_carbon_unit)

        self.material_rows.append(row_widgets)
        self.current_material_row_idx += 1
        self.updateGeometry()
        self.adjustSize()

        if not item:
            # append widget to self.widget
            self.widgets.append(row_widgets)

        return row_widgets

    def remove_material_row_by_widgets(self, row_widgets_to_remove):
        if row_widgets_to_remove not in self.material_rows:
            return

        row_idx_in_grid = -1
        for i, row_dict in enumerate(self.material_rows):
            if row_dict == row_widgets_to_remove:
                row_idx_in_grid = i + 1  # +1 because row 0 is header
                break

        if row_idx_in_grid == -1:
            return

        for col in range(self.material_grid_layout.columnCount()):
            item = self.material_grid_layout.itemAtPosition(row_idx_in_grid, col)
            if item:
                if item.widget():
                    widget = item.widget()
                    self.material_grid_layout.removeWidget(widget)
                    widget.deleteLater()
                elif item.layout():
                    layout = item.layout()
                    # Iterate and delete widgets within the layout
                    while layout.count():
                        sub_item = layout.takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
                    self.material_grid_layout.removeItem(layout) # Remove the layout itself

        self.material_rows.remove(row_widgets_to_remove)
        self.current_material_row_idx -= 1

        # Re-arrange remaining rows
        for r_idx in range(row_idx_in_grid, self.current_material_row_idx + 1):
            for c_idx in range(self.material_grid_layout.columnCount()):
                item = self.material_grid_layout.itemAtPosition(r_idx + 1, c_idx) # Look at the row below
                if item:
                    if item.widget():
                        widget = item.widget()
                        self.material_grid_layout.removeWidget(widget)
                        self.material_grid_layout.addWidget(widget, r_idx, c_idx, alignment=Qt.AlignmentFlag.AlignHCenter) # Re-add with original alignment
                    elif item.layout():
                        layout = item.layout()
                        self.material_grid_layout.removeItem(layout)
                        self.material_grid_layout.addLayout(layout, r_idx, c_idx, alignment=Qt.AlignmentFlag.AlignHCenter) # Re-add with original alignment

        self.updateGeometry()
        self.update()
        self.material_grid_layout.invalidate()
        self.adjustSize()


    def collect_data(self):
        p = []
        for row in self.widgets:
            data = {
                KEY_TYPE: row[2].text() if isinstance(row[2], QLineEdit) else row[2],
                KEY_GRADE: row[3].text() if isinstance(row[3], QLineEdit) else "",
                KEY_QUANTITY: row[1].text() if isinstance(row[1], QLineEdit) else row[1],
                KEY_UNIT_M3: row[0].text() if isinstance(row[0], QLineEdit) else row[0],
                KEY_EMBODIED_CARBON_ENERGY: row[4].text() if row[4].text() else "0",
                KEY_CARBON_EMISSION_FACTOR: row[5].text() if row[4].text() else "0",
            }
            p.append(data)
        return p


class CarbonEmissionData(QWidget):
    closed = Signal()
    next = Signal(str)
    back = Signal(str)
    def __init__(self, database, parent=None):
        super().__init__()
        self.database_manager = database
        self.material_store = self.database_manager.get_unique_materials_and_grades()
        print(self.material_store)
        self.component_widgets = [] # To store references to each ComponentWidget instance

        self.setStyleSheet("""
            #central_panel_widget {
                background-color: #F8F8F8;
                border-radius: 8px;
            }
            #central_panel_widget QLabel {
                color: #333333;
                font-size: 12px;
            }
            #central_panel_widget QLabel#page_number_label {
                font-size: 14px;
                font-weight: bold;
                color: #555555;
            }

            QScrollArea {

                background-color: transparent;
                outline: none;
            }
            #scroll_content_widget {
                background-color: #FFF9F9;
                border: 1px solid #000000;
                padding-bottom: 20px;
            }

            QScrollBar:vertical {
                border: 1px solid #E0E0E0;
                background: #F0F0F0;
                width: 12px;
                margin: 18px 0px 18px 0px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #C0C0C0;
                border: 1px solid #A0A0A0;
                min-height: 20px;
                border-radius: 5px;
            }

            QScrollBar::add-line:vertical {
                border: 1px solid #E0E0E0;
                background: #E8E8E8;
                height: 18px;
                subcontrol-origin: bottom;
                subcontrol-position: bottom;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }

            QScrollBar::sub-line:vertical {
                border: 1px solid #E0E0E0;
                background: #E8E8E8;
                height: 18px;
                subcontrol-origin: top;
                subcontrol-position: top;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 10px;
                height: 10px;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar::up-arrow:vertical {
                image: url(resources/arrow_up.png);
            }
            QScrollBar::down-arrow:vertical {
                image: url(resources/arrow_down.png);
            }

            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {
                background: #D0D0D0;
            }

            QPushButton#top_button_left_panel {
                background-color: #FDEFEF;
                border-top: 1px solid #000000;
                border-left: 1px solid #000000;
                border-right: 1px solid #000000;
                text-align: left;
                padding: 4px 10px;
                color: #000000;
            }
            QPushButton#top_button_left_panel:hover {
                background-color: #F0E6E6;
                border-color: #808080;
            }
            QPushButton#top_button_left_panel:pressed {
                background-color: #FFF3F3;
                border-color: #606060;
            }

            /* Styling for component_first_widget (the container for the nested scroll area) */
            #component_first_widget {
                background-color: transparent;
                margin-top: 10px; /* Add some space above each component block */
            }

            #component_first_scroll_content_widget { /* This now applies directly to ComponentWidget itself */
                background-color: #FFFFFF;
                padding: 10px;

                border-radius: 8px;
            }

            /* Updated Styling for navigation buttons to match the Add Material/Component buttons */
            QPushButton#nav_button {
                background-color: #FFFFFF; /* White background */
                border: 1px solid #E0E0E0; /* Light grey border */
                border-radius: 8px; /* Slightly more rounded corners */
                color: #3F3E5E; /* Dark text color */
                padding: 6px 15px; /* Increased padding */
                text-align: center;
                min-width: 80px; /* Ensure a minimum width */
            }
            QPushButton#nav_button:hover {
                background-color: #F8F8F8; /* Very subtle light grey on hover */
                border-color: #C0C0C0; /* Darker border on hover */
            }
            QPushButton#nav_button:pressed {
                background-color: #E8E8E8; /* Darker grey on pressed */
                border-color: #A0A0A0; /* Even darker border */
            }
            /* Styling for QComboBox */
            QComboBox {
                border: 1px solid #DDDCE0;
                border-radius: 10px;
                padding: 3px 10px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 5px;
            }
            QComboBox::down-arrow {
                image: url(resources/country_arrow.png);
                width: 30px;
                height: 30px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #DDDCE0;
                border-radius: 5px;
                background-color: #FFFFFF;
                outline: none;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #FDEFEF;
                color: #000000;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #FDEFEF;
            }

            /* Styling for material grid elements */
            #MaterialGridLabel {
                font-weight: bold;
                color: #3F3E5E;
                padding: 5px;
                text-align: center;
            }
            #MaterialGridInput {
                border: 1px solid #DDDCE0;
                border-radius: 10px;
                padding: 3px 10px;
                background-color: #FFFFFF;
            }
            #MaterialGridInput:focus {
                border: 1px solid #DDDCE0;
                background-color: #FFFFFF;
            }
            /* IMPROVED CSS FOR ADD MATERIAL/COMPONENT BUTTONS */
            QPushButton#add_material_button, QPushButton#add_component_button {
                background-color: #FFFFFF; /* White background */
                border: 1px solid #E0E0E0; /* Light grey border */
                border-radius: 8px; /* Slightly more rounded corners */
                color: #3F3E5E; /* Dark text color */
                padding: 6px 15px; /* Increased padding */
                text-align: center;
            }
            QPushButton#add_material_button:hover, QPushButton#add_component_button:hover {
                background-color: #F8F8F8; /* Very subtle light grey on hover */
                border-color: #C0C0C0; /* Darker border on hover */
            }
            QPushButton#add_material_button:pressed, QPushButton#add_component_button:pressed {
                background-color: #E8E8E8; /* Darker grey on pressed */
                border-color: #A0A0A0; /* Even darker border */
            }
            /* END IMPROVED CSS */
        """)

        self.setObjectName("central_panel_widget")
        left_panel_vlayout = QVBoxLayout(self)
        left_panel_vlayout.setContentsMargins(0, 0, 0, 0)
        left_panel_vlayout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_content_widget = QWidget()
        scroll_content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroll_content_widget.setObjectName("scroll_content_widget")
        self.scroll_area.setWidget(scroll_content_widget)

        self.scroll_content_layout = QVBoxLayout(scroll_content_widget)
        self.scroll_content_layout.setContentsMargins(0,0,0,0)
        self.scroll_content_layout.setSpacing(0)

        # Create the navigation buttons layout
        self.button_h_layout = QHBoxLayout()
        self.button_h_layout.setSpacing(10)
        self.button_h_layout.setContentsMargins(10,10,10,10)

        # Adjust these stretch factors to control the position
        self.button_h_layout.addStretch(6) # Larger stretch on the left to push it more right

        back_button = QPushButton("Back")
        back_button.setObjectName("nav_button")
        back_button.clicked.connect(lambda: self.back.emit(KEY_CARBON_EMISSION))
        self.button_h_layout.addWidget(back_button)

        next_button = QPushButton("Next")
        next_button.setObjectName("nav_button")
        next_button.clicked.connect(self.collect_data)
        next_button.clicked.connect(lambda: self.next.emit(KEY_CARBON_EMISSION))
        self.button_h_layout.addWidget(next_button)


        # Add the initial component layout
        self.add_component_layout()
        

        # Add initial spacing before the navigation buttons
        self.scroll_content_layout.addLayout(self.button_h_layout)

        # --- Add a corner spacer to the scroll_content_layout ---
        self.button_h_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.scroll_content_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        left_panel_vlayout.addWidget(self.scroll_area)


    def add_component_layout(self):
        new_component = ComponentWidget(data=self.material_store, parent=self)
        self.component_widgets.append(new_component)

        # Temporarily remove button_h_layout and the vertical spacer for insertion
        # Find the vertical spacer and remove it if it exists
        vertical_spacer_item = None
        for i in range(self.scroll_content_layout.count()):
            item = self.scroll_content_layout.itemAt(i)
            if isinstance(item, QSpacerItem) and item.sizeHint().width() == 0: # This identifies the vertical spacer
                vertical_spacer_item = self.scroll_content_layout.takeAt(i)
                break

        if self.scroll_content_layout.indexOf(self.button_h_layout) != -1:
            self.scroll_content_layout.removeItem(self.button_h_layout)

        # Insert the new component
        self.scroll_content_layout.addWidget(new_component)

        # Re-add the navigation buttons layout
        self.scroll_content_layout.addLayout(self.button_h_layout)
        
        # Re-add the vertical spacer if it was found
        if vertical_spacer_item:
            self.scroll_content_layout.addItem(vertical_spacer_item)

        self.scroll_area.widget().updateGeometry()
        self.scroll_area.widget().adjustSize()


    def remove_component_layout(self, component_to_remove):
        if component_to_remove in self.component_widgets:
            self.scroll_content_layout.removeWidget(component_to_remove)
            self.component_widgets.remove(component_to_remove)
            component_to_remove.deleteLater()
            self.scroll_area.widget().updateGeometry()
            self.scroll_area.widget().adjustSize()


    def expand_scroll_area(self):
        self.central_widget.layout().invalidate()   

    def close_widget(self):
        self.closed.emit()
        self.setParent(None)

    def collect_data(self):
        data = self.component_widgets[0].collect_data()
        print("Collected Data from UI:",data)     
        self.database_manager.insert_carbon_emission_data(data)


#----------------Standalone-Test-Code--------------------------------

# class MyMainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         self.setStyleSheet("border: none")

#         self.central_widget = QWidget()
#         self.central_widget.setObjectName("central_widget")
#         self.setCentralWidget(self.central_widget)

#         self.main_h_layout = QHBoxLayout(self.central_widget)
#         self.main_h_layout.addStretch(1)

#         self.main_h_layout.addWidget(CarbonEmissionData(), 2)

#         self.setWindowState(Qt.WindowMaximized)


# if __name__ == "__main__":
#     QCoreApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)
#     app = QApplication(sys.argv)
#     window = MyMainWindow()
#     window.show()
#     sys.exit(app.exec())