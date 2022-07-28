ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}-slim-buster
# DO NOT SPECIFY PATH AS ARG; it will change PATH directory in linux docker
ARG FOLDERPATH=C:/Users/daronphang/coding_projects/pee_df_adhoc_requests/src
ENV FLASK_APP src/enter_app_name/flask_app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=4280
COPY . ${FOLDERPATH} 
WORKDIR ${FOLDERPATH} 
# RUN apt update && \
#     apt install -y gcc default-libmysqlclient-dev && \
#     pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir  --trusted-host pypi.org --trusted-host files.pythonhosted.org --proxy proxy-web.micron.com:80 -r requirements.txt
EXPOSE 4280
CMD ["python3", "-m", "flask", "run"]