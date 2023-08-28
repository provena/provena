# Includes lambda runtime 
FROM python:3.10

# Build arg input from deployment
ARG github_token 
ARG branch_name
ARG repo_string

# Expose for pip install which requires authorized pulls
ENV GITHUB_TOKEN=$github_token
ENV BRANCH_NAME=$branch_name
ENV REPO_STRING=$repo_string

WORKDIR /app

COPY . .

RUN python -m ensurepip

# add cache buster layer which can be injected with hash of extra dirs or other changed things
ARG CACHE_BUSTER 
RUN echo "$CACHE_BUSTER"

# Install requirements
RUN pip install --no-cache-dir --upgrade -r docker_requirements.txt

# Python job runner entry point
CMD ["python", "launch_job_runner.py"]
