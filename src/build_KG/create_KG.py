
from py2neo import Graph, Node, Relationship
import pandas as pd

def clear_graph():
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    graph.run(query)
    print("Graph has been cleared...")

graph = Graph("bolt://44.211.183.59:7687", auth=("neo4j", "blocks-hoop-analyzers")) 
clear_graph()

df_cn = pd.read_csv('raw_data.csv', encoding="utf-8")

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

    disease_node = Node("Disease", name=disease_name, description=disease_description, category=disease_category, prevention=disease_prevention, cause=disease_cause, people_easy_get=people_easy_get)
    graph.merge(disease_node, "Disease", "name")

    treatment_node = Node("Treatment", name=f"{disease_name}'s treatment", treatment_method=cure_method, treatment_department=cure_department, treatment_prob=cure_probability)
    graph.merge(treatment_node, "Treatment", "name")
    cured_rela = Relationship(disease_node, "IS_CURED_BY", treatment_node)
    graph.create(cured_rela)

    symptom_node = Node("Symptom", name=f"{disease_name}'s symptom", symptom=disease_symptom, check_body=check_method)
    graph.merge(symptom_node, "Symptom", "name")
    has_rela = Relationship(disease_node, "HAS", symptom_node)
    graph.create(has_rela)

    medication_node = Node("Medication", name=f"{disease_name}'s medication", drug_common=drug_common, drug_detail=drug_detail, drug_recommend=drug_recommend)
    graph.merge(medication_node, "Medication", "name")
    prescribed_rela = Relationship(disease_node, "IS_PRESCRIBED_WITH", medication_node)
    graph.create(prescribed_rela)

    nutrition_node = Node("Nutrition", name=f"Nutrition for {disease_name}", do_eat=nutrition_do_eat, recommend_meal=nutrition_recommend_meal, not_eat=nutrition_not_eat)
    graph.merge(nutrition_node, "Nutrition", "name")
    treated_rela = Relationship(disease_node, "IS_TREATED_WITH", nutrition_node)
    graph.create(treated_rela)

    if associated_disease:
        if isinstance(eval(associated_disease), list):
            associated_disease_list =  eval(associated_disease)
            for associated_disease_name in associated_disease_list:
                print("ýe")
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
                    (
                        associated_disease_name, associated_disease_description, associated_disease_category,
                        associated_disease_prevention, associated_disease_cause, associated_disease_symptom,
                        associated_people_easy_get, _, associated_cure_method, associated_cure_department,
                        associated_cure_probability, associated_check_method, associated_nutrition_do_eat,
                        associated_nutrition_not_eat, associated_nutrition_recommend_meal, associated_drug_recommend,
                        associated_drug_common, associated_drug_detail
                    ) = None
                associated_disease_node = Node("Disease", name=associated_disease_name, description=associated_disease_description, category=associated_disease_category, prevention=associated_disease_prevention, cause=associated_disease_cause, people_easy_get=associated_people_easy_get)
                graph.merge(associated_disease_node, "Disease", "name")

                has_associated_rela = Relationship(disease_node, "HAS_ASSOCIATED", associated_disease_node)
                graph.create(has_associated_rela)
                    
    
    