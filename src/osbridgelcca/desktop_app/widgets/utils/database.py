import sqlite3
from typing import List, Dict, Tuple
from .data import *
from .cost_component import ( InitialConstructionCost, TimeCost, RoadUserCost,
                                    AdditionalCarbonEmissionCost, PeriodicMaintenanceCost,
                                    RoutineInspectionCost, RepairAndRehabilitationCost, 
                                    DemolitionCost, RecyclingCost, ReconstructionCost,
                                    PeriodicMaintenanceCarbonCost
)

class DatabaseManager:
    """Database manager for Structure Works Data"""
    
    def __init__(self, db_path: str = "widgets/utils/structure_works.db", recreate: bool = True):
        """
        Initialize database connection and create tables if they don't exist
        
        Args:
            db_path: Path to the database file
            recreate: If True, delete existing database and create fresh. If False, use existing database.
        """
        self.db_path = db_path
        self.conn = None
        self.create_database(recreate=recreate)
        self.carbon_cost = 6.3936
    
    def create_database(self, recreate: bool = True):
        """
        Create database tables with proper schema
        
        Args:
            recreate: If True, delete existing database and create fresh
        """
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Delete existing database if recreate is True
        if recreate and os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"Deleted existing database: {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create struct_works_data table first with comp_id as PRIMARY KEY
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS struct_works_data (
                comp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN (
                    'Foundation', 
                    'Sub-Structure', 
                    'Super-Structure', 
                    'Miscellaneous'
                )),
                component_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create component table with comp_id as FOREIGN KEY
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS component (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comp_id INTEGER NOT NULL,
                type_material TEXT NOT NULL,
                grade TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL,
                rate REAL NOT NULL DEFAULT 0.0,
                rate_data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (comp_id) REFERENCES struct_works_data(comp_id) ON DELETE CASCADE
            )
        ''')

        # Create financial_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                real_discount_rate REAL NOT NULL,
                interest_rate REAL NOT NULL,
                investment_ratio REAL NOT NULL,
                duration_of_study INTEGER NOT NULL,
                time_of_project INTEGER NOT NULL,       
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       
            )
        ''')

        cursor.execute('''
             CREATE TABLE IF NOT EXISTS carbon_emission(
                type_material TEXT NOT NULL,
                grade TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL,
                emission_factor REAL NOT NULL,
                embodied REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (type_material, grade, unit)
            )
        ''')
        
        self.conn.commit()
    
    def insert_structure_work(self, work_type: str, component_type: str) -> int:
        """
        Insert a new structure work entry
        
        Args:
            work_type: Type of structure work (Foundation, Sub-Structure, etc.)
            component_type: Type of component (e.g., 'Pile', 'Beam', etc.)
        
        Returns:
            comp_id: The auto-generated component ID (PRIMARY KEY)
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO struct_works_data (type, component_type)
            VALUES (?, ?)
        ''', (work_type, component_type))
        
        comp_id = cursor.lastrowid
        self.conn.commit()
        return comp_id
    
    def insert_component(self, comp_id: int, type_material: str, grade: str, 
                        quantity: float, unit: str, rate: float, 
                        rate_data_source: str = None) -> int:
        """
        Insert a new component (material row)
        
        Args:
            comp_id: Foreign key referencing struct_works_data.comp_id
            type_material: Type of material (e.g., 'Steel Re', 'Concrete')
            grade: Material grade (e.g., 'Fe415', 'M25')
            quantity: Quantity of material
            unit: Unit of measurement
            rate: Rate per unit
            rate_data_source: Source of rate data (optional)
        
        Returns:
            id: The ID of the newly created component row
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO component (comp_id, type_material, grade, quantity, unit, rate, rate_data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (comp_id, type_material, grade, quantity, unit, rate, rate_data_source))
        
        component_id = cursor.lastrowid
        self.conn.commit()
        return component_id
    
    def input_data_row(self, work_type: str, rows_data: List[Dict]) -> List[int]:
        """
        Input complete data row with structure work and multiple components
        
        Args:
            work_type: Type of structure work (Foundation, Sub-Structure, etc.)
            rows_data: List of dictionaries containing component data
        
        Returns:
            List of comp_id values created in struct_works_data for the provided rows
        
        Example:
            rows_data = [
                [
                    {
                        KEY_COMPONENT: "Pile",
                        KEY_TYPE: "Steel Re",
                        KEY_GRADE: "Fe415",
                        KEY_QUANTITY: "100",
                        KEY_UNIT_M3: "cum",
                        KEY_RATE: "5000.00",
                        KEY_RATE_DATA_SOURCE: "Market Survey"
                    },
                    ...
                ],
                ...
            ]
        """
        if not rows_data:
            raise ValueError("rows_data cannot be empty")
        
        created_comp_ids: List[int] = []
        for row in rows_data:
            # Get component type from first row
            component_type = row[0].get(KEY_COMPONENT, "Unknown")

            # Create structure work entry - this generates comp_id
            comp_id = self.insert_structure_work(work_type, component_type)
            created_comp_ids.append(comp_id)

            # Insert all component rows with the generated comp_id
            for row_dict in row:
                type_material = row_dict.get(KEY_TYPE, "")
                grade = row_dict.get(KEY_GRADE, "")
                quantity = float(row_dict.get(KEY_QUANTITY, 0))
                unit = row_dict.get(KEY_UNIT_M3, "")
                rate = float(row_dict.get(KEY_RATE, 0.0))
                rate_data_source = row_dict.get(KEY_RATE_DATA_SOURCE, "")
                
                self.insert_component(
                    comp_id=comp_id,
                    type_material=type_material,
                    grade=grade,
                    quantity=quantity,
                    unit=unit,
                    rate=rate,
                    rate_data_source=rate_data_source
                )
        
        return created_comp_ids

    def replace_structure_work_rows(self, work_type: str, rows_data: List[Dict], old_comp_ids: List[int]) -> List[int]:
        """
        Delete existing structure work rows by comp_id and insert new rows.
        
        Args:
            work_type: Type of structure work (Foundation, Sub-Structure, etc.)
            rows_data: New rows data to insert (same structure as input_data_row)
            old_comp_ids: List of comp_id values to delete before inserting new data
        
        Returns:
            List[int]: Newly created comp_id values for the inserted data
        """
        if old_comp_ids:
            for comp_id in old_comp_ids:
                self.delete_structure_work(comp_id)
        
        return self.input_data_row(work_type, rows_data)

    def delete_structure_work(self, comp_id: int):
        """Delete a structure work and all its components (CASCADE)"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM struct_works_data WHERE comp_id = ?', (comp_id,))
        self.conn.commit()
    
    def delete_component(self, component_id: int):
        """Delete a specific component by its ID"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM component WHERE id = ?', (component_id,))
        self.conn.commit()
    
    def get_all_structure_works(self) -> List[Tuple]:
        """Get summary of all structure works"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT sw.comp_id, sw.type, sw.component_type, COUNT(c.id) as component_count
            FROM struct_works_data sw
            LEFT JOIN component c ON sw.comp_id = c.comp_id
            GROUP BY sw.comp_id
            ORDER BY sw.type, sw.comp_id
        ''')
        return cursor.fetchall()
    
    def get_components_by_comp_id(self, comp_id: int) -> List[Tuple]:
        """Get all component rows for a specific comp_id"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, comp_id, type_material, grade, quantity, unit, rate, rate_data_source
            FROM component
            WHERE comp_id = ?
            ORDER BY id
        ''', (comp_id,))
        return cursor.fetchall()

    def _insert_financial_data(self, data: List[float]) -> int:
        """
        Insert a new row into the financial_data table
        
        Args:
            data: List containing [real_discount_rate, interest_rate, investment_ratio, duration_of_study]
                 in the same sequence as the table columns
        
        Returns:
            id: The ID of the newly created financial data row
        
        Raises:
            ValueError: If the data list doesn't contain exactly 4 elements
        """
        if len(data) != 5:
            raise ValueError("Data list must contain exactly 4 elements: [real_discount_rate, interest_rate, investment_ratio, duration_of_study]")
        
        cursor = self.conn.cursor()
        
        
        cursor.execute('''
            INSERT INTO financial_data (
                real_discount_rate,
                interest_rate,
                investment_ratio,
                duration_of_study,
                time_of_project
            )
            VALUES (?, ?, ?, ?,?)
        ''', data)
        
        financial_data_id = cursor.lastrowid
        self.conn.commit()
        return financial_data_id

    def get_all_materials_info(self) -> List[Dict]:
        """
        Retrieve all unique material types, grades, and quantities from the component table
        
        Returns:
            List of dictionaries containing material information with keys:
            - type_material: The type of material
            - grade: The grade of the material
            - quantity: The quantity used
            - unit: The unit of measurement
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT type_material, grade, quantity, unit, rate
            FROM component
            ORDER BY type_material, grade
        ''')
        
        results = []
        for row in cursor.fetchall():
            material_info = {
                'type_material': row[0],
                'grade': row[1],
                'quantity': row[2],
                'unit': row[3],
                'rate': row[4]
            }
            results.append(material_info)
        
        return results
    
    def get_unique_materials_and_grades(self) -> List[List[str]]:
        """
        Retrieve all unique material and grade pairs from the component table
        as a list of lists: [[type_material, grade], ...]
        """

        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT type_material, grade, unit, SUM(quantity) as total_quantity
            FROM component
            GROUP BY type_material, grade, unit
        ''')


        output =[[row[0], row[1], row[2], row[3]] for row in cursor.fetchall()]
        p = []
        for item in output:
            s = item[0] + " (" + item[1] + ")"
            p.append([s, item[2], item[3], item[0], item[1]])
        return p

    def insert_carbon_emission_data(self, data_list):
        """
        Insert multiple records into CARBON_EMISSION table
        
        Args:
            data_list: List of dictionaries containing carbon emission data
        """
        try:
            cursor = self.conn.cursor()
            
            # SQL insert statement
            insert_query = '''
                INSERT INTO CARBON_EMISSION 
                (type_material, grade, quantity, unit, emission_factor, embodied)
                VALUES (?, ?, ?, ?, ?, ?)
            '''

            # Prepare data for batch insert
            records = []
            for data in data_list:
                print(data)
                record = (
                    data.get(KEY_TYPE, ''),
                    data.get(KEY_GRADE, ''),
                    float(data.get(KEY_QUANTITY, 0)),
                    data.get(KEY_UNIT_M3, ''),
                    float(data.get(KEY_CARBON_EMISSION_FACTOR, 0)),
                    float(data.get(KEY_EMBODIED_CARBON_ENERGY, 0))
                    
                )
                records.append(record)
            # Execute batch insert
            cursor.executemany(insert_query, records)
            self.conn.commit()
            
            print(f"Successfully inserted {len(records)} records")
            return True
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def get_carbon_emission_data(self) -> List[Dict]:        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT type_material, unit, quantity, emission_factor
            FROM carbon_emission
        ''')

        results = []
        for row in cursor.fetchall():
            material_info = {
                KEY_TYPE: row[0],
                KEY_UNIT_M3: row[1],
                KEY_QUANTITY: row[2],
                KEY_RATE: row[3],
                KEY_CARBON_EMISSION_FACTOR: row[3]
            }
            results.append(material_info)
        return results

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    #========================Calculations========================

    # 1. Called on next from Auxiliary Cost Data.py
    def calculate_total_initial_cost(self) -> float:
        data = self.get_all_materials_info()
        total_cost = 0.0
        for item in data:
            component = InitialConstructionCost(
            quantity=item["quantity"],
            rate=item["rate"]
            )
            total_cost += component.calculate_cost()
        print("\nTotal Initial Construction Cost:", total_cost)
        return total_cost
    
    # 3. Called on next from financial_data.py
    def calculate_time_cost(self, data: List, total_init_construct_cost: float) -> float:
        # Insert financial data into the database
        self._insert_financial_data(data) 
        time_cost_component = TimeCost(
            construction_cost=total_init_construct_cost,
            interest_rate=float(data[1]),
            time=float(data[4]),
            investment_ratio=float(data[2])
        )
        print("\nTime Cost:", time_cost_component.calculate_cost())
        return time_cost_component.calculate_cost()

    # 2. Called on next from carbon_emission_cost_data.py
    def carbon_emission_cost(self, carbon_cost: float) -> float:
        # Updated Carbon cost
        self.carbon_cost = carbon_cost

        unit_conversions = {
            "cum": 2549.25,
            "kg": 1.0,
            "mt": 1000.0,
            "rmt": 1.0,
            "sqm": 1.0,
            "ltr": 1.0
        }

        # Get carbon emission data from the database
        data = self.get_carbon_emission_data()

        total_carbon_emission_cost= 0.0
        for item in data:
            total_component = 0.0
            qty = float(item.get(KEY_QUANTITY))
            unit = item.get(KEY_UNIT_M3)
            emission_factor = float(item.get(KEY_CARBON_EMISSION_FACTOR))
            # convert quantity to kg
            qty = qty * unit_conversions.get(unit.lower())
            total_component += qty                
            carbon_emission_cost = (total_component * emission_factor) * carbon_cost;
            total_carbon_emission_cost += carbon_emission_cost
            print(f"Carbon Emission Cost for {item.get(KEY_TYPE)}:", total_carbon_emission_cost)
        
        print("\nTotal Carbon Emission Cost:", total_carbon_emission_cost)
        return total_carbon_emission_cost

    IRC_ROAD_COSTS_DATA = {
        # Format: (Vehicle_Type, Lane_Type, Roughness, RF): Grand_Cost
        ("Car", "2", "Good", "Rolling"): 15.50,
        ("Car", "2", "Good", "Hilly"): 18.20,
        ("Car", "2", "Fair", "Rolling"): 17.80,
        ("Car", "2", "Fair", "Hilly"): 20.90,
        ("Car", "2", "Poor", "Rolling"): 22.40,
        ("Car", "2", "Poor", "Hilly"): 26.10,
        ("Car", "4", "Good", "Rolling"): 14.20,
        ("Car", "4", "Good", "Hilly"): 16.80,
        ("Car", "4", "Fair", "Rolling"): 16.50,
        ("Car", "4", "Fair", "Hilly"): 19.40,
        ("Car", "4", "Poor", "Rolling"): 21.10,
        ("Car", "4", "Poor", "Hilly"): 24.70,
        
        ("Bus", "2", "Good", "Rolling"): 45.80,
        ("Bus", "2", "Good", "Hilly"): 52.30,
        ("Bus", "2", "Fair", "Rolling"): 48.90,
        ("Bus", "2", "Fair", "Hilly"): 55.80,
        ("Bus", "2", "Poor", "Rolling"): 56.20,
        ("Bus", "2", "Poor", "Hilly"): 64.10,
        ("Bus", "4", "Good", "Rolling"): 42.50,
        ("Bus", "4", "Good", "Hilly"): 48.70,
        ("Bus", "4", "Fair", "Rolling"): 45.60,
        ("Bus", "4", "Fair", "Hilly"): 52.10,
        ("Bus", "4", "Poor", "Rolling"): 53.80,
        ("Bus", "4", "Poor", "Hilly"): 61.40,
        
        ("HCV", "2", "Good", "Rolling"): 78.90,
        ("HCV", "2", "Good", "Hilly"): 89.20,
        ("HCV", "2", "Fair", "Rolling"): 84.50,
        ("HCV", "2", "Fair", "Hilly"): 95.60,
        ("HCV", "2", "Poor", "Rolling"): 96.80,
        ("HCV", "2", "Poor", "Hilly"): 109.50,
        ("HCV", "4", "Good", "Rolling"): 75.40,
        ("HCV", "4", "Good", "Hilly"): 85.30,
        ("HCV", "4", "Fair", "Rolling"): 81.20,
        ("HCV", "4", "Fair", "Hilly"): 91.80,
        ("HCV", "4", "Poor", "Rolling"): 93.70,
        ("HCV", "4", "Poor", "Hilly"): 106.00,
        
        ("MCV", "2", "Good", "Rolling"): 56.70,
        ("MCV", "2", "Good", "Hilly"): 64.80,
        ("MCV", "2", "Fair", "Rolling"): 61.20,
        ("MCV", "2", "Fair", "Hilly"): 69.90,
        ("MCV", "2", "Poor", "Rolling"): 70.50,
        ("MCV", "2", "Poor", "Hilly"): 80.40,
        ("MCV", "4", "Good", "Rolling"): 54.30,
        ("MCV", "4", "Good", "Hilly"): 62.10,
        ("MCV", "4", "Fair", "Rolling"): 58.80,
        ("MCV", "4", "Fair", "Hilly"): 67.20,
        ("MCV", "4", "Poor", "Rolling"): 68.20,
        ("MCV", "4", "Poor", "Hilly"): 77.90,
        
        ("LCV", "2", "Good", "Rolling"): 38.40,
        ("LCV", "2", "Good", "Hilly"): 44.10,
        ("LCV", "2", "Fair", "Rolling"): 41.60,
        ("LCV", "2", "Fair", "Hilly"): 47.70,
        ("LCV", "2", "Poor", "Rolling"): 48.30,
        ("LCV", "2", "Poor", "Hilly"): 55.40,
        ("LCV", "4", "Good", "Rolling"): 36.80,
        ("LCV", "4", "Good", "Hilly"): 42.30,
        ("LCV", "4", "Fair", "Rolling"): 40.10,
        ("LCV", "4", "Fair", "Hilly"): 46.00,
        ("LCV", "4", "Poor", "Rolling"): 46.90,
        ("LCV", "4", "Poor", "Hilly"): 53.80,
    }

    # 4. Called on next from bridge_and_traffic_data.py
    def calculate_irc_road_cost(self, data: List) -> float:
        # fetch Construction time
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT time_of_project
            FROM financial_data
        ''')
        construction_time = float(cursor.fetchone()[0])
        
        total_road_user_cost = 0
        lanes = data[0]
        roughness = data[2]
        rf = data[3]

        key = ["Car", "Bus", "HCV", "MCV", "LCV"]
        for vehicle in key:
            count = int(data[6+key.index(vehicle)])
            key_vehicle = (vehicle, lanes, roughness, rf)
            cost_per_km = self.IRC_ROAD_COSTS_DATA.get(key_vehicle, "")
            if cost_per_km:
                ct = construction_time * float(data[1])
                road_user_cost_component = RoadUserCost(
                    vehicles_affected=count,
                    vehicle_operation_cost=cost_per_km,
                    construction_time=ct
                )
                total_road_user_cost += road_user_cost_component.calculate_cost()
            else:
                print(f"No Grand_Cost found for {vehicle}, {lanes}, {roughness}, {rf}")
        
        print("\nTotal Road User Cost:", total_road_user_cost)  # INR
        return total_road_user_cost
    
    # 5. Called on next from bridge_and_traffic_data.py
    def additional_carbon_emission_cost(self, data: List) -> float:
        total_vehicles_affected = 0
        for i in range(6,11):
            total_vehicles_affected += float(data[i])

        reroute_distance = float(data[1])

        additional_carbon_emission_component = AdditionalCarbonEmissionCost(
            vehicles_affected=total_vehicles_affected,
            reroute_distance=reroute_distance,
            co2_emission_per_km=0.1213,
            carbon_cost=self.carbon_cost
        )
        print("\nAdditional Carbon Emission Cost:", additional_carbon_emission_component.calculate_cost())  # INR
        return additional_carbon_emission_component.calculate_cost()

    # 6. Called on next from maintainance_repair_data.py
    def periodic_maintainance_cost(self, data: List, total_initial_cost) -> float:
        maintenance_cost_rate = PeriodicMaintenanceCost(
            maintenance_cost_rate=float(data[0]),
            construction_cost=total_initial_cost,
            discount_rate=0.0425,
            period=float(data[3]),
            design_life=50.0
        )
        print("\nPeriodic Maintenance Cost:", maintenance_cost_rate.calculate_cost())  # INR

        return maintenance_cost_rate.calculate_cost()
    
    # 7. Periodic Maintenance Carbon Emission Cost Calculation (Concrete only)
    def periodic_maintainnce_carbon_emission_cost(self, data: List):
        unit_conversions = {
            "cum": 2549.25,
            "kg": 1.0,
            "mt": 1000.0,
            "rmt": 1.0,
            "sqm": 1.0,
            "ltr": 1.0
        }

        # Get carbon emission data from the database
        c_data = self.get_carbon_emission_data()

        maintenance_concrete_emission_factor = 0
        maintenance_concrete_kg = 0
        for item in c_data:
            type = item.get(KEY_TYPE)
            if type[-8:].lower() == "concrete":
                qty = item.get(KEY_QUANTITY)
                unit = item.get(KEY_UNIT_M3)
                # convert quantity to kg
                qty = qty * unit_conversions.get(unit.lower())
                maintenance_concrete_emission_factor = item.get(KEY_CARBON_EMISSION_FACTOR)
                maintenance_concrete_kg += qty            

        maintenance_carbon_cost = 6.3936
        maintenance_discount_rate = 0.0425
        maintenance_period = float(data[3])
        maintenance_design_life = 50.0
        periodic_maintenance_concrete_carbon_component = PeriodicMaintenanceCarbonCost(
            material_quantity=maintenance_concrete_kg,
            carbon_emission_factor=maintenance_concrete_emission_factor,
            carbon_cost=maintenance_carbon_cost,
            discount_rate=maintenance_discount_rate,
            period=maintenance_period,
            design_life=maintenance_design_life
        )
        print("\nPeriodic Maintenance Carbon Emission Cost (Concrete only):", periodic_maintenance_concrete_carbon_component.calculate_cost())  # INR
        return periodic_maintenance_concrete_carbon_component.calculate_cost()

    # 8. Annual Routine Inspection Cost Calculation
    def routine_inspection_cost(self, total_initial_construction_cost: float) -> float:

        inspection_discount_rate = 0.0425
        inspection_design_life = 50.0

        inspection_rate = 0.01
        inspection_period = 1.0

        inspection_component = RoutineInspectionCost(
            inspection_cost_rate=inspection_rate,  # Use inspection_rate as inspection cost rate
            construction_cost=total_initial_construction_cost,  # Always use total_initial_construction_cost
            discount_rate=inspection_discount_rate,
            design_life=inspection_design_life,
            period=inspection_period  # always annual
        )
        total_routine_inspection_cost = inspection_component.calculate_cost()
        print("\nTotal Routine Inspection Cost:", total_routine_inspection_cost)  # INR
        return total_routine_inspection_cost

    # 9. Repair and Rehabilitation Cost Calculation
    def repair_and_rehabilitation_cost(self, total_initial_construction_cost: float) -> float:
        repair_period = 30.0
        repair_cost_rate = 0.10

        discount_rate = 0.0425
        design_life = 50.0

        repair_component = RepairAndRehabilitationCost(
            repair_cost_rate=repair_cost_rate,
            construction_cost=total_initial_construction_cost,
            discount_rate=discount_rate,
            period=repair_period,
            design_life=design_life
        )
        print("\nRepair and Rehabilitation Cost:", repair_component.calculate_cost())  # INR
        return repair_component.calculate_cost()
    
    # 10. Demolition and Disposal Cost Calculation
    def demolition_and_disposal_cost(self, data: List, total_initial_construction_cost: float) -> float:
        demolition_discount_rate = 0.0425
        demolition_design_life = 50.0
        demolition_rate = float(float(data[0])/100)  # e.g., 0.05 for 5%

        demolition_component = DemolitionCost(
            demolition_rate=demolition_rate,
            construction_cost=total_initial_construction_cost,
            discount_rate=demolition_discount_rate,
            design_life=demolition_design_life
        )
        print("\nDemolition and Disposal Cost:", demolition_component.calculate_cost())  # INR
        return demolition_component.calculate_cost()

    # 11. Recycling Cost Calculation
    def recycling_cost(self, data: List) -> float:
        scrap_value = float(data[1])
        recycling_design_life = 50.0
        scrap_rate = 0.98

        discount_rate = 0.0425

        user_input_steel_quantity_mt = 0.0

        recycling_component = RecyclingCost(
            scrap_value=scrap_value,
            quantity=user_input_steel_quantity_mt,
            scrap_rate=scrap_rate,
            discount_rate=discount_rate,
            design_life=recycling_design_life
        )
        print("\nRecycling Cost (user-input steel only):", recycling_component.calculate_cost())  # INR
        return recycling_component.calculate_cost()

    # 12. Reconstruction Cost Calculation 
    def reconstruction_cost(self, initial_construction_cost: float,
                            demolition_cost: float,
                            carbon_emission_cost: float,
                            time_cost: float,
                            roaduser_cost: float,
                            rerouting_carbon_cost: float) -> float:

        reconstruction_cost = initial_construction_cost
        demolition_cost = demolition_cost
        reconstruction_carbon_cost = carbon_emission_cost
        reconstruction_time_cost = time_cost
        reconstruction_roaduser_cost = roaduser_cost
        reconstruction_rerouting_carbon_cost = rerouting_carbon_cost
        reconstruction_design_life = 50.0

        reconstruction_result = 0
        analysis_period = 75.0

        design_life = 50.0
        discount_rate = 0.0425

        if analysis_period > design_life:
            reconstruction_component = ReconstructionCost(
                demolition_cost=demolition_cost,
                reconstruction_cost=reconstruction_cost,
                reconstruction_carbon_cost=reconstruction_carbon_cost,
                reconstruction_time_cost=reconstruction_time_cost,
                reconstruction_roaduser_cost=reconstruction_roaduser_cost,
                reconstruction_rerouting_carbon_cost=reconstruction_rerouting_carbon_cost,
                design_life=reconstruction_design_life,
                discount_rate=discount_rate
            )
            reconstruction_result = reconstruction_component.calculate_cost()
        else:
            reconstruction_result = 0
        print("\nReconstruction Cost:", reconstruction_result)  # INR
        return reconstruction_result
        
        