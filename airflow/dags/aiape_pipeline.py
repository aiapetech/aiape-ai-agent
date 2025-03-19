import os
import sys
from datetime import datetime 
from airflow import DAG
from airflow.operators.python import PythonOperator, ExternalPythonOperator
cwd = os.getcwd()
sys.path.append(cwd)
sys.path.append('/home/azureuser/data/datawarehouse')
sys.path.append(f'{cwd}/../data/')
# # Set up import paths
# def setup_import_paths():
#     cwd = os.getcwd()
#     sys.path.append(f'{cwd}/../')
#     #sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# setup_import_paths()
# from get_data import get_daily_data
from airflow.decorators import dag, task

default_args = {
    'owner': 'Bao',
    'depends_on_past': False,
    'email': ['hoquocbao93@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'start_date': datetime(2025, 3, 7),
    
}

with DAG(
    dag_id='ai_api_pipeline',
    default_args=default_args,
    description='AI APE pipeline',
    schedule_interval='0 */3 * * *',
    catchup=False,
    tags=["SIGHTSEA","AI"]
) as dag:
    PYTHON_PATH = "~/miniconda3/envs/sightsea-ai-demo/bin/python"
    from data.aipe_pipeline import AIPEPipeline
    aipae_pipeline = AIPEPipeline(datetime.now())

    extract_most_mentioned_project_name = PythonOperator(
        task_id='extract_most_mentioned_project_name',
        python_callable=aipae_pipeline.extract_most_mentioned_project_name ,
        provide_context=True,
        dag=dag,
    )
    process_data = PythonOperator(
        task_id='process_data',
        python_callable=aipae_pipeline.process_data,
        provide_context=True,
        dag=dag,
    )
    generate_x_post = PythonOperator(
        task_id='generate_x_post',
        python_callable=aipae_pipeline.generate_x_post,
        provide_context=True,
        dag=dag,
    )
    post_to_x = PythonOperator(
        task_id='post_to_x',
        python_callable=aipae_pipeline.post_to_x,
        provide_context=True,
        dag=dag,
    )
    extract_most_mentioned_project_name >> process_data >> generate_x_post >> post_to_x
if __name__ == "__main__":
    dag.test()