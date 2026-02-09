To run the project, start the Azure Functions host locally using VS Code or func start, which launches the API on localhost:7071.
Send a request to the TextAnalyzer endpoint with a text query parameter to analyze and store data in Cosmos DB.
Use the GetAnalysisHistory endpoint to retrieve previously stored analysis results as JSON.