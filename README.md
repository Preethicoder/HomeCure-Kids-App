# HomeCure-Kids-App for Kids' Illnesses

## Description
The **Kitchen Remedy App** is designed to help parents and caregivers find home remedies for common kids' illnesses using readily available kitchen ingredients. The app takes user inputs such as symptoms and available ingredients, then suggests soothing and easy-to-prepare remedies or recipes.

## Features
- **Symptom-Based Search**: Users can enter symptoms (e.g., sore throat, cough, upset stomach) to receive remedy suggestions.
- **Ingredient Matching**: The app suggests remedies based on the ingredients available at home.
- **Customizable Recipes**: Users can adjust remedies based on ingredient availability.
- **Interactive Guidance**: Step-by-step preparation instructions for each remedy.
- **Educational Tips**: Provides additional information on natural healing properties of ingredients.

## Technology Stack
- **Front-End**: React
- **Back-End**: FastAPI
- **Database**: PostgreSQL
- **AI Integration**:
  - Transformer-based models (GPT or T5) for remedy generation.
  - Dense Retriever or ElasticSearch for finding relevant remedies.
  - Vector databases (Pinecone or Weaviate) for efficient retrieval.
  - AI APIs: Hugging Face or OpenAI for retrieval-augmented generation (RAG).

## Getting Started
### Prerequisites
- Python (for FastAPI backend)
- Node.js (for React frontend)
- PostgreSQL (database setup)

### Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Preethicoder/HomeCure-Kids-App.git
   cd HomeCure-Kids-App
   ```
2. **Set up the backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. **Set up the frontend**:
   ```bash
   cd ../frontend
   npm install
   npm start
   ```

## Usage
1. Enter symptoms and available ingredients.
2. Get recommended home remedies.
3. Follow the step-by-step instructions to prepare the remedy.

## Contribution
Feel free to contribute! Submit pull requests or report issues to improve the app.

## Contact
For any inquiries, reach out at [preethisivakumar2024@gmail.com]
