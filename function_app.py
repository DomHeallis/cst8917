# =============================================================================
# IMPORTS - Libraries we need for our function
# =============================================================================
import azure.functions as func  # Azure Functions SDK - required for all Azure Functions
import logging                  # Built-in Python library for printing log messages
import json                     # Built-in Python library for working with JSON data
import re                       # Built-in Python library for Regular Expressions (pattern matching)
import os
import uuid
from datetime import datetime   # Built-in Python library for working with dates and times

from azure.cosmos import CosmosClient


# =============================================================================
# COSMOS DB CONFIG (from environment variables)
# =============================================================================
COSMOS_CONN_STR = os.getenv("DATABASE_CONNECTION_STRING")
COSMOS_DB_NAME = os.getenv("COSMOS_DATABASE_NAME")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME")


# =============================================================================
# CREATE THE FUNCTION APP
# =============================================================================
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# =============================================================================
# DEFINE THE TEXT ANALYZER FUNCTION
# =============================================================================
@app.route(route="TextAnalyzer")
def TextAnalyzer(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Text Analyzer API was called!")

    # =========================================================================
    # STEP 1: GET THE TEXT INPUT
    # =========================================================================
    text = req.params.get("text")

    if not text:
        try:
            req_body = req.get_json()
            text = req_body.get("text")
        except ValueError:
            pass

    # =========================================================================
    # STEP 2: ANALYZE THE TEXT
    # =========================================================================
    if text:
        words = text.split()
        word_count = len(words)

        char_count = len(text)
        char_count_no_spaces = len(text.replace(" ", ""))

        sentence_count = len(re.findall(r"[.!?]+", text)) or 1
        paragraph_count = len([p for p in text.split("\n\n") if p.strip()])

        reading_time_minutes = round(word_count / 200, 1)
        avg_word_length = round(char_count_no_spaces / word_count, 1) if word_count > 0 else 0
        longest_word = max(words, key=len) if words else ""

        response_data = {
            "analysis": {
                "wordCount": word_count,
                "characterCount": char_count,
                "characterCountNoSpaces": char_count_no_spaces,
                "sentenceCount": sentence_count,
                "paragraphCount": paragraph_count,
                "averageWordLength": avg_word_length,
                "longestWord": longest_word,
                "readingTimeMinutes": reading_time_minutes
            },
            "metadata": {
                "analyzedAt": datetime.utcnow().isoformat(),
                "textPreview": text[:100] + "..." if len(text) > 100 else text
            }
        }

        # =========================================================================
        # STEP 3: STORE RESULT IN COSMOS DB
        # =========================================================================
        if not COSMOS_CONN_STR or not COSMOS_DB_NAME or not COSMOS_CONTAINER_NAME:
            return func.HttpResponse(
                json.dumps({"error": "Cosmos DB settings missing. Check local.settings.json"}, indent=2),
                mimetype="application/json",
                status_code=500
            )

        client = CosmosClient.from_connection_string(COSMOS_CONN_STR)
        database = client.get_database_client(COSMOS_DB_NAME)
        container = database.get_container_client(COSMOS_CONTAINER_NAME)

        record_id = str(uuid.uuid4())

        document = {
            "id": record_id,
            "analysis": response_data["analysis"],
            "metadata": response_data["metadata"],
            "originalText": text
        }

        container.create_item(body=document)

        # =========================================================================
        # STEP 4: RETURN RESULT + ID
        # =========================================================================
        response_data["id"] = record_id

        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            mimetype="application/json",
            status_code=200
        )

    # =========================================================================
    # STEP 5: HANDLE MISSING TEXT (Error Response)
    # =========================================================================
    instructions = {
        "error": "No text provided",
        "howToUse": {
            "option1": "Add ?text=YourText to the URL",
            "option2": "Send a POST request with JSON body: {\"text\": \"Your text here\"}",
            "example": "https://your-function-url/api/TextAnalyzer?text=Hello world"
        }
    }

    return func.HttpResponse(
        json.dumps(instructions, indent=2),
        mimetype="application/json",
        status_code=400
    )

# =============================================================================
# GET ANALYSIS HISTORY FUNCTION
# =============================================================================
@app.route(route="GetAnalysisHistory", methods=["GET"])
def GetAnalysisHistory(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("GetAnalysisHistory API was called!")

    # Get optional ?limit query parameter (default = 10)
    limit_param = req.params.get("limit", "10")

    try:
        limit = int(limit_param)
    except ValueError:
        limit = 10

    # Safety cap (optional but good practice)
    limit = min(limit, 50)

    # Validate Cosmos DB settings
    if not COSMOS_CONN_STR or not COSMOS_DB_NAME or not COSMOS_CONTAINER_NAME:
        return func.HttpResponse(
            json.dumps({"error": "Cosmos DB settings missing"}, indent=2),
            mimetype="application/json",
            status_code=500
        )

    # Connect to Cosmos DB
    client = CosmosClient.from_connection_string(COSMOS_CONN_STR)
    database = client.get_database_client(COSMOS_DB_NAME)
    container = database.get_container_client(COSMOS_CONTAINER_NAME)

    # Query most recent results (ordered by timestamp)
    query = """
        SELECT c.id, c.analysis, c.metadata
        FROM c
        ORDER BY c.metadata.analyzedAt DESC
    """

    items = list(
        container.query_items(
            query=query,
            enable_cross_partition_query=True
        )
    )

    results = items[:limit]

    response_data = {
        "count": len(results),
        "results": results
    }

    return func.HttpResponse(
        json.dumps(response_data, indent=2),
        mimetype="application/json",
        status_code=200
    )

