FROM python:3.11.8
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 6789
CMD ["streamlit", "run", "Home.py", "--server.port=6789", "--server.enableCORS=false"]


