import os
 
import dotenv
 
dotenv.load_dotenv() 
 
SQL_SERVER = os.getenv()
SQL_DATABASE = os.getenv()
SQL_UID = os.getenv()
SQL_PWD = os.getenv()



INSTRUCTIONS_IN_GERMAN=os.getenv("INSTRUCTIONS_IN_GERMAN", "Verwenden Sie genau das folgende Format und fügen Sie keine zusätzlichen Informationen hinzu:      Antwort: [answer]     Seitenzahl: [pageNumber]     Dateiname: [filename]")
INSTRUCTIONS_IN_ENGLISH=os.getenv("INSTRUCTIONS_IN_ENGLISH", "Use exactly the following format and do not add any additional information: Answer: [answer] Page number: [pageNumber] File name: [filename]")



CLIENT_ID = ""
CLIENT_SECRET = ""

STATE = "...my super secure state..."
