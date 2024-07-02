from py2neo import Graph, Node, Relationship
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class DiseaseGraph:
    """
    A class to manage the creation and management of a Neo4j graph for disease data.
    """

    def __init__(self, uri, user, password):
        """
        Initialize the DiseaseGraph with Neo4j connection details.

        Parameters:
        uri (str): The URI for the Neo4j database.
        user (str): The username for Neo4j authentication.
        password (str): The password for Neo4j authentication.
        """
        self.graph = Graph(uri, auth=(user, password))
        self.df_cn = None

    def clear_graph(self):
        """
        Clear all nodes and relationships from the graph.
        """
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        self.graph.run(query)
        print("Graph has been cleared...")

    def create_nodes_and_relationships(self, row):
        """
        Create nodes and relationships in the graph from a DataFrame row.

        Parameters:
        row (pd.Series): A row of data from the DataFrame.
        """
        disease_name = row['disease_name']
        disease_description = row['disease_description']
        disease_category = row['disease_category']
        disease_prevention = row['disease_prevention']
        disease_cause = row['disease_cause']
        disease_symptom = row['disease_symptom']
        people_easy_get = row['people_easy_get']
        associated_disease = row['associated_disease']
        cure_method = row['cure_method']
        cure_department = row['cure_department']
        cure_probability = row['cure_probability']
        check_method = row['check_method']
        nutrition_do_eat = row['nutrition_do_eat']
        nutrition_not_eat = row['nutrition_not_eat']
        nutrition_recommend_meal = row['nutrition_recommend_eat']
        drug_recommend = row['drug_recommend']
        drug_common = row['drug_common']
        drug_detail = row['drug_detail']

        # Create Disease node
        if disease_name and disease_description and disease_category and disease_cause:
            disease_node = Node(
                "BỆNH", 
                tên_bệnh=disease_name, 
                mô_tả_bệnh=disease_description, 
                loại_bệnh=disease_category, 
                nguyên_nhân=disease_cause
            )
            self.graph.merge(disease_node, "BỆNH", "tên_bệnh")

        # Create Treatment node and relationship
        if cure_method and cure_department and cure_probability:
            treatment_node = Node(
                "ĐIỀU TRỊ",  
                tên_bệnh=disease_name, 
                phương_pháp=cure_method, 
                khoa_điều_trị=cure_department, 
                tỉ_lệ_chữa_khỏi=cure_probability
            )
            self.graph.merge(treatment_node, "ĐIỀU TRỊ", "tên_bệnh")
            cured_rela = Relationship(disease_node, "ĐƯỢC CHỮA BỞI", treatment_node)
            self.graph.create(cured_rela)

        # Create Symptom node and relationship
        if disease_symptom and check_method and people_easy_get:
            symptom_node = Node(
                "TRIỆU CHỨNG", 
                tên_bệnh=disease_name, 
                triệu_chứng=disease_symptom, 
                kiểm_tra=check_method, 
                đối_tượng_dễ_mắc_bệnh=people_easy_get
            )
            self.graph.merge(symptom_node, "TRIỆU CHỨNG", "tên_bệnh")
            has_rela = Relationship(disease_node, "CÓ TRIỆU CHỨNG", symptom_node)
            self.graph.create(has_rela)

        # Create Medication node and relationship
        if drug_recommend and drug_common and drug_detail:
            medication_node = Node(
                "THUỐC", 
                tên_bệnh=disease_name, 
                thuốc_phổ_biến=drug_common, 
                thông_tin_thuốc=drug_detail, 
                đề_xuất_thuốc=drug_recommend
            )
            self.graph.merge(medication_node, "THUỐC", "tên_bệnh")
            prescribed_rela = Relationship(disease_node, "ĐƯỢC KÊ ĐƠN", medication_node)
            self.graph.create(prescribed_rela)

        # Create Nutrition node and relationship
        if nutrition_do_eat and nutrition_not_eat and nutrition_recommend_meal and disease_prevention:
            nutrition_node = Node(
                "LỜI KHUYÊN", 
                tên_bệnh=disease_name, 
                nên_ăn_thực_phẩm_chứa=nutrition_do_eat, 
                đề_xuất_món_ăn=nutrition_recommend_meal, 
                không_nên_ăn_thực_phẩm_chứa=nutrition_not_eat, 
                cách_phòng_tránh=disease_prevention
            )
            self.graph.merge(nutrition_node, "LỜI KHUYÊN", "tên_bệnh")
            treated_rela = Relationship(disease_node, "ĐIỀU TRỊ VÀ PHÒNG TRÁNH CÙNG", nutrition_node)
            self.graph.create(treated_rela)

        # Create Associated Disease nodes and relationships
        if associated_disease:
            if isinstance(associated_disease, str) and not '[' in associated_disease:
                associated_disease_node = Node(
                    "BỆNH", 
                    tên_bệnh=associated_disease, 
                    mô_tả_bệnh="Không có thông tin", 
                    loại_bệnh="Không có thông tin", 
                    nguyên_nhân="Không có thông tin"
                )
                self.graph.merge(associated_disease_node, "BỆNH", "tên_bệnh")
                has_associated_rela = Relationship(disease_node, "ĐI KÈM VỚI BỆNH", associated_disease_node)
                self.graph.create(has_associated_rela)
            else:
                try:
                    associated_disease_list = eval(associated_disease)
                    for associated_disease_name in associated_disease_list:
                        associated_disease_row = self.df_cn[self.df_cn["disease_name"] == associated_disease_name]
                        if not associated_disease_row.empty:
                            associated_disease_info = associated_disease_row.iloc[0]
                            associated_disease_node = Node(
                                "BỆNH", 
                                tên_bệnh=associated_disease_info['disease_name'], 
                                mô_tả_bệnh=associated_disease_info['disease_description'], 
                                loại_bệnh=associated_disease_info['disease_category'], 
                                nguyên_nhân=associated_disease_info['disease_cause']
                            )
                        else:
                            associated_disease_node = Node(
                                "BỆNH", 
                                tên_bệnh=associated_disease_name, 
                                mô_tả_bệnh="Không có thông tin", 
                                loại_bệnh="Không có thông tin", 
                                nguyên_nhân="Không có thông tin"
                            )
                        self.graph.merge(associated_disease_node, "BỆNH", "tên_bệnh")
                        has_associated_rela = Relationship(disease_node, "ĐI KÈM VỚI BỆNH", associated_disease_node)
                        self.graph.create(has_associated_rela)
                except:
                    pass

    def process_row(self, row):
        """
        Process a single row of the DataFrame to create nodes and relationships.

        Parameters:
        row (pd.Series): A row of data from the DataFrame.

        Returns:
        str: A confirmation message indicating the completion of the row processing.
        """
        self.create_nodes_and_relationships(row)
        return f"DONE {row['disease_name']}"

    def load_data(self, csv_file):
        """
        Load data from a CSV file into a DataFrame.

        Parameters:
        csv_file (str): The path to the CSV file.
        """
        self.df_cn = pd.read_csv(csv_file, encoding="utf-8")

    def execute(self, csv_file):
        """
        Execute the process of clearing the graph, loading data, and creating nodes and relationships.

        Parameters:
        csv_file (str): The path to the CSV file.
        """
        self.clear_graph()
        self.load_data(csv_file)
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(tqdm(executor.map(self.process_row, [row for _, row in self.df_cn.iterrows()]), total=len(self.df_cn)))
        for result in results:
            print(result)


def main():
    """
    Main function to execute the disease graph creation.
    """
    uri = "bolt://3.84.13.206:7687"
    user = "neo4j"
    password = "whispers-probes-quartermaster"
    csv_file = '/home/dslab/code/tammy/benchmark/create_KG/translated_processed.csv'

    disease_graph = DiseaseGraph(uri, user, password)
    disease_graph.execute(csv_file)


if __name__ == "__main__":
    main()
