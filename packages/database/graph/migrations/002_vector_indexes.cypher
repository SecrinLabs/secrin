CREATE VECTOR INDEX function_embedding_index IF NOT EXISTS
FOR (f:Function)
ON f.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1024,
  `vector.similarity_function`: 'cosine'
  }};
  
  CREATE VECTOR INDEX class_embedding_index IF NOT EXISTS
  FOR (c:Class)
  ON c.embedding
  OPTIONS {indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
    }};
    
    CREATE VECTOR INDEX file_embedding_index IF NOT EXISTS
    FOR (f:File)
    ON f.embedding
    OPTIONS {indexConfig: {
      `vector.dimensions`: 1024,
      `vector.similarity_function`: 'cosine'
      }};
      
      CREATE VECTOR INDEX doc_embedding_index IF NOT EXISTS
      FOR (d:Doc)
      ON d.embedding
      OPTIONS {indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
        }};
        
        CREATE VECTOR INDEX module_embedding_index IF NOT EXISTS
        FOR (m:Module)
        ON m.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
          }};
          
          CREATE VECTOR INDEX commit_embedding_index IF NOT EXISTS
          FOR (c:Commit)
          ON c.embedding
          OPTIONS {indexConfig: {
            `vector.dimensions`: 1024,
            `vector.similarity_function`: 'cosine'
            }};
