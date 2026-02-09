# Your Choice: Which database did you select?
Azure Cosmos DB 
# Justification: Why is this the best choice for this use case? (3-5 sentences)
Azure Cosmos DB is the best choice for this project because it works naturally with JSON data, which matches the format of the analysis results produced by the Azure Function. The serverless tier is cost-effective and well suited since it only charges based on usage and works well with low or unpredictable traffic. Cosmos DB also requires very little setup, does not require a fixed schema, and integrates easily with Azure Functions using the Python SDK.

# Alternatives Considered: What other options did you evaluate and why did you reject them?
Azure Table Storage was considered, but it was not chosen because it has limited query capabilities and does not handle JSON data as well as Cosmos DB. Azure SQL Database was also considered, but it requires predefined schemas and adds unnecessary complexity for a project that primarily works with JSON documents. Azure Blob Storage was rejected because it is mainly designed for file storage and does not support structured queries like a database
# Cost Considerations: How does pricing work for your chosen database?
Cosmos DB’s serverless pricing model only charges for the request units that are actually used so its good for us.