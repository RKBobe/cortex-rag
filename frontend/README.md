# Cortex-RAG Frontend

This directory contains the user interface for the **Cortex-RAG** system. It is a modern, responsive single-page application (SPA) built with **React** and **TypeScript**, designed to provide a seamless chat experience powered by the Cortex engine.

---

## 🎨 UI/UX Design
The interface is built with a focus on clarity and technical utility:
* **Real-time Chat:** Interactive terminal-style or modern chat interface for RAG interaction.
* **Document Management:** Integrated tools for uploading and tracking indexed files.
* **State Management:** Robust handling of chat history and context status using React hooks.
* **TypeScript:** Strictly typed components and API interfaces for reliable development.

---

## 🏗 Frontend Architecture

[attachment_0](attachment)

The application is structured into modular components:
* **Providers/Context:** Manages global state such as API authentication and active chat sessions.
* **Components:** Reusable UI elements (Message bubbles, Upload modals, Sidebar).
* **Services/Hooks:** Custom logic for communicating with the Flask backend via Axios or Fetch.

---

## 📁 Directory Structure
```text
frontend/
├── public/             # Static assets
├── src/
│   ├── components/     # UI Building blocks (ChatWindow, Sidebar, FileUpload)
│   ├── hooks/          # Custom hooks for API interaction (useChat, useUpload)
│   ├── services/       # API client configuration
│   ├── types/          # TypeScript interfaces and types
│   └── App.tsx         # Main application entry and routing
├── package.json        # Dependencies and scripts
└── tsconfig.json       # TypeScript configuration
