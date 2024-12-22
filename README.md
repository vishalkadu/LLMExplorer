# LLMExplorer  

LLMExplorer is a simple app to interact with **Ollama language models**. It allows you to select a model, adjust parameters, and chat with the model in real time.  

---

## Installation  
### Step 0: Install Ollama  

Download and install Ollama from the official website:  
[https://ollama.com/download](https://ollama.com/download)  

After installation, download the model of your choice by running below command:  
```bash
ollama pull <model-name>
```

For example, to download the **llama3.2:latest** model, use command:  
```bash
ollama pull llama3.2:latest
```  

### Step 1: Clone the Repository  

Run the following commands:  
```bash
git clone https://github.com/vishalkadu/LLMExplorer.git
cd LLMExplorer
```  

### Step 2: Install Dependencies  

Ensure you have **Python 3.8+** installed. Then, install the required libraries:  
```bash
pip install -r packages.txt
```  

### Step 3: Run the App  

Start the app by running the **ServiceManager**:  
```bash
streamlit run service_manager.py
```  
it helps you start and manage the following services:  
- **Redis**  
- **Ollama**  
- **Streamlit**  

With just one click, you can ensure that all the necessary services are running for application.  

---

## Usage  

Once the app is running:  

1. **Click "Start All Services"** to start Redis, Ollama, and the Streamlit app.  
2. The app will automatically check if Redis and Ollama are running, and if they are not, it will start them.  
3. The Streamlit app will also be started automatically.  

---

### Services Managed  

- **Redis**: Ensures Redis is running; if not, it will start it.
- **Ollama**: Checks and starts Ollama if it isn't already active.  
- **Streamlit**: Launches the main Streamlit app.  

---

## License  

This project is licensed under the **MIT License**.  

---

### Happy Coding! 🚀  
