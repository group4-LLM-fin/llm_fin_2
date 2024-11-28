import os
import re
import openai
import json
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from langchain.chat_models import ChatOpenAI
import tiktoken
import yaml
from database.vectorDB import VectorDB
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import ast
import time
from langchain_openai import ChatOpenAI
load_dotenv(override = True)

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

db_config = {
    'user': user,
    'password': password,
    'host': host,
    'port': port,
    'dbname': dbname
}
db = VectorDB(**db_config)

sql_query_acc_name = """
SELECT accname, accno, report
FROM "ACCNO";
"""
try:
    # Execute the query
    cursor.execute(sql_query_acc_name)
    
    # Fetch the results
    acc_name = cursor.fetchall()
except psycopg2.Error as e:
    print(f"Database error: {e}")
    connection.rollback()

with open('db_structure.yaml', 'r', encoding='utf-8') as file:
    db_structure_data = yaml.safe_load(file)

class GetAnswer:
    def __init__(self, model="gpt-4o-mini", engine=None, db_structure=None, acc_name=None, db = None):
        self.model = model
        self.llm = ChatOpenAI(model=model)
        self.sql_engine = engine
        self.sql_database = SQLDatabase(engine=engine)
        self.db_structure = db_structure
        self.acc_name = acc_name
        self.db = db

    def extract_bank_name(self, question):
        prompt = f"""
        Bạn là một chuyên gia phân tích tài chính với câu hỏi liên quan đến ngân hàng. Hãy trích xuất chỉ tên ngân hàng từ câu hỏi sau, luôn cho vào trong list, không thêm thắt ghi chú, nếu không có, trả về none:
        Câu hỏi: "{question}"
        Tên ngân hàng
        """
        # Change the input to a string
        response = self.llm.invoke(prompt)  # Pass the prompt directly as a string
        return response.content.strip()
    
    def query_bank_to_symbol(self, question):
        try:
            bank_names_str = self.extract_bank_name(question)
            if bank_names_str == "[]":
                return []  # Return empty list if no bank names found
            query_texts = ast.literal_eval(bank_names_str)
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing bank names: {e}")
            return []  # Return an empty list if parsing fails

        bank_list = []
        for bank in query_texts:
            if not bank:
                print("Không có tên ngân hàng để truy vấn.")
                continue

            try:
                database = self.db
                # Query with L2 distance
                result = database.query_with_distance_bank(
                    bank, 
                    table_name="BANK", 
                    distance='L2',
                    columns=["symbol"], 
                    limit=5
                )
                bank_list.append(result[0][0]['symbol'])
            except Exception as e:
                print(f"Đã xảy ra lỗi khi truy vấn cho ngân hàng '{bank}': {e}")
        
        return bank_list

#Lower name để tìm đc, embedding name
    def chain_of_thought_prompt(self, question):
        prompt = f"""
     Bạn là một chuyên gia phân tích tài chính chuyên sâu. Hãy phân tích câu hỏi dưới đây và thực hiện các bước để trả lời chính xác và chi tiết.

    **Câu hỏi**: "{question}"

    ### Bước 1: Xác định loại vấn đề cần phân tích và chia nhỏ vấn đề
    - **Dịch câu hỏi sang tiếng Anh**.
    - **Phân tích yêu cầu** và chia nhỏ bài toán: [Xác định các vấn đề cụ thể cần được phân tích từ câu hỏi, chẳng hạn như các chỉ số tài chính hoặc thông tin tài sản liên quan].
    - Tạo danh sách các vấn đề cụ thể cần giải quyết, ví dụ:
      - ['Tìm lợi nhuận sau thuế và tổng vốn, sau đó tính tỷ lệ ROE và tìm ngân hàng có ROE lớn nhất trong quý 2 năm 2024', 
      - 'Tìm tổng tài sản của ACB trong quý 2 năm 2024'].

    ### Bước 2: Xác định thông tin cơ bản cần truy vấn từ vấn đề ở Bước 1
    - **Chuyển tên ngân hàng thành symbol trong bảng BANK**:
      - Sử dụng danh sách đã được ánh xạ từ tên ngân hàng sang symbol: {self.query_bank_to_symbol(question)}.
      - Xem xét các symbol gần đúng để xác định Symbol ngân hàng cần tìm.
    - **Năm tài chính**: [Ví dụ: 2024].
    - **Kỳ báo cáo**: [Ví dụ: quý 1, quý 2, quý 3, quý 4].
    - **Mục cụ thể trong báo cáo**: [Dựa vào bài toán đã chia nhỏ, xác định rõ mục cần truy vấn, ví dụ: doanh thu, lợi nhuận ròng, ROE].
    - **Loại báo cáo tài chính**: [Xác định rõ loại báo cáo cần thiết, ví dụ: bảng cân đối kế toán, báo cáo kết quả kinh doanh].

    ### Bước 3: Tạo câu truy vấn SQL cho từng vấn đề
    - Với mỗi vấn đề từ Bước 1 và thông tin bước 2, tạo một câu truy vấn SQL tương ứng.
    - **Cấu trúc database**: {self.db_structure}.
    - **Danh sách tên các tài khoản có sẵn**: {json.dumps(self.acc_name)}.
    - Ví dụ truy vấn: {self.load_example()}.

    ### Bước 4: Giải thích và kiểm tra lại lỗi truy vấn SQL
    - **Giải thích từng câu truy vấn SQL**:
      - Mô tả cách truy vấn thực hiện và lý do phù hợp với yêu cầu bài toán.
    - **Kiểm tra lại**:
      - So sánh câu truy vấn với yêu cầu của câu hỏi, xác định xem nó đã chính xác chưa.
      - Nếu sai, sửa lại câu truy vấn bằng cách quay lại từ Bước 1.

    ### Bước 5: Ghi lại câu truy vấn SQL cuối cùng
    - Sau khi đảm bảo các câu truy vấn chính xác:
      - Ghi lại câu truy vấn SQL theo định dạng:
        ```sql
        [Câu truy vấn SQL chính xác]
        ```
      - **Lưu ý**:
        - Chỉ sử dụng dữ liệu từ database đã kết nối.
        - Với tên ngân hàng viết tắt, ưu tiên `symbol` hoặc `abbreviation` nếu cần.
        - Sử dụng bảng `ACCNO` để tìm số tài khoản chung khi không có thông tin thời gian/ngân hàng cụ thể.
        - Với các câu hỏi liệt kê, không giới hạn số kết quả.

    Hãy làm tuần tự từ Bước 1 và trả lời bằng tiếng Việt.
    """
        return prompt
    
    def get_token_usage(self, text):
        """
        Returns the estimated token usage for the given text.
        """
        encoding = tiktoken.encoding_for_model(self.model)  # Ensure the model is specified

        # Calculate the number of tokens for the text
        return len(encoding.encode(text))
    
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
                
        return results
    

    def get_result(self, question):
        system_role_template = """
        Given the following user question, corresponding SQL queries, and SQL results, provide a detailed answer.
        Question: {question}
        SQL Queries: {queries}
        SQL Results: {results}
        Answer:
        """

        total_input_tokens = 0
        total_output_tokens = 0

        try:
            start_time = time.time()  # Ensure this is correct
            # Step 1: Calculate tokens for the question
            prompt_cot = self.chain_of_thought_prompt(question)  # Pass bank_symbol here
            input_tokens_question = self.get_token_usage(prompt_cot)
            total_input_tokens += input_tokens_question
            
            print(f"Input tokens for question: {input_tokens_question}")

            # Step 2: Generate SQL queries from the question
            sql_queries = self.get_sql_query(question)
            if sql_queries is None:
                raise ValueError("Failed to generate SQL query from the question.")

            input_tokens_sql = sum(self.get_token_usage(query) for query in sql_queries)
            total_input_tokens += input_tokens_sql
            print(f"Input tokens for SQL queries: {input_tokens_sql}")

            # Step 3: Execute all SQL queries and get results
            sql_results = self.execute_sql_queries(sql_queries)

            # Step 4: Format prompt and create the final answer
            answer_input = {
                "question": question,
                "queries": sql_queries,
                "results": sql_results
            }
            answer_prompt = PromptTemplate.from_template(system_role_template)
            answer_chain = answer_prompt | self.llm | StrOutputParser()

            # Step 5: Generate and return the answer
            answer = answer_chain.invoke(answer_input)
            output_tokens_answer = self.get_token_usage(answer)
            total_output_tokens += output_tokens_answer
            print(f"Output tokens for answer: {output_tokens_answer}")

            # Total tokens
            print(f"Total token: {total_input_tokens + total_output_tokens}")
            end_time = time.time()  # End timing
            execution_time = end_time - start_time
            print(f"Execution time for question: {execution_time:.2f} seconds")

            return answer

        except Exception as e:
            print(f"Error: {e}")
            return None

# message = 'Tổng tài sản của MBBank năm 2024 quý 2'
# text2sql_instance = GetAnswer(model="gpt-4o-mini", engine=sql_engine, db_structure=db_structure_data, acc_name=acc_name, db = db)
# try:
#     final_answer = text2sql_instance.get_result(message)
#     if final_answer:
#         print(final_answer)
# except KeyError as e:
#     print("Error:", e)



