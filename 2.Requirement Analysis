# Phase 2: Requirement Analysis

This folder documents the requirements, technical choices, customer journeys, and data flow architectures for the platform.

---

## 1. Technology Stack Selection
The platform is built using a modern, scalable, and responsive architecture:

*   **Frontend**: 
    *   **React.js (Vite)**: Quick build tool and robust Single Page Application (SPA) structure.
    *   **Vanilla CSS**: Premium dark-mode Token system using HSL configurations, custom animations, and glassmorphic card patterns.
    *   **Lucide-React**: Premium, unified vector iconography.
*   **Backend**:
    *   **FastAPI (Python)**: High-performance, async-enabled REST API with auto-generated Swagger documentation.
    *   **Uvicorn**: Lightweight ASGI web server.
*   **Database & ORM**:
    *   **SQLite**: Lightweight, serverless relational database for local development and testing.
    *   **SQLAlchemy ORM**: Handles SQL queries via Python models. Easily maps to cloud Postgres (Neon/Supabase) in production.
*   **Generative AI Layer**:
    *   **Google Gemini API (`gemini-1.5-flash`)**: Used for generating intelligent, professional, lender-specific hardship negotiation letters.

---

## 2. Customer Journey Map
This journey traces how John Doe uses the platform to resolve a credit card delinquency:

```
[Discovery] ➔ [Registration] ➔ [Debt Input] ➔ [Analysis] ➔ [AI Drafting] ➔ [Resolution]
```

1.  **Discovery**: John is stressed by collection letters and searches for an automated debt settlement tool. He finds BlogForge.
2.  **Registration**: John signs up, inputting his monthly gross income and basic expenses.
3.  **Debt Input**: He inputs his delinquent Chase Credit Card details: balance ($10,000), monthly EMI ($350), and overdue months (6 months).
4.  **Analysis (Settlement Predictor)**: John views his dashboard. The visual meter shows a "Severe" stress rating due to a high DTI. He runs the predictor, which suggests offering a 35% settlement ($3,500 payoff) based on the 6-month delinquency.
5.  **AI Drafting**: John selects the Chase Card, selects "Job Loss" as his hardship, adds salary details, and clicks "Generate". Google Gemini AI drafts a formal proposal.
6.  **Resolution**: John copies the letter, mails it to Chase's settlement department, and begins paying off the settled amount in structured installments.

---

## 3. Data Flow Diagram (DFD)

### Level 0 DFD: Context Diagram
```
                     +---------------------------+
                     |                           |
                     |                           | <--- [User Credentials / Debt Inputs]
                     |                           |
                     |                           | ---> [Ratios, Predictions, AI Letters]
                     |                           |
                     |         BLOGFORGE         |
    [Borrower User]  |       DEBT RELIEF         |
                     |         PLATFORM          |
                     |                           | <--- [Live Hardship / Prompt Data]
                     |                           |
                     |                           | ---> [Structured AI JSON Outputs]
                     |                           |
                     +---------------------------+
                                   ^
                                   | (Database Queries)
                                   v
                         +-------------------+
                         |  SQLite / Postgres|
                         |     Database      |
                         +-------------------+
```

### Level 1 DFD: Functional Decomposition
1.  **Process 1.0 (Auth & Session)**: Verifies user registration and login credentials, encoding active states inside JWT security tokens.
2.  **Process 2.0 (Financial Profile Engine)**: Takes user income, expenses, and total loan EMIs to calculate surplus and update the DTI and EMI ratios.
3.  **Process 3.0 (Settlement Predictor)**: Evaluates loan type and overdue months against user stress levels to output suggested settlement percentages.
4.  **Process 4.0 (AI Letter Compiler)**: Sends the user profile, loan status, and hardship details to the Gemini API, returning the strategy and letter.
5.  **Process 5.0 (Data Persistence)**: Writes user inputs, predictions, and negotiation history to the SQLite database.
