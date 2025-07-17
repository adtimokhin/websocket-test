## 🐍 Step 1: Set Up with venv

A **virtual environment** keeps your project's dependencies isolated from other Python projects on your computer.

### 💡 Create and activate the environment:

```bash
# Create venv folder
python3 -m venv venv

# Activate it
source venv/bin/activate
```

```bash
# Create venv folder
python -m venv venv

# Activate it
venv\Scripts\activate
```

> ✅ When activated, your terminal prompt will show `(venv)`.

### Installation of dependencies

1. Install the required dependency:
```bash
pip install -r requirements.txt
```
Make sure to install the correct requirements file. It might help to move the client into a separate folder completely.


## 🚀 Step 2: Run the FastAPI App

`main.py` has the main entrypoint to the application

```bash
python app/main.py 
```

## 📚 Step 3: View the API Documentation

FastAPI automatically provides interactive documentation!
After running the app (either locally or with Docker), open your browser and go to:

### Swagger UI:

**Local development:**

```
http://127.0.0.1:8000/docs
```