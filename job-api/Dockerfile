FROM python:3.10 

# Build arg input from deployment
ARG github_token 
ARG branch_name
ARG repo_string

# Expose for pip install which requires authorized pulls
ENV GITHUB_TOKEN=$github_token
ENV BRANCH_NAME=$branch_name
ENV REPO_STRING=$repo_string

WORKDIR /api

COPY ./docker-requirements.txt .

RUN pip install --no-cache-dir --upgrade -r docker-requirements.txt 

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]