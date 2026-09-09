# mini-rag

This is a minimal implementation of the RAG model for question answering

## Requirements

- Python 3.14.6

#### Install Python

1) Download and install Python [here](https://www.python.org/)
```bash
$ sudo apt install python3
```

2) Create new virual envirnoment using virtualenv and activate it
```bash
$ virualenv mini-rag
$ cd mini-rag
$ source ./bin/activate
```

### (Optional) Setup you command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## Installation

### Install the required packages

```bash
$ pip install -r requirements.txt
```

### Setup the environment variables

```bash
$ cp .env.example .env
```

Set your envirnoment variables in the `.env` file. Like `OPENAI_API_KEY` value.


## Run the FastAPI server
```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

## POSTMAN Collection

Download the POSTMAN collection from [/assets/mini-rag.postman_collection.json](/assets/mini-rag.postman_collection.json)



## Run Docker Compose Services

```bash
$ cd docker
$ cp .env.example .env
```

- update `.env` with your credentials.

