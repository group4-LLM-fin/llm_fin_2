import os
import openai
import json
import psycopg2
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_openai import ChatOpenAI
from langchain.chat_models import ChatOpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

user = os.getenv('USER')
host = os.getenv('HOST')
port = os.getenv('PORT')
password = os.getenv('PASSWORD')
dbname = os.getenv('DB1')

sqlalchemy_connection_url = URL.create(
    "postgresql+psycopg2",
    username=user,
    password=password,
    host=host,
    database=dbname,
)
# Set up PostgreSQL connection
connection = psycopg2.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=user,
    password=password
)
cursor = connection.cursor()
sql_engine = create_engine(sqlalchemy_connection_url)
inspector = inspect(sql_engine)

db_structure = {
    'tables': inspector.get_table_names(),
}
db_structure.update({
    table: {
        'columns': [{'name': column['name'], 'type': str(column['type'])} for column in inspector.get_columns(table)]
    } for table in db_structure['tables']
})


sql_query_acc_name = """
SELECT accname
FROM "ACCNO"
"""
cursor.execute(sql_query_acc_name)
acc_name = cursor.fetchall()

class GetAnswer:
    def __init__(self, model="gpt-4o-mini", engine=None, db_structure=None, acc_name=None):
        self.llm = ChatOpenAI(model=model)
        self.sql_engine = engine
        self.sql_database = SQLDatabase(engine=engine)
        self.db_structure = db_structure
        self.acc_name = acc_name

    def chain_of_thought_prompt(self, question):
        prompt = f"""
    Bạn là một chuyên gia phân tích tài chính chuyên sâu. Hãy phân tích câu hỏi dưới đây và thực hiện các bước để trả lời chính xác và chi tiết.

    Câu hỏi: "{question}"

    Bước 1: Xác định loại vấn đề cần phân tích và chia nhỏ vấn đề
    - Phân tích yêu cầu và chia nhỏ bài toán: [Xác định các vấn đề cụ thể cần được phân tích từ câu hỏi, chẳng hạn như các chỉ số tài chính hoặc thông tin tài sản liên quan]
    - Từ đó, hãy tạo 1 danh sách với các câu lệnh nhỏ hơn với các vấn đề nhỏ đã được chia
    Ví dụ: ['Hãy tìm lợi nhuận sau thuế và tổng vốn rồi tính tỷ lệ ROE rồi tìm ngân hàng có ROE lớn nhất năm 2024 quý 2","Hãy tìm tổng tài sản của ACB năm 2024 quý 2"]

    Bước 2: Xác định thông tin cơ bản cần truy vấn từ vấn đề ở Bước 1
    - Tên công ty: [Liệt kê rõ những công ty được đề cập, ví dụ: BIDV, Vietcombank, ACB]
    - Năm tài chính: [Ghi rõ năm tài chính cần phân tích, ví dụ: 2024]
    - Kỳ báo cáo: [Xác định kỳ báo cáo cụ thể, chẳng hạn quý 1, quý 2, quý 3, hoặc "Cả năm". Nếu kỳ không được chỉ định rõ ràng, mặc định là "Cả năm"]
    - Mục cụ thể trong báo cáo: [Dựa vào các vấn đề đã được chia nhỏ, xác định rõ mục cần tìm trong báo cáo tài chính. Ví dụ: doanh thu, lợi nhuận ròng, tổng tài sản, ROE (Return on Equity). Nếu liên quan đến các chỉ số tài chính, xác định các thành phần cụ thể để tính toán, ví dụ: lợi nhuận sau thuế, vốn chủ sở hữu]
    - Loại báo cáo: [Xác định rõ loại báo cáo tài chính cần thiết, chẳng hạn Bảng cân đối kế toán, Báo cáo kết quả kinh doanh, Báo cáo lưu chuyển tiền tệ]

    Bước 3: Trả về câu truy vấn SQL dựa trên các thông tin đã xác định ở bước 1, 2
    - Với từng vấn đề trong danh sách trên, hãy tạo từng câu truy vấn sql cho từng vấn đề nhỏ
    - Cấu trúc database của bạn: {json.dumps(self.db_structure)}
    - Danh sách tên các tài khoản có sẵn: {self.acc_name}
    Đây là ví dụ: {self.load_example()}  
    
    Lưu ý: Chỉ sử dụng dữ liệu từ database đã kết nối và đảm bảo truy vấn chính xác từng chỉ số tài chính được yêu cầu.
    Hãy làm tuần tự từ bước 1
    """
        return prompt
    
    def load_example(self):
        """Loads the example text from example.txt."""
        with open('example.txt', 'r', encoding='utf-8') as file:
            return file.read()
        
    def get_sql_query(self, input_question):
        try:
            # Generate the prompt using the chain of thought method
            prompt_cot = self.chain_of_thought_prompt(input_question)
            # Create a chain to generate the SQL query
            sql_query_chain = create_sql_query_chain(self.llm, self.sql_database)
            # Invoke the chain and get the SQL query
            sql_query = sql_query_chain.invoke({"question": prompt_cot})
            # Extract the SQL query from the response
            return self.extract_sql_queries(sql_query)
        except Exception as e:
            print(f"Error generating SQL query: {e}")
            return None

    def extract_sql_queries(self, sql_query):
        """
        Extracts all SQL queries from the response and returns them in a list.
        """
        pattern = r"```sql\s*(.*?)\s*```"
        matches = re.findall(pattern, sql_query, re.DOTALL)
        # Ensure unique queries by converting to a set and back to a list
        return list(set(match.strip() for match in matches)) if matches else []

    def execute_sql_queries(self, sql_queries):
        """
        Execute each SQL query in the list and return the results in the order they were executed.
        """
        results = []  # List to store the results
        for query in sql_queries:
            try:
                # Execute the query using your database connection
                result = QuerySQLDataBaseTool(db=self.sql_database).run(query)
                results.append(result)  # Add the result to the list
            except Exception as e:
                print(f"Error executing query: {query}\nError: {e}")
                results.append(None)  # Add None if there is an error
                ##Thêm lệnh để quay tròn lại ko là bị chết ở đây(optional)
        return results
    

    def get_result(self, question):
        system_role_template = """
        Given the following user question, corresponding SQL query, and SQL result, answer the user question.
        Question: {question}
        SQL Query: {queries}
        SQL Result: {results}
        Answer:
        """

        try:
            # Generate the SQL query from the user question
            sql_queries = self.get_sql_query(question)
            if not sql_queries:
                raise ValueError("Failed to generate SQL query from the question.")

            # Execute all SQL queries and retrieve results
            sql_results = self.execute_sql_queries(sql_queries)

            # Format the prompt and generate the final answer
            answer_input = {
                "question": question,
                "queries": sql_queries,
                "results": sql_results
            }
            answer_prompt = PromptTemplate.from_template(system_role_template)
            answer_chain = answer_prompt | self.llm | StrOutputParser()

            # Generate and return the answer
            return answer_chain.invoke(answer_input)

        except Exception as e:
            print(f"Error: {e}")
            return None

# # Example usage
# message = "Tìm ngân hàng có tỷ lệ ROA lớn nhất quý 3 năm 2024 và đưa ra chỉ số ROA"
# text2sql_instance = GetAnswer(model="gpt-4o-mini", engine=sql_engine, db_structure=db_structure, acc_name=acc_name)

# try:
#     final_answer = text2sql_instance.get_result(message)
#     if final_answer:
#         print(final_answer)
# except KeyError as e:
#     print("Error:", e)

