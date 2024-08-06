from py2neo import Graph, Node, Relationship
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def uppercase_first_letter(text):
    if isinstance(text, str):
        return text.capitalize()  # Capitalize first letter of each word
    else:
        return text
    
def clear_graph():
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    graph.run(query)
    print("Graph has been cleared...")

def check_node_exists(graph, associated_disease):
    tên_bệnh = associated_disease.capitalize()
    query = """
    MATCH (n:BỆNH {tên_bệnh: $tên_bệnh})
    RETURN COUNT(n) > 0 AS node_exists
    """
    result = graph.run(query, tên_bệnh=tên_bệnh).data()
    return result[0]["node_exists"] if result else False

def process_row(row):
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

    if disease_name and disease_description and disease_category and disease_cause:
        # Create disease node
        disease_node = Node("BỆNH", tên_bệnh=disease_name, mô_tả_bệnh=disease_description, loại_bệnh=disease_category, nguyên_nhân=disease_cause)
        graph.merge(disease_node, "BỆNH", "tên_bệnh")

    if cure_method and cure_department and cure_probability:
        # Create treatment node and relationship
        treatment_node = Node("ĐIỀU TRỊ", tên_bệnh=disease_name, phương_pháp=cure_method, khoa_điều_trị=cure_department, tỉ_lệ_chữa_khỏi=cure_probability)
        graph.merge(treatment_node, "ĐIỀU TRỊ", "tên_bệnh")
        cured_rela = Relationship(disease_node, "ĐƯỢC CHỮA BỞI", treatment_node)
        graph.create(cured_rela)

    if disease_symptom and check_method and people_easy_get:
        # Create symptom node and relationship
        symptom_node = Node("TRIỆU CHỨNG", tên_bệnh=disease_name, triệu_chứng=disease_symptom, kiểm_tra=check_method, đối_tượng_dễ_mắc_bệnh=people_easy_get)
        graph.merge(symptom_node, "TRIỆU CHỨNG", "tên_bệnh")
        has_rela = Relationship(disease_node, "CÓ TRIỆU CHỨNG", symptom_node)
        graph.create(has_rela)

    if drug_recommend and drug_common and drug_detail:
        # Create medication node and relationship
        medication_node = Node("THUỐC", tên_bệnh=disease_name, thuốc_phổ_biến=drug_common, thông_tin_thuốc=drug_detail, đề_xuất_thuốc=drug_recommend)
        graph.merge(medication_node, "THUỐC", "tên_bệnh")
        prescribed_rela = Relationship(disease_node, "ĐƯỢC KÊ ĐƠN", medication_node)
        graph.create(prescribed_rela)

    if nutrition_do_eat and nutrition_not_eat and nutrition_recommend_meal and disease_prevention:
        # Create nutrition node and relationship
        nutrition_node = Node("LỜI KHUYÊN", tên_bệnh=disease_name, nên_ăn_thực_phẩm_chứa=nutrition_do_eat, đề_xuất_món_ăn=nutrition_recommend_meal, không_nên_ăn_thực_phẩm_chứa=nutrition_not_eat, cách_phòng_tránh=disease_prevention)
        graph.merge(nutrition_node, "LỜI KHUYÊN", "tên_bệnh")
        treated_rela = Relationship(disease_node, "ĐIỀU TRỊ VÀ PHÒNG TRÁNH CÙNG", nutrition_node)
        graph.create(treated_rela)

    if associated_disease:
        if isinstance(associated_disease, str) and not '[' in associated_disease:
            if check_node_exists(graph, uppercase_first_letter(associated_disease)):
                return
            associated_disease_description = None
            associated_disease_category = None
            associated_disease_cause = None
            if not df_cn[df_cn['disease_name'].str.lower() == associated_disease.lower()].empty:
                row = df_cn[df_cn['disease_name'].str.lower() == associated_disease.lower()].iloc[0]
                associated_disease_description = row['disease_description']
                associated_disease_category = row['disease_category']
                associated_disease_cause = row['disease_cause']
            associated_disease_node = Node("BỆNH", tên_bệnh=uppercase_first_letter(associated_disease), mô_tả_bệnh=associated_disease_description, loại_bệnh=associated_disease_category, nguyên_nhân=associated_disease_cause)
            graph.merge(associated_disease_node, "BỆNH", "tên_bệnh")
            has_associated_rela = Relationship(disease_node, "ĐI KÈM VỚI BỆNH", associated_disease_node)
            graph.create(has_associated_rela)
            return

        try:
            associated_disease = associated_disease.replace("[", "").replace("]", "")  # Remove square brackets if present
            associated_disease = [item.strip() for item in associated_disease.split(',')]

            if isinstance(associated_disease, list):
                for associated_disease_name in associated_disease:
                    associated_disease_row = df_cn[df_cn["disease_name"] == uppercase_first_letter(associated_disease_name)]
                    if not associated_disease_row.empty:
                        associated_disease_info = associated_disease_row.iloc[0]
                        (
                            associated_disease_name, associated_disease_description, associated_disease_category,
                            _, associated_disease_cause, _, _, _, _, _, _, _, _, _, _, _, _, _
                        ) = associated_disease_info
                    else:
                        associated_disease_description = None
                        associated_disease_category = None
                        associated_disease_cause = None
                    if check_node_exists(graph, uppercase_first_letter(associated_disease_name)):
                        continue
                    associated_disease_node = Node("BỆNH", tên_bệnh=uppercase_first_letter(associated_disease_name), mô_tả_bệnh=associated_disease_description, loại_bệnh=associated_disease_category, nguyên_nhân=associated_disease_cause)
                    graph.merge(associated_disease_node, "BỆNH", "tên_bệnh")
                    has_associated_rela = Relationship(disease_node, "ĐI KÈM VỚI BỆNH", associated_disease_node)
                    graph.create(has_associated_rela)
        except Exception as e:
            print(f"Error processing associated disease: {e}")

if __name__ == "__main__": 
    graph = Graph("bolt://54.237.191.131:7687", auth=("neo4j", "curvature-signals-flashlight"))
    clear_graph()
    df_cn = pd.read_csv(r'.\data\data_translated.csv', encoding="utf-8")
    num_workers = 4
    # Process each row in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_row, row) for index, row in df_cn.iterrows()]
        for future in as_completed(futures):
            try:
                future.result()  # Retrieve and handle exceptions if any
            except Exception as e:
                print(f"Error processing row: {e}")