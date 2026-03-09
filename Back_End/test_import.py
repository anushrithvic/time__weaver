import traceback
try:
    from app.main import app
    print("Successfully imported app")
except Exception as e:
    print("FAILED TO IMPORT APP:")
    traceback.print_exc()
