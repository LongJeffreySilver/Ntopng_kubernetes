

import subprocess


ps_process = subprocess.Popen(["ps", "aux"],stdout=subprocess.PIPE)
grep_process = subprocess.run(["grep", "/usr/bin/ntopng"],stdin=ps_process.stdout, capture_output=True,text=True)
aux = grep_process.stdout.splitlines()[0]
line = aux.split()
user_process = line[0]

if user_process == "ntopng":
    print("a")
else:
    #Iniciar el servidor de normal
    print("b")
