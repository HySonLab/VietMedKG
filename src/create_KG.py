
from py2neo import Graph, Node, Relationship
import pandas as pd

def clear_graph():
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    graph.run(query)
    print("Graph has been cleared...")

graph = Graph("bolt://54.242.247.141:7687", auth=("neo4j", "deputy-corks-silks")) 
clear_graph()

df_cn = pd.read_csv('../data/data_vie/data_translated.csv', encoding="utf-8")

for i, row in df_cn.iterrows():
    # if i <= 10: continue
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

    disease_node = Node("BỆNH", tên=disease_name, mô_tả=disease_description, loại_bệnh=disease_category, nguyên_nhân=disease_cause, đối_tượng_dễ_mắc_bệnh=people_easy_get)
    graph.merge(disease_node, "BỆNH", "tên")

    treatment_node = Node("ĐIỀU TRỊ", tên=f"Điều trị {disease_name}", phương_pháp=cure_method, khoa_điều_trị=cure_department, tỉ_lệ_chữa_khỏi=cure_probability)
    graph.merge(treatment_node, "ĐIỀU TRỊ", "tên")
    cured_rela = Relationship(disease_node, "ĐƯỢC CHỮA BỞI", treatment_node)
    graph.create(cured_rela)

    symptom_node = Node("TRIỆU CHỨNG", tên=f"Triệu chứng của {disease_name}", triệu_chứng=disease_symptom, kiểm_tra=check_method)
    graph.merge(symptom_node, "TRIỆU CHỨNG", "tên")
    has_rela = Relationship(disease_node, "CÓ", symptom_node)
    graph.create(has_rela)

    medication_node = Node("THUỐC", tên=f"Thuốc cho {disease_name}", thuốc_phổ_biến=drug_common, thông_tin_thuốc=drug_detail, đề_xuất_thuốc=drug_recommend)
    graph.merge(medication_node, "THUỐC", "tên")
    prescribed_rela = Relationship(disease_node, "ĐƯỢC KÊ ĐƠN", medication_node)
    graph.create(prescribed_rela)

    nutrition_node = Node("LỜI KHUYÊN", tên=f"Lời khuyên cho {disease_name}", nên_ăn_thực_phẩm_chứa=nutrition_do_eat, đề_xuất_món_ăn=nutrition_recommend_meal, không_nên_ăn_thực_phẩm_chứa=nutrition_not_eat, cách_phòng_tránh=disease_prevention)
    graph.merge(nutrition_node, "LỜI KHUYÊN", "tên")
    treated_rela = Relationship(disease_node, "ĐIỀU TRỊ VÀ PHÒNG TRÁNH CÙNG", nutrition_node)
    graph.create(treated_rela)

    if associated_disease:
        if isinstance(associated_disease, str) and not '[' in associated_disease:
            associated_disease_description = None
            associated_disease_category = None
            associated_disease_prevention = None
            associated_disease_cause = None
            associated_disease_symptom = None
            associated_people_easy_get = None
            associated_disease_node = Node("BỆNH", tên=associated_disease, mô_tả=associated_disease_description, loại_bệnh=associated_disease_category, nguyên_nhân=associated_disease_cause, đối_tượng_dễ_mắc_bệnh=associated_people_easy_get)
            graph.merge(associated_disease_node, "BỆNH", "tên")

            has_associated_rela = Relationship(disease_node, "ĐI KÈM VỚI BỆNH", associated_disease_node)
            graph.create(has_associated_rela)
            continue
        try: 
            if isinstance(eval(associated_disease), list):
                associated_disease_list =  eval(associated_disease)
                for associated_disease_name in associated_disease_list:
                    associated_disease_row = df_cn[df_cn["disease_name"] == associated_disease_name]
                    if not associated_disease_row.empty:
                        associated_disease_info = associated_disease_row.iloc[0]
                        (
                            associated_disease_name, associated_disease_description, associated_disease_category,
                            associated_disease_prevention, associated_disease_cause, associated_disease_symptom,
                            associated_people_easy_get, _, associated_cure_method, associated_cure_department,
                            associated_cure_probability, associated_check_method, associated_nutrition_do_eat,
                            associated_nutrition_not_eat, associated_nutrition_recommend_meal, associated_drug_recommend,
                            associated_drug_common, associated_drug_detail
                        ) = associated_disease_info
                    else: 
                
                    
                        associated_disease_description = None
                        associated_disease_category = None
                        associated_disease_prevention = None
                        associated_disease_cause = None
                        associated_disease_symptom = None
                        associated_people_easy_get = None
                    associated_disease_node = Node("BỆNH", tên=associated_disease_name, mô_tả=associated_disease_description, loại_bệnh=associated_disease_category, nguyên_nhân=associated_disease_cause, đối_tượng_dễ_mắc_bệnh=associated_people_easy_get)
                    graph.merge(associated_disease_node, "BỆNH", "tên")
                    has_associated_rela = Relationship(disease_node, "ĐI KÈM VỚI BỆNH", associated_disease_node)
                    graph.create(has_associated_rela)
        except: 
            pass 
    print("DONE", i)                
    
    