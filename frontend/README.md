# Cortex-RAG

**Cortex-RAG** is a sophisticated Retrieval-Augmented Generation (RAG) agent designed for context-aware chat. Developed by **Treelight Innovations**, it leverages a modern web stack and advanced vector retrieval to allow users to interact with their data in a natural, conversational manner.

---

## 🚀 Overview
The "Cortex" engine acts as a bridge between raw data and Large Language Models (LLMs). It processes documents, stores them in a vector database, and retrieves the most relevant information to augment the generation process, ensuring responses are grounded in specific, provided contexts.

### Key Features
* **Context-Aware Chat:** Intelligent responses based on retrieved document fragments.
* **Modern UI/UX:** A clean, responsive interface built with React and TypeScript.
* **Robust Backend:** A high-performance Flask API handling orchestration and retrieval logic.
* **Efficient Vector Search:** Optimized for fast similarity searches to provide near-instantaneous context injection.

---

## 🛠 Tech Stack
* **Frontend:** React, TypeScript
* **Backend:** Flask (Python)
* **Storage:** Vector Database (RAG)
* **Environment:** Node.js, Python 3.9+

---

## 📁 Project Structure
```text
cortex-rag/
├── backend/            # Flask API & RAG Logic (See /backend/README.md)
├── frontend/           # React + TypeScript App
├── data/               # Local vector storage and document cache
└── docs/               # Technical documentation

git clone [https://github.com/your-username/cortex-rag.git](https://github.com/your-username/cortex-rag.git)
cd cortex-rag

## Setup backend:
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

##Setup frontend
cd ../frontend
npm install
npm start


 Contributing
Contributions are welcome! Please feel free to submit a Pull Request or open an issue for any bugs or feature requests.
📄 License
This project is licensed under the MIT License.
Developed by Treelight Innovations
