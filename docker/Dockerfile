ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}-slim-buster
# DO NOT SPECIFY PATH AS ARG; it will change PATH directory in linux docker
ARG FOLDERPATH=put/absolute/path/here
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
COPY . ${FOLDERPATH} 
WORKDIR ${FOLDERPATH} 
RUN apt update && \
    apt install -y gcc default-libmysqlclient-dev && \
    pip install --no-cache-dir -r requirements.txt
EXPOSE 4280
CMD ["python3", "-m", "flask", "run"]