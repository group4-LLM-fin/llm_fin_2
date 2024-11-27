import os
import re
import openai
import json
import yaml
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from langchain.chat_models import ChatOpenAI
import tiktoken
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
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
inspector = inspect(sql_engine)

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

class GetAnswer:
    def __init__(self, model="gpt-4o-mini", engine=None, db_structure=None, acc_name=None):
        self.model = model
        self.llm = ChatOpenAI(model=model)
        self.sql_engine = engine
        self.sql_database = SQLDatabase(engine=engine)
        self.db_structure = db_structure
        self.acc_name = acc_name

#Lower name để tìm đc, embedding name
    def chain_of_thought_prompt(self, question):
        prompt = f"""
    Bạn là một chuyên gia phân tích tài chính chuyên sâu. Hãy phân tích câu hỏi dưới đây và thực hiện các bước để trả lời chính xác và chi tiết.

    Câu hỏi: "{question}"

    Bước 1: Xác định loại vấn đề cần phân tích và chia nhỏ vấn đề
    - Dịch câu hỏi sang tiếng anh
    - Phân tích yêu cầu và chia nhỏ bài toán: [Xác định các vấn đề cụ thể cần được phân tích từ câu hỏi, chẳng hạn như các chỉ số tài chính hoặc thông tin tài sản liên quan]
    - Từ đó, hãy tạo 1 danh sách với các câu lệnh nhỏ hơn với các vấn đề nhỏ đã được chia
    Ví dụ: ['Hãy tìm lợi nhuận sau thuế và tổng vốn rồi tính tỷ lệ ROE rồi tìm ngân hàng có ROE lớn nhất năm 2024 quý 2","Hãy tìm tổng tài sản của ACB năm 2024 quý 2"]

    Bước 2: Xác định thông tin cơ bản cần truy vấn từ vấn đề ở Bước 1
    - Tên công ty: [Liệt kê rõ những công ty được đề cập, ví dụ: BIDV, Vietcombank, ACB]
    Lưu ý: Luôn quy chuẩn từ Ngân hàng về NH. Ví dụ: 'Ngân hàng Việt Nam Thịnh Vượng' thành 'NH Việt Nam Thịnh Vượng'
    - Năm tài chính: [Ghi rõ năm tài chính cần phân tích, ví dụ: 2024]
    - Kỳ báo cáo: [Xác định kỳ báo cáo cụ thể, chẳng hạn quý 1, quý 2, quý 3, quý 4]
    - Mục cụ thể trong báo cáo: [Dựa vào các vấn đề đã được chia nhỏ, xác định rõ mục cần tìm trong báo cáo tài chính. Ví dụ: doanh thu, lợi nhuận ròng, tổng tài sản, ROE (Return on Equity). Nếu liên quan đến các chỉ số tài chính, xác định các thành phần cụ thể để tính toán, ví dụ: lợi nhuận sau thuế, vốn chủ sở hữu]
    - Loại báo cáo: [Xác định rõ loại báo cáo tài chính cần thiết, chẳng hạn Bảng cân đối kế toán, Báo cáo kết quả kinh doanh, Báo cáo lưu chuyển tiền tệ]

    Bước 3: Trả về câu truy vấn SQL dựa trên các thông tin đã xác định ở bước 1, 2
    - Với từng vấn đề trong danh sách trên, hãy tạo từng câu truy vấn sql cho từng vấn đề nhỏ
    - Cấu trúc database của bạn: {self.db_structure}
    - Danh sách tên các tài khoản có sẵn: {json.dumps(self.acc_name)}
    Đây là ví dụ: {self.load_example()}

    Bước 4: Giải thích và kiểm tra lại lỗi truy vấn SQL
    - Với từng vấn đề trong danh sách trên, hãy giải thích lại lệnh truy vấn.
    - Sau khi giải thích, hãy đối chiếu lại với yêu cầu của câu hỏi và xác nhận câu truy vấn đấy thỏa mãn câu hỏi chưa
    - Nếu đúng thì xác nhận và chuyển sang bước 5, nếu sai thì hãy sửa lại câu truy vấn đấy bằng cách thực hiện lại từ bước 1

    Bước 5: Ghi lại câu truy vấn SQL cuối cùng 
    - Sau khi đảm bảo các câu truy vấn đã đúng, Luôn viết lại câu truy vấn theo fomart sau:
   ```sql[câu truy vấn SQL chính xác]```
    Lưu ý: 
    - Chỉ sử dụng dữ liệu từ database đã kết nối và đảm bảo truy vấn chính xác từng chỉ số tài chính được yêu cầu.
    - Hầu hết các tên ngân hàng viết tắt đều ở symbol, nếu không được hãy thử sang abbreviation nếu câu hỏi vẫn yêu cầu tên viết tắt. 
    - bankname chứa tên tiếng việt, banknameng chứa tên tiếng anh
    - Với những câu hỏi tìm số tài khoản chung hoặc tìm tài khoản cấp X mà không đề cập đến thời gian/ngân hàng, hãy tìm trong bảng ACCNO
    - Bậc của số tài khoản được quyết định theo độ dài. 1 là cao nhất, càng dài càng thấp.(Ví dụ: tài khoản 10, 11, 12 là tài khoản con của 1)
    - Những câu hỏi liệt kê, Không tự động giới hạn kết quả, hãy liệt kê hết.
    - Luôn đảm bảo những câu query SQL phải trả kết quả về.
    Hãy làm tuần tự từ bước 1 và trả lời bằng tiếng việt
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

        # total_input_tokens = 0
        # total_output_tokens = 0

        try:
            start_time = time.time()

            # Step 1: Calculate tokens for the question
            prompt_cot = self.chain_of_thought_prompt(question)
            # input_tokens_question = self.get_token_usage(prompt_cot)
            # total_input_tokens += input_tokens_question
            
            # print(f"Input tokens for question: {input_tokens_question}")

            # Step 2: Generate SQL queries from the question
            sql_queries = self.get_sql_query(question)
            # input_tokens_sql = sum(self.get_token_usage(query) for query in sql_queries)
            # total_input_tokens += input_tokens_sql
            # print(f"Input tokens for SQL queries: {input_tokens_sql}")

            if not sql_queries:
                raise ValueError("Failed to generate SQL query from the question.")

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
            # output_tokens_answer = self.get_token_usage(answer)
            # total_output_tokens += output_tokens_answer
            # print(f"Output tokens for answer: {output_tokens_answer}")

            # Total tokens
            # print(f"Total token:{total_input_tokens+total_output_tokens}")
            # end_time = time.time()  # End timing
            # execution_time = end_time - start_time
            # print(f"Execution time for question: {execution_time:.2f} seconds")


            return answer

        except Exception as e:
            print(f"Error: {e}")
            return None

# message = 'Dòng tiền vào từ hoạt động kinh doanh quý nào là cao nhất của MBB trong năm 2024, và lý do là gì?'
# text2sql_instance = GetAnswer(model="gpt-4o-mini", engine=sql_engine, db_structure=db_structure_data, acc_name=acc_name)
# try:
#     final_answer = text2sql_instance.get_result(message)
#     if final_answer:
#         print(final_answer)
# except KeyError as e:
#     print("Error:", e)


