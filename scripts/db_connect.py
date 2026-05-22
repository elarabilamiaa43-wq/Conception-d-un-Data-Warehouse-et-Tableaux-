import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Kat-qra l-fichier .env automatic
load_dotenv()

def get_connection():
    
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    database = os.getenv("database")
    
    
    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    
   
    engine = create_engine(db_url)
    return engine