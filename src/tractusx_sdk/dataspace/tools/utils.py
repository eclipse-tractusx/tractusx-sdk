import argparse

def get_arguments():
    
    parser = argparse.ArgumentParser()

    parser.add_argument('--test-mode', action='store_true', help="Run in test mode (skips uvicorn.run())", required=False)
    
    parser.add_argument("--debug", default=False, action="store_false", help="Enable and disable the debug", required=False)
    
    parser.add_argument("--port", default=9000, help="The server port where it will be available", type=int, required=False,)
    
    parser.add_argument("--host", default="localhost", help="The server host where it will be available", type=str, required=False)
    
    args = parser.parse_args()
    return args