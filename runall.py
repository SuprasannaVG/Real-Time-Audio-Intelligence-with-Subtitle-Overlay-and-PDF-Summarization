import subprocess

# Start each Flask app in a new terminal
subprocess.Popen(["python", "app.py"])
subprocess.Popen(["python", "reco.py"])
subprocess.Popen(["python", "onlyA.py"])
