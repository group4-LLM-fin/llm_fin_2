import json
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
load_dotenv()
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_openai import ChatOpenAI
import re

class Quest2SQL:
    def __init__(self, model="gpt-4o-mini", engine=None, db_structure=None, acc_name=None):
        self.llm = ChatOpenAI(model=model)
        self.sql_engine = engine
        self.sql_database = SQLDatabase(engine=engine)
        self.db_structure = db_structure
        self.acc_name = acc_name

    def chain_of_thought_prompt(self, question):
        #Do lenh prompt kieu moi nen no ko work tot lam k hieu sao, truoc chay bang tieng viet lenh 
        # Creating a well-structured prompt with clear guidance
        prompt = f"""
        Bạn là một chuyên gia phân tích tài chính chuyên sâu. Hãy phân tích câu hỏi dưới đây và thực hiện các bước để trả lời chính xác.

        Câu hỏi: "{question}"

        Bước 1: Xác định loại vấn đề cần phân tích và chia nhỏ vấn đề
        - Phân tích yêu cầu và chia nhỏ bài toán: [Xác định các vấn đề cần phân tích từ câu hỏi]
        - Mục cụ thể trong báo cáo: [Từ những vấn để đã chia nhỏ ở trên, xác định mục cụ thể cần tìm trong báo cáo (ví dụ: doanh thu, lợi nhuận ròng, tổng tài sản). Nếu là các chỉ số tài chính, xác định thành phần cụ thể để tính toán]
        - Loại báo cáo: [Xác định loại báo cáo tài chính liên quan (Bảng cân đối kế toán, Báo cáo kết quả kinh doanh, Báo cáo lưu chuyển tiền tệ)]
        Ví dụ ở bước 1 về về tính thanh khoản của BID năm 2022:  
        - Thành phần cần tính toán:
        - Current Ratio: `Tổng Tài Sản Ngắn Hạn / Nợ Ngắn Hạn`
        - Quick Ratio: `(Tài Sản Ngắn Hạn - Hàng Tồn Kho) / Nợ Ngắn Hạn`
        - Cash Ratio: `(Tiền Mặt + Tài Sản Tương Đương Tiền) / Nợ Ngắn Hạn`
        Tất cả các mục được xác nhận trong ví dụ ở trong Balance_sheet
    
        Bước 2: Xác định thông tin cơ bản từ vấn đề ở bước 1
        - Tên công ty: [Xác định những tên công ty được đề cập]
        - Năm tài chính: [Xác định những năm tài chính được nhắc đến]
        - Kỳ báo cáo: [Xác định kỳ báo cáo cụ thể nếu có, nếu không mặc định là "Cả năm" (Ví dụ: 1, 2, "Cả năm", 'Nửa năm')]

        Bước 3: Trả về câu truy vấn SQL dựa trên các thông tin đã xác định ở bước 1, 2 và 3
        - Đây là cấu trúc database của bạn cần sử dụng: {json.dumps(self.db_structure)}
        - Đây là danh sách tên các tài khoản bạn cần {self.acc_name}. Hãy dựa trên đấy để tạo ra câu truy vấn SQL

        Bắt đầu với Bước 1 và làm theo từng bước trên để cung cấp câu trả lời chi tiết.
        Lưu ý: Chỉ được lấy dữ liệu từ trong database kết nối; chỉ 
        """
        return prompt

    def get_sql_query(self, input_question):
        try:
            # Generate the prompt using the chain of thought method
            prompt_cot = self.chain_of_thought_prompt(input_question)
            # Create a chain to generate the SQL query
            sql_query_chain = create_sql_query_chain(self.llm, self.sql_database)
            # Invoke the chain and get the SQL query
            sql_query = sql_query_chain.invoke({"question": prompt_cot})
            # Make sure there are no extraneous characters in the query
            pattern = r"```sql\s*(.*?)\s*```"
            match = re.search(pattern, sql_query, re.DOTALL)
            return match.group(1).strip() if match else None
        except Exception as e:
            print(f"Error generating SQL query: {e}")
            return None

    def get_result(self, question):
        # Create a system role template for generating a complete answer
        # system_role = """
        # Given the following user question, corresponding SQL query, and SQL result, answer the user question.
        # Question: {question}
        # SQL Query: {query}
        # SQL Result: {result}
        # Answer:
        # """
        try:
            # First, generate the SQL query from the question
            sql_query = self.get_sql_query(question)
            if not sql_query:
                raise ValueError("SQL query generation failed.")
            
            # Execute the SQL query and retrieve the result
            query_tool = QuerySQLDataBaseTool(db=self.sql_database)
            sql_result = query_tool.run(sql_query)

            # # Format the prompt to generate the final answer
            # answer_prompt = PromptTemplate.from_template(system_role)
            # answer_chain = answer_prompt | self.llm | StrOutputParser()

            # # Prepare the answer input with actual values
            # answer_input = {
            #     "question": question,
            #     "query": sql_query,
            #     "result": sql_result
            # }

            # # Generate the final answer
            # final_answer = answer_chain.invoke(answer_input)
            return sql_result

        except Exception as e:
            print(f"Error executing SQL query or generating result: {e}")
            return None